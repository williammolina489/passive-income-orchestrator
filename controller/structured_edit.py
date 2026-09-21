from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from openai import OpenAI

from controller.codex_job import ROOT, validate_job


DEFAULT_MODEL = "gpt-5.6-luna"
MAX_INPUT_CHARS = 120_000


def _exact_allowed_files(job: dict[str, Any], target_repo: Path) -> list[str]:
    files: list[str] = []
    for raw in job["allowed_paths"]:
        rel = raw.rstrip("/")
        path = target_repo / rel
        if not path.is_file():
            raise ValueError(
                "structured fallback requires allowed_paths to name exact existing files; "
                f"{raw!r} is not an existing file"
            )
        files.append(rel)
    return files


def _response_schema(allowed_files: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["summary", "files", "no_change_reason"],
        "properties": {
            "summary": {"type": "string", "minLength": 1, "maxLength": 2000},
            "files": {
                "type": "array",
                "maxItems": len(allowed_files),
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "content"],
                    "properties": {
                        "path": {"type": "string", "enum": allowed_files},
                        "content": {"type": "string"},
                    },
                },
            },
            "no_change_reason": {
                "anyOf": [
                    {"type": "string", "minLength": 1, "maxLength": 2000},
                    {"type": "null"},
                ]
            },
        },
    }


def _prompt(
    job: dict[str, Any],
    project: dict[str, Any],
    state: dict[str, Any],
    files: dict[str, str],
) -> str:
    return f"""You are a bounded code editor acting as a fallback for a timed-out Codex CLI run.

Repository: {project['repo']}
Authorized starting SHA: {job['expected_head_sha']}
Canonical branch: {state['branch']}

AUTHORIZATION BASIS
{job['authorization_basis']}

OBJECTIVE
{job['objective']}

CONSTRAINTS
{json.dumps(job['constraints'], indent=2)}

FORBIDDEN ACTIONS
{json.dumps(job['forbidden_actions'], indent=2)}

COMPLETION CRITERIA
{json.dumps(job['completion_criteria'], indent=2)}

ALLOWED FILES
{json.dumps(list(files), indent=2)}

CURRENT FILE CONTENTS
{json.dumps(files, indent=2)}

Return complete replacement contents only for files that actually need changes.
Do not invent additional paths. Do not modify production behavior, methodology, research state,
credentials, workflows, or any file outside ALLOWED FILES. Do not run tools. Do not claim tests
passed; the outer workflow runs the authoritative tests. If equivalent coverage already exists,
return an empty files array and explain why in no_change_reason.
"""


def apply_structured_edit(
    root: Path,
    job_path: Path,
    target_repo: Path,
    *,
    client: OpenAI | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    job, project, state = validate_job(root, job_path, require_enabled=True)
    allowed_files = _exact_allowed_files(job, target_repo)
    contents = {
        rel: (target_repo / rel).read_text(encoding="utf-8")
        for rel in allowed_files
    }
    total_chars = sum(len(value) for value in contents.values())
    if total_chars > MAX_INPUT_CHARS:
        raise ValueError(
            f"structured fallback input is too large: {total_chars} chars > {MAX_INPUT_CHARS}"
        )

    schema = _response_schema(allowed_files)
    api = client or OpenAI()
    response = api.responses.create(
        model=model,
        reasoning={"effort": "low"},
        store=False,
        max_output_tokens=20_000,
        input=[
            {
                "role": "developer",
                "content": (
                    "Return only the requested structured edit. "
                    "Never broaden scope beyond the explicitly allowed files."
                ),
            },
            {"role": "user", "content": _prompt(job, project, state, contents)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "bounded_code_edit",
                "strict": True,
                "schema": schema,
            }
        },
    )
    if getattr(response, "status", None) not in (None, "completed"):
        raise RuntimeError(f"OpenAI edit response did not complete: {response.status}")
    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise RuntimeError("OpenAI edit response contained no output_text")

    payload = json.loads(output_text)
    Draft202012Validator(schema).validate(payload)

    seen: set[str] = set()
    changed: list[str] = []
    for item in payload["files"]:
        path = item["path"]
        if path in seen:
            raise ValueError(f"duplicate edited path returned: {path}")
        seen.add(path)
        destination = target_repo / path
        before = contents[path]
        after = item["content"]
        if after != before:
            destination.write_text(after, encoding="utf-8")
            changed.append(path)

    if not changed and not payload.get("no_change_reason"):
        raise ValueError("fallback returned no changes without a no_change_reason")

    usage = getattr(response, "usage", None)
    return {
        "schema_version": "1.0",
        "model": model,
        "summary": payload["summary"],
        "changed_paths": changed,
        "no_change_reason": payload.get("no_change_reason"),
        "usage": {
            "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
            "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply a bounded structured code edit when Codex CLI times out."
    )
    parser.add_argument("job_file", type=Path)
    parser.add_argument("target_repo", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--model",
        default=os.environ.get("ORCHESTRATOR_CODE_MODEL", DEFAULT_MODEL),
    )
    args = parser.parse_args(argv)

    report = apply_structured_edit(
        args.root.resolve(),
        args.job_file.resolve(),
        args.target_repo.resolve(),
        model=args.model,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
