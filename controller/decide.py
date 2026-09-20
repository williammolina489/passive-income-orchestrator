from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from openai import OpenAI

from controller.status import ROOT, build_report


DEFAULT_MODEL = "gpt-5.6-luna"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_candidates(report: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for project in report["projects"]:
        if not project.get("dispatch_eligible"):
            continue
        actions = project.get("next_permitted_actions") or []
        for index, action in enumerate(actions):
            candidates.append(
                {
                    "candidate_id": f"{project['project_id']}::{index}",
                    "project_id": project["project_id"],
                    "repository": project["repository"],
                    "branch": project.get("branch"),
                    "head_sha": project.get("recorded_head_sha"),
                    "lifecycle_status": project.get("lifecycle_status"),
                    "experiment": project.get("experiment"),
                    "action": action,
                    "forbidden_actions": project.get("forbidden_actions", []),
                    "worker": project.get("worker"),
                }
            )
    return candidates


def build_dynamic_schema(
    base_schema: dict[str, Any], candidates: list[dict[str, Any]]
) -> dict[str, Any]:
    schema = copy.deepcopy(base_schema)
    allowed = ["NONE"] + [candidate["candidate_id"] for candidate in candidates]
    schema["properties"]["candidate_id"]["enum"] = allowed
    return schema


def validate_decision(
    decision: dict[str, Any],
    schema: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    Draft202012Validator(schema).validate(decision)
    by_id = {candidate["candidate_id"]: candidate for candidate in candidates}

    candidate_id = decision["candidate_id"]
    kind = decision["decision"]

    if kind == "RUN_TASK":
        if candidate_id == "NONE" or candidate_id not in by_id:
            raise ValueError("RUN_TASK must select exactly one verified candidate")
        return by_id[candidate_id]

    if candidate_id != "NONE":
        raise ValueError(f"{kind} must use candidate_id=NONE")

    return None


def build_prompt(
    root: Path,
    report: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> str:
    global_policy = (root / "policies" / "global-policy.md").read_text(
        encoding="utf-8"
    )
    terminal_projects = [
        {
            "project_id": project["project_id"],
            "enabled": project["enabled"],
            "worker_ready": project.get("worker_ready"),
            "lifecycle_status": project.get("lifecycle_status"),
            "decision_hint": project.get("decision_hint"),
        }
        for project in report["projects"]
        if not project.get("dispatch_eligible")
    ]

    payload = {
        "verified_candidates": candidates,
        "non_dispatchable_projects": terminal_projects,
    }

    return f"""You are the scheduling controller for a fail-closed research orchestrator.

Your job is ONLY to choose whether one already-permitted candidate should run next.
You are not being asked to invent research, modify methodology, generate a new strategy,
unseal data, spend money, trade, or broaden scope.

Rules:
- Treat the supplied verified candidates as the complete action menu.
- If you choose RUN_TASK, select exactly one candidate_id from that menu.
- Never invent, rewrite, combine, or expand an action.
- Closed, disabled, stale, human-gated, or worker-not-ready projects are not candidates.
- Prefer a concrete action that can remove a current blocker over idle waiting when it is
  clearly permitted.
- If the candidate set is empty, do not choose RUN_TASK.
- If the information is materially ambiguous or would require a human-gated action,
  choose NEEDS_HUMAN.
- The result is scheduling only; execution is handled by a separately constrained worker.
- Base the decision only on the supplied repository-derived state and policy.

Global policy:
--- begin policy ---
{global_policy}
--- end policy ---

Verified portfolio input:
{json.dumps(payload, indent=2, sort_keys=True)}
"""


def call_controller(
    *,
    root: Path = ROOT,
    model: str = DEFAULT_MODEL,
    client: OpenAI | None = None,
) -> dict[str, Any]:
    token = os.environ.get("ORCHESTRATOR_GITHUB_TOKEN") or os.environ.get(
        "GITHUB_TOKEN"
    )
    if not token:
        raise RuntimeError("ORCHESTRATOR_GITHUB_TOKEN is required")

    report = build_report(root, verify_remote=True, token=token)
    if not report["ok"]:
        raise RuntimeError("portfolio verification failed; refusing model scheduling call")

    candidates = build_candidates(report)

    if not candidates:
        return {
            "mode": "DETERMINISTIC_NO_CANDIDATE",
            "model": None,
            "decision": {
                "schema_version": "1.0",
                "decision": "WAIT",
                "candidate_id": "NONE",
                "rationale": "No verified worker-ready autonomous task is currently eligible.",
            },
            "selected_candidate": None,
            "candidate_count": 0,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            },
        }

    if len(candidates) == 1:
        selected = candidates[0]
        return {
            "mode": "DETERMINISTIC_SINGLE_CANDIDATE",
            "model": None,
            "decision": {
                "schema_version": "1.0",
                "decision": "RUN_TASK",
                "candidate_id": selected["candidate_id"],
                "rationale": (
                    "Exactly one verified, enabled, worker-ready bounded task is eligible; "
                    "no model arbitration is needed."
                ),
            },
            "selected_candidate": selected,
            "candidate_count": 1,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            },
        }

    base_schema = load_json(root / "schemas" / "controller-decision.schema.json")
    schema = build_dynamic_schema(base_schema, candidates)
    prompt = build_prompt(root, report, candidates)

    api = client or OpenAI()
    response = api.responses.create(
        model=model,
        reasoning={"effort": "low"},
        store=False,
        max_output_tokens=1200,
        input=[
            {
                "role": "developer",
                "content": (
                    "Return only the requested structured scheduling decision. "
                    "Do not execute tools or propose actions outside the supplied candidates."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "orchestrator_controller_decision",
                "strict": True,
                "schema": schema,
            }
        },
    )

    if getattr(response, "status", None) not in (None, "completed"):
        raise RuntimeError(f"OpenAI response did not complete: {response.status}")

    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise RuntimeError("OpenAI response contained no output_text")

    decision = json.loads(output_text)
    selected = validate_decision(decision, schema, candidates)

    usage = getattr(response, "usage", None)
    usage_summary = None
    if usage is not None:
        usage_summary = {
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }

    return {
        "mode": "DRY_RUN_NO_DISPATCH",
        "model": model,
        "decision": decision,
        "selected_candidate": selected,
        "candidate_count": len(candidates),
        "usage": usage_summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Make one OpenAI-powered scheduling decision without dispatching work."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("ORCHESTRATOR_MODEL", DEFAULT_MODEL),
        help=f"OpenAI model (default: {DEFAULT_MODEL}).",
    )
    args = parser.parse_args(argv)

    result = call_controller(root=args.root.resolve(), model=args.model)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
