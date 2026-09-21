from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from controller.status import ROOT


_BRANCH_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_registry(root: Path) -> dict[str, Any]:
    with (root / "projects.yaml").open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)["projects"]


def _normalize_scope(value: str) -> str:
    value = value.strip().replace("\\", "/")
    path = PurePosixPath(value)
    if not value or value in {".", "/"}:
        raise ValueError("path scope cannot be empty or repository-wide")
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe path scope: {value!r}")
    normalized = path.as_posix()
    return normalized.rstrip("/")


def _scopes_overlap(left: str, right: str) -> bool:
    left = _normalize_scope(left)
    right = _normalize_scope(right)
    return (
        left == right
        or left.startswith(right + "/")
        or right.startswith(left + "/")
    )


def _validate_path_policy(job: dict[str, Any], config: dict[str, Any]) -> None:
    allowed = [_normalize_scope(item) for item in job["allowed_paths"]]
    protected = [
        _normalize_scope(item)
        for item in (config.get("protected_paths") or [])
    ]
    for allowed_scope in allowed:
        for protected_scope in protected:
            if _scopes_overlap(allowed_scope, protected_scope):
                raise ValueError(
                    f"allowed path {allowed_scope!r} overlaps protected path "
                    f"{protected_scope!r}"
                )


def _branch_name(prefix: str, job_id: str) -> str:
    slug = _BRANCH_SAFE.sub("-", job_id).strip("-._")
    if not slug:
        raise ValueError("job_id cannot produce an empty branch name")
    return f"{prefix}{slug}"[:240]


def validate_job(
    root: Path,
    job_path: Path,
    *,
    require_enabled: bool = True,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    job = _load_json(job_path)
    schema = _load_json(root / "schemas" / "codex-job.schema.json")
    Draft202012Validator(schema).validate(job)

    registry = _load_registry(root)
    project_id = job["project_id"]
    if project_id not in registry:
        raise ValueError(f"unknown project_id: {project_id}")
    project = registry[project_id]
    code_worker = project.get("code_worker")
    if not isinstance(code_worker, dict):
        raise ValueError(f"{project_id} has no code_worker configuration")
    if require_enabled and code_worker.get("enabled") is not True:
        raise ValueError(
            f"{project_id} code_worker is disabled: "
            f"{code_worker.get('reason', 'no reason recorded')}"
        )

    state = _load_json(root / project["state_file"])
    if state["repository"] != project["repo"]:
        raise ValueError("project registry/state repository mismatch")
    if state["head_sha"] != job["expected_head_sha"]:
        raise ValueError("Codex job expected_head_sha does not match canonical state")
    if job["authorization_basis"] not in state.get("next_permitted_actions", []):
        raise ValueError(
            "Codex job authorization_basis must exactly match a canonical "
            "next_permitted_action"
        )
    if state.get("human_action_required") is True:
        raise ValueError("project is human-gated; Codex editing is not permitted")
    if state.get("lifecycle_status") in {"CLOSED", "STOPPED", "COMPLETE", "NEEDS_HUMAN"}:
        raise ValueError(
            f"project lifecycle {state.get('lifecycle_status')} is not code-worker eligible"
        )

    base_ref = str(code_worker.get("base_ref") or state["branch"])
    if base_ref != state["branch"]:
        raise ValueError("code_worker base_ref must match the canonical state branch")

    _validate_path_policy(job, code_worker)
    return job, project, state


def build_prompt(
    root: Path,
    job: dict[str, Any],
    project: dict[str, Any],
    state: dict[str, Any],
) -> str:
    policy = (root / "policies" / "global-policy.md").read_text(encoding="utf-8")
    code_worker = project["code_worker"]
    allowed = "\n".join(f"- {item}" for item in job["allowed_paths"])
    constraints = "\n".join(f"- {item}" for item in job["constraints"])
    forbidden = "\n".join(f"- {item}" for item in job["forbidden_actions"])
    completion = "\n".join(f"- {item}" for item in job["completion_criteria"])
    protected = "\n".join(
        f"- {item}" for item in code_worker.get("protected_paths", [])
    )

    return f"""You are a PR-only coding worker inside a fail-closed research system.

GitHub repository: {project['repo']}
Starting commit: {job['expected_head_sha']}
Project state branch: {state['branch']}
Job ID: {job['job_id']}

AUTHORIZATION BASIS
{job['authorization_basis']}

OBJECTIVE
{job['objective']}

ALLOWED PATHS
You may modify only these paths:
{allowed}

PROTECTED PATHS
Do not modify these paths:
{protected or '- none'}

CONSTRAINTS
{constraints}

FORBIDDEN ACTIONS
{forbidden}

COMPLETION CRITERIA
{completion}

GLOBAL POLICY
{policy}

EXECUTION BOUNDARIES
- Work only in the checked-out repository.
- Do not commit, push, create a PR, merge, or change branches. The outer workflow owns Git operations.
- Do not modify methodology, acceptance gates, protected validation/OOS evidence, or research conclusions.
- Do not enable live-money behavior or weaken paper/live safety gates.
- Do not write outside ALLOWED PATHS.
- Do not add credentials, tokens, secrets, or external service configuration.
- Network access is intentionally unavailable during your step.
- Prefer the smallest implementation that satisfies the exact objective.
- Run any already-available focused tests that help you reason, but the outer workflow will run the authoritative validation commands afterward.
"""


def prepare_job(
    root: Path,
    job_path: Path,
    output_dir: Path,
    *,
    require_enabled: bool = True,
) -> dict[str, Any]:
    job, project, state = validate_job(
        root, job_path, require_enabled=require_enabled
    )
    code_worker = project["code_worker"]
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = output_dir / "prompt.txt"
    prompt_path.write_text(
        build_prompt(root, job, project, state), encoding="utf-8"
    )

    setup_path = output_dir / "setup.sh"
    setup_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    setup_lines.extend(str(item) for item in code_worker.get("setup_commands", []))
    setup_path.write_text("\n".join(setup_lines) + "\n", encoding="utf-8")

    validation_path = output_dir / "validate.sh"
    validation_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    validation_lines.extend(
        str(item) for item in code_worker.get("validation_commands", [])
    )
    validation_path.write_text(
        "\n".join(validation_lines) + "\n", encoding="utf-8"
    )

    branch = _branch_name(
        str(code_worker.get("branch_prefix") or "orchestrator/"),
        str(job["job_id"]),
    )
    metadata = {
        "schema_version": "1.0",
        "job_id": job["job_id"],
        "project_id": job["project_id"],
        "repository": project["repo"],
        "base_ref": str(code_worker.get("base_ref") or state["branch"]),
        "expected_head_sha": job["expected_head_sha"],
        "branch_name": branch,
        "prompt_file": str(prompt_path),
        "setup_script": str(setup_path),
        "validation_script": str(validation_path),
        "allowed_paths": job["allowed_paths"],
        "protected_paths": code_worker.get("protected_paths", []),
        "authorization_basis": job["authorization_basis"],
        "objective": job["objective"],
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def _write_github_outputs(path: Path, metadata: dict[str, Any]) -> None:
    keys = [
        "job_id",
        "project_id",
        "repository",
        "base_ref",
        "expected_head_sha",
        "branch_name",
        "prompt_file",
        "setup_script",
        "validation_script",
    ]
    with path.open("a", encoding="utf-8") as handle:
        for key in keys:
            value = str(metadata[key])
            if "\n" in value or "\r" in value:
                raise ValueError(f"unsafe multiline GitHub output for {key}")
            handle.write(f"{key}={value}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and prepare a PR-only Codex job.")
    parser.add_argument("job_file", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("codex-runtime"),
    )
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)

    metadata = prepare_job(
        args.root.resolve(),
        args.job_file.resolve(),
        args.output_dir.resolve(),
    )
    if args.github_output:
        _write_github_outputs(args.github_output, metadata)
    print(json.dumps(metadata, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
