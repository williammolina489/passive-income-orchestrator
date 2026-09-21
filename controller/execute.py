from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from controller.github_actions import (
    GitHubActionsError,
    dispatch_workflow,
    fetch_run_job_logs,
    wait_for_run,
)
from controller.status import ROOT, github_branch_sha, worker_window_status


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_registry(root: Path) -> dict[str, Any]:
    with (root / "projects.yaml").open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return payload["projects"]


def _validate(schema_path: Path, payload: dict[str, Any]) -> None:
    schema = _load_json(schema_path)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)


def _now() -> datetime:
    return datetime.now(UTC)


def _task_id(project_id: str, experiment_id: str | None, now: datetime) -> str:
    exp = experiment_id or "none"
    return f"{project_id}:{exp}:{now.strftime('%Y%m%dT%H%M%SZ')}"


def _parse_live_validation(logs: list[dict[str, Any]]) -> dict[str, Any]:
    marker = "LIVE_VALIDATION_RESULT="
    matches: list[str] = []
    for job in logs:
        for line in str(job.get("logs", "")).splitlines():
            if marker in line:
                matches.append(line.split(marker, 1)[1].strip())
    if not matches:
        raise ValueError("worker logs did not contain LIVE_VALIDATION_RESULT")
    return json.loads(matches[-1])


def _crypto_stage1_result(
    *,
    task: dict[str, Any],
    run: dict[str, Any],
    logs: list[dict[str, Any]],
    final_attempt: bool = False,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    completed = _now()
    run_url = str(run.get("html_url") or run.get("url") or "")
    conclusion = run.get("conclusion")

    if conclusion != "success":
        result = {
            "schema_version": "1.0",
            "task_id": task["task_id"],
            "project_id": task["project_id"],
            "repository": task["repository"],
            "experiment_id": task["experiment_id"],
            "starting_sha": task["expected_head_sha"],
            "ending_sha": task["expected_head_sha"],
            "outcome": "ERROR",
            "summary": f"Read-only validation workflow ended with conclusion={conclusion!r}.",
            "evidence": [
                {
                    "type": "URL",
                    "reference": run_url,
                    "summary": "GitHub Actions worker run.",
                }
            ],
            "checks": [
                {
                    "name": "worker_workflow",
                    "status": "FAIL",
                    "details": f"Workflow conclusion: {conclusion}",
                }
            ],
            "methodology_changed": False,
            "protected_data_access": {"validation": False, "oos": False},
            "financial_action_taken": False,
            "human_action_required": False,
            "human_action_reason": None,
            "recommended_next_action": "Retry the same bounded read-only validation after diagnosing the workflow error.",
            "pull_request": None,
            "completed_at": completed.isoformat(),
        }
        return result, None

    payload = _parse_live_validation(logs)
    symbol_map = payload.get("logical_to_live_symbol", {})
    live_spot = symbol_map.get("BTCUSD", "BTCUSD")
    books = payload.get("websocket", {}).get("books", {})
    spot_book = books.get(live_spot, {})

    ack_id = str(spot_book.get("ack_id"))
    has_bid = spot_book.get("best_bid_ticks") is not None and spot_book.get("best_bid_price") is not None
    has_ask = spot_book.get("best_ask_ticks") is not None and spot_book.get("best_ask_price") is not None
    executable = ack_id != "0" and has_bid and has_ask

    checks = [
        {
            "name": "read_only_safety",
            "status": "PASS" if (
                payload.get("authentication_used") is False
                and payload.get("orders_or_writes_performed") is False
            ) else "FAIL",
            "details": (
                f"authentication_used={payload.get('authentication_used')}; "
                f"orders_or_writes_performed={payload.get('orders_or_writes_performed')}"
            ),
        },
        {
            "name": "btcusd_executable_book",
            "status": "PASS" if executable else "FAIL",
            "details": (
                f"live_symbol={live_spot}; ack_id={ack_id}; "
                f"bid_levels={spot_book.get('bid_levels')}; "
                f"ask_levels={spot_book.get('ask_levels')}; "
                f"best_bid_price={spot_book.get('best_bid_price')}; "
                f"best_ask_price={spot_book.get('best_ask_price')}"
            ),
        },
    ]

    if executable:
        outcome = "PASS"
        summary = (
            "Stage-1 executable-book requirement was directly observed: the frozen BTCUSD "
            "spot book had a nonzero acknowledgement plus executable bid and ask."
        )
        human_required = True
        human_reason = (
            "Stage-1 PASS evidence must be reconciled into the worker repository's durable "
            "research state before any later-stage automation is authorized."
        )
        next_action = (
            "Record the Stage-1 PASS in the worker repository and separately authorize any "
            "later-stage build; do not start the collector automatically."
        )
    else:
        outcome = "BLOCKED"
        summary = (
            "Stage 1 remains blocked because the frozen BTCUSD production book still did "
            "not satisfy the executable non-empty bid/ask requirement."
        )
        if final_attempt:
            human_required = True
            human_reason = (
                "The finite Stage-1 revalidation protocol is exhausted. This was the final "
                "authorized Checkpoint B; no further automatic retries are permitted without "
                "a new explicit decision."
            )
            next_action = (
                "Record the final Stage-1 BLOCKED classification in the worker repository "
                "and stop automatic revalidation. Do not substitute instruments or continue "
                "retrying without a new explicit decision."
            )
        else:
            human_required = False
            human_reason = None
            next_action = (
                "Repeat the same read-only BTCUSD/PBTCUC production validation without changing "
                "the frozen instrument or methodology."
            )

    result = {
        "schema_version": "1.0",
        "task_id": task["task_id"],
        "project_id": task["project_id"],
        "repository": task["repository"],
        "experiment_id": task["experiment_id"],
        "starting_sha": task["expected_head_sha"],
        "ending_sha": task["expected_head_sha"],
        "outcome": outcome,
        "summary": summary,
        "evidence": [
            {
                "type": "URL",
                "reference": run_url,
                "summary": "GitHub Actions read-only live-validation run.",
            },
            {
                "type": "LOG",
                "reference": f"{run_url}#logs",
                "summary": (
                    f"BTCUSD live book ack_id={ack_id}, "
                    f"best_bid={spot_book.get('best_bid_price')}, "
                    f"best_ask={spot_book.get('best_ask_price')}."
                ),
            },
        ],
        "checks": checks,
        "methodology_changed": False,
        "protected_data_access": {"validation": False, "oos": False},
        "financial_action_taken": False,
        "human_action_required": human_required,
        "human_action_reason": human_reason,
        "recommended_next_action": next_action,
        "pull_request": None,
        "completed_at": completed.isoformat(),
    }
    return result, payload


def _update_state_from_result(
    state: dict[str, Any],
    result: dict[str, Any],
    run_url: str,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(state))
    updated["state_revision"] = int(updated["state_revision"]) + 1
    updated["updated_at"] = _now().isoformat()
    updated["last_result_task_id"] = result["task_id"]

    sources = list(updated.get("source_documents", []))
    if run_url and run_url not in sources:
        sources.append(run_url)
    updated["source_documents"] = sources

    if result["outcome"] == "PASS":
        updated["lifecycle_status"] = "NEEDS_HUMAN"
        if isinstance(updated.get("experiment"), dict):
            updated["experiment"]["status"] = "PASS"
        updated["current_blockers"] = [
            "Stage-1 PASS evidence has not yet been reconciled into the worker repository's durable status documents."
        ]
        updated["next_permitted_actions"] = []
        updated["human_action_required"] = True
        updated["human_action_reason"] = result["human_action_reason"]
        updated["notes"] = result["summary"]
    elif result["outcome"] == "BLOCKED":
        if result.get("human_action_required"):
            updated["lifecycle_status"] = "NEEDS_HUMAN"
            if isinstance(updated.get("experiment"), dict):
                updated["experiment"]["status"] = "BLOCKED"
            updated["next_permitted_actions"] = []
            updated["human_action_required"] = True
            updated["human_action_reason"] = result.get("human_action_reason")
        else:
            updated["lifecycle_status"] = "BLOCKED"
            updated["human_action_required"] = False
            updated["human_action_reason"] = None
        updated["notes"] = result["summary"]
    elif result["outcome"] == "ERROR":
        updated["notes"] = result["summary"]

    return updated


def execute_candidate(
    controller_output: dict[str, Any],
    *,
    root: Path = ROOT,
    token: str | None = None,
) -> dict[str, Any]:
    selected = controller_output.get("selected_candidate")
    if not selected:
        raise ValueError("controller output has no selected candidate")

    token = token or os.environ.get("ORCHESTRATOR_GITHUB_TOKEN")
    if not token:
        raise RuntimeError("ORCHESTRATOR_GITHUB_TOKEN is required")

    registry = _load_registry(root)
    project_id = selected["project_id"]
    config = registry[project_id]
    worker = config.get("worker") or {}
    if not worker.get("enabled") or worker.get("kind") != "github_workflow":
        raise RuntimeError(f"project {project_id} has no enabled github_workflow worker")

    state_path = root / config["state_file"]
    state = _load_json(state_path)

    window_status = worker_window_status(worker, _now())
    if window_status not in {"OPEN", "UNBOUNDED"}:
        raise RuntimeError(
            f"worker dispatch window is {window_status}; refusing out-of-window execution"
        )

    actual_sha = github_branch_sha(state["repository"], state["branch"], token)
    if actual_sha != selected["head_sha"] or actual_sha != state["head_sha"]:
        raise RuntimeError("worker branch moved after controller selection; refusing stale dispatch")

    now = _now()
    experiment = state.get("experiment") or {}
    experiment_id = experiment.get("id")
    task = {
        "schema_version": "1.0",
        "task_id": _task_id(project_id, experiment_id, now),
        "project_id": project_id,
        "repository": state["repository"],
        "experiment_id": experiment_id,
        "issued_at": now.isoformat(),
        "expected_head_sha": state["head_sha"],
        "objective": selected["action"],
        "rationale": controller_output["decision"]["rationale"],
        "constraints": [
            "Perform only the configured read-only worker workflow.",
            "Preserve the frozen methodology and instrument selection.",
            "Do not start any later experimental stage automatically.",
            *(
                [
                    "This is the final authorized finite Checkpoint B. If the executable BTCUSD requirement still fails, stop automatic revalidation and require a new explicit decision."
                ]
                if worker.get("final_attempt")
                else []
            ),
        ],
        "allowed_actions": [selected["action"]],
        "forbidden_actions": state.get("forbidden_actions", []),
        "completion_criteria": [
            "The configured worker workflow completes and its exact production evidence is captured.",
            "Stage 1 passes only if the frozen BTCUSD production book has ack_id != 0 and non-empty executable bid and ask.",
            "Any pass transitions to NEEDS_HUMAN rather than automatically starting a later stage.",
            *(
                [
                    "If the final Checkpoint B remains non-executable, transition to NEEDS_HUMAN and prohibit further automatic retries."
                ]
                if worker.get("final_attempt")
                else []
            ),
        ],
        "safe_outputs": ["RESULT_ONLY", "UPLOAD_ARTIFACT"],
        "approval": {
            "required": False,
            "granted": False,
            "approval_reference": None,
        },
        "protected_data_permissions": {"validation": False, "oos": False},
        "financial_permissions": {
            "spend_money": False,
            "purchase_data_or_services": False,
            "place_live_trade": False,
            "transfer_or_withdraw_funds": False,
        },
        "methodology_change_permitted": False,
        "merge_to_default_branch_permitted": False,
    }
    _validate(root / "schemas" / "task.schema.json", task)

    tasks_dir = root / "tasks"
    results_dir = root / "results"
    tasks_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)
    task_path = tasks_dir / f"{task['task_id']}.json"
    task_path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")

    dispatch = dispatch_workflow(
        state["repository"],
        str(worker["workflow"]),
        str(worker.get("ref") or state["branch"]),
        token,
    )
    run = wait_for_run(
        state["repository"],
        int(dispatch["run_id"]),
        token,
        timeout_seconds=int(worker.get("timeout_seconds", 420)),
    )
    logs = fetch_run_job_logs(state["repository"], int(dispatch["run_id"]), token)

    evaluator = worker.get("evaluator")
    if evaluator != "crypto_stage1_live_validation":
        raise RuntimeError(f"unsupported evaluator: {evaluator}")

    result, raw_payload = _crypto_stage1_result(
        task=task,
        run=run,
        logs=logs,
        final_attempt=bool(worker.get("final_attempt", False)),
    )
    _validate(root / "schemas" / "result.schema.json", result)

    result_path = results_dir / f"{task['task_id']}.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    run_url = str(run.get("html_url") or dispatch.get("html_url") or "")
    updated_state = _update_state_from_result(state, result, run_url)
    _validate(root / "schemas" / "project-state.schema.json", updated_state)
    state_path.write_text(json.dumps(updated_state, indent=2) + "\n", encoding="utf-8")

    return {
        "task": task,
        "dispatch": dispatch,
        "worker_run": {
            "id": run.get("id"),
            "html_url": run.get("html_url"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
        },
        "result": result,
        "raw_worker_payload_captured": raw_payload is not None,
        "files_written": [
            str(task_path.relative_to(root)),
            str(result_path.relative_to(root)),
            str(state_path.relative_to(root)),
        ],
    }
