from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from controller.status import ROOT


PROJECT_ID = "crypto_funding_basis"
E002_OBS_PREFIX = "e002_crypto_funding_basis_checkpoint_"
CHECKPOINTS = ("A", "B", "C")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _observation_path(root: Path, checkpoint: str) -> Path:
    return root / "observations" / f"{E002_OBS_PREFIX}{checkpoint}.json"


def _previous_checkpoints(checkpoint: str) -> tuple[str, ...]:
    index = CHECKPOINTS.index(checkpoint)
    return CHECKPOINTS[:index]


def _checkpoint_observation(root: Path, checkpoint: str) -> dict[str, Any] | None:
    path = _observation_path(root, checkpoint)
    if not path.is_file():
        return None
    return _load_json(path)


def preflight(root: Path, checkpoint: str) -> dict[str, Any]:
    if checkpoint not in CHECKPOINTS:
        raise ValueError(f"invalid checkpoint: {checkpoint}")

    state = _load_json(root / "state" / "crypto_funding_basis.json")
    experiment = state.get("experiment") or {}

    if state.get("project_id") != PROJECT_ID:
        raise ValueError("unexpected project state")
    if experiment.get("id") != "E002":
        return {"run": False, "reason": "E002 is not the active experiment"}
    if state.get("lifecycle_status") != "ACTIVE":
        return {
            "run": False,
            "reason": f"project lifecycle is {state.get('lifecycle_status')}, not ACTIVE",
        }
    if experiment.get("status") != "RUNNING":
        return {
            "run": False,
            "reason": f"E002 status is {experiment.get('status')}, not RUNNING",
        }
    if state.get("human_action_required") is True:
        return {"run": False, "reason": "project is human-gated"}

    existing = _checkpoint_observation(root, checkpoint)
    if existing is not None:
        return {
            "run": False,
            "reason": f"checkpoint {checkpoint} already has a durable observation",
        }

    for prior in _previous_checkpoints(checkpoint):
        observation = _checkpoint_observation(root, prior)
        if observation is None:
            return {
                "run": False,
                "reason": f"prior checkpoint {prior} has no durable observation",
            }
        if observation.get("status") != "PASS":
            return {
                "run": False,
                "reason": f"prior checkpoint {prior} did not PASS",
            }

    return {
        "run": True,
        "reason": "authorized checkpoint sequence is ready",
        "expected_sha": state["head_sha"],
        "repository": state["repository"],
        "branch": state["branch"],
    }


def parse_result_log(text: str, checkpoint: str) -> dict[str, Any]:
    prefix = "E002_FEASIBILITY_RESULT="
    payloads = [
        line[len(prefix):]
        for line in text.splitlines()
        if line.startswith(prefix)
    ]
    if len(payloads) != 1:
        raise ValueError(
            f"expected exactly one {prefix} line, found {len(payloads)}"
        )
    payload = json.loads(payloads[0])

    if payload.get("experiment_id") != "E002":
        raise ValueError("result experiment_id mismatch")
    if payload.get("checkpoint") != checkpoint:
        raise ValueError("result checkpoint mismatch")
    if not isinstance(payload.get("passed"), bool):
        raise ValueError("result passed field must be boolean")
    if payload.get("authentication_used") is not False:
        raise ValueError("authenticated access was used")
    if payload.get("orders_or_writes_performed") is not False:
        raise ValueError("orders/writes were performed")
    if payload.get("profitability_calculated") is not False:
        raise ValueError("profitability was calculated")

    funding = payload.get("funding_schema")
    if not isinstance(funding, dict):
        raise ValueError("missing funding_schema")
    forbidden_exact = {"funding_rate", "estimated_funding_rate", "finalized_funding_rate"}
    for key in funding:
        if key in forbidden_exact:
            raise ValueError(f"funding magnitude leaked through field {key}")

    if payload.get("passed") is True and payload.get("failure_reasons"):
        raise ValueError("PASS result contains failure_reasons")

    return payload


def _append_source(state: dict[str, Any], value: str) -> None:
    sources = list(state.get("source_documents") or [])
    if value not in sources:
        sources.append(value)
    state["source_documents"] = sources


def _transition_valid_result(
    state: dict[str, Any],
    *,
    checkpoint: str,
    result: dict[str, Any],
    run_url: str | None,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(state))
    updated["state_revision"] = int(updated["state_revision"]) + 1
    updated["updated_at"] = datetime.now(UTC).isoformat()
    updated["governance"]["methodology_frozen"] = True
    updated["governance"]["performance_viewed"] = False
    updated["governance"]["data_integrity_status"] = "PASS"

    observation_ref = f"observations/{E002_OBS_PREFIX}{checkpoint}.json"
    _append_source(updated, observation_ref)
    if run_url:
        _append_source(updated, run_url)

    experiment = updated["experiment"]

    if result["passed"] is False:
        reasons = [str(item) for item in result.get("failure_reasons", [])]
        updated["lifecycle_status"] = "NEEDS_HUMAN"
        experiment["stage"] = f"Checkpoint {checkpoint} / feasibility stop"
        experiment["status"] = "BLOCKED"
        updated["current_blockers"] = [
            f"E002 checkpoint {checkpoint} produced valid production evidence that failed the frozen feasibility gate: "
            + (", ".join(reasons) if reasons else "unspecified frozen-gate failure")
        ]
        updated["next_permitted_actions"] = []
        updated["human_action_required"] = True
        updated["human_action_reason"] = (
            f"E002 is BLOCKED / STOP after valid checkpoint {checkpoint}. "
            "The preregistration prohibits additional checkpoints or instrument/venue substitutions inside E002. "
            "A new explicit human decision is required for any subsequent experiment."
        )
        updated["notes"] = (
            f"E002 stopped at checkpoint {checkpoint} on valid engineering evidence. "
            "No profitability was calculated, no authentication was used, and no orders/writes were performed."
        )
        return updated

    if checkpoint != "C":
        next_checkpoint = CHECKPOINTS[CHECKPOINTS.index(checkpoint) + 1]
        updated["lifecycle_status"] = "ACTIVE"
        experiment["stage"] = f"Checkpoint {checkpoint} PASS / {next_checkpoint} pending"
        experiment["status"] = "RUNNING"
        updated["current_blockers"] = []
        updated["next_permitted_actions"] = [
            f"Execute only authorized E002 checkpoint {next_checkpoint} inside its precommitted 2026-09-23 window, provided all prior checkpoints remain PASS."
        ]
        updated["human_action_required"] = False
        updated["human_action_reason"] = None
        updated["notes"] = (
            f"E002 checkpoint {checkpoint} passed the frozen engineering-feasibility gate. "
            f"Checkpoint {next_checkpoint} remains pending. No profitability evidence was collected."
        )
        return updated

    updated["lifecycle_status"] = "NEEDS_HUMAN"
    experiment["stage"] = "Finite feasibility sequence complete"
    experiment["status"] = "PASS"
    updated["current_blockers"] = []
    updated["next_permitted_actions"] = []
    updated["human_action_required"] = True
    updated["human_action_reason"] = (
        "E002 PASS: all three frozen feasibility checkpoints passed. "
        "This authorizes only design of a later separately preregistered prospective performance experiment; "
        "it does not authorize performance collection, paper trading, authenticated access, or live trading."
    )
    updated["notes"] = (
        "E002 finite engineering-feasibility sequence passed A/B/C. "
        "No profitability was calculated and the system stopped at the required human gate."
    )
    return updated


def _transition_technical_failure(
    state: dict[str, Any],
    *,
    checkpoint: str,
    log_text: str,
    run_url: str | None,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(state))
    updated["state_revision"] = int(updated["state_revision"]) + 1
    updated["updated_at"] = datetime.now(UTC).isoformat()
    updated["lifecycle_status"] = "NEEDS_HUMAN"
    updated["experiment"]["stage"] = f"Checkpoint {checkpoint} technical failure"
    updated["experiment"]["status"] = "WAITING"
    updated["governance"]["data_integrity_status"] = "UNKNOWN"
    updated["current_blockers"] = [
        f"E002 checkpoint {checkpoint} did not produce a valid bounded production result. "
        "The preregistration allows at most one technical retry inside the same frozen window, "
        "but technical-failure classification must be reviewed before any retry."
    ]
    updated["next_permitted_actions"] = []
    updated["human_action_required"] = True
    updated["human_action_reason"] = (
        f"Checkpoint {checkpoint} ended before valid E002 evidence was recorded. "
        "Review the technical failure. If and only if it qualifies under the preregistered technical-retry exception "
        "and the same authorized window remains open, one retry may be explicitly approved."
    )
    updated["notes"] = (
        "Technical failure excerpt: " + log_text[-2000:].replace("\n", " ")
    )
    if run_url:
        _append_source(updated, run_url)
    return updated


def record(
    root: Path,
    *,
    checkpoint: str,
    log_path: Path,
    exit_code: int,
    run_url: str | None,
) -> dict[str, Any]:
    if checkpoint not in CHECKPOINTS:
        raise ValueError(f"invalid checkpoint: {checkpoint}")

    state_path = root / "state" / "crypto_funding_basis.json"
    state = _load_json(state_path)

    if _checkpoint_observation(root, checkpoint) is not None:
        raise RuntimeError(f"checkpoint {checkpoint} already recorded")

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    observation: dict[str, Any]

    if exit_code != 0:
        observation = {
            "schema_version": "1.0",
            "project_id": PROJECT_ID,
            "experiment_id": "E002",
            "checkpoint": checkpoint,
            "status": "TECHNICAL_FAILURE",
            "recorded_at": datetime.now(UTC).isoformat(),
            "workflow_run_url": run_url,
            "exit_code": exit_code,
            "valid_e002_result": False,
            "log_excerpt": log_text[-4000:],
        }
        updated = _transition_technical_failure(
            state,
            checkpoint=checkpoint,
            log_text=log_text,
            run_url=run_url,
        )
    else:
        result = parse_result_log(log_text, checkpoint)
        observation = {
            "schema_version": "1.0",
            "project_id": PROJECT_ID,
            "experiment_id": "E002",
            "checkpoint": checkpoint,
            "status": "PASS" if result["passed"] else "BLOCKED",
            "recorded_at": datetime.now(UTC).isoformat(),
            "workflow_run_url": run_url,
            "exit_code": 0,
            "valid_e002_result": True,
            "result": result,
        }
        updated = _transition_valid_result(
            state,
            checkpoint=checkpoint,
            result=result,
            run_url=run_url,
        )

    _write_json(_observation_path(root, checkpoint), observation)
    _write_json(state_path, updated)
    return observation


def _write_outputs(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key in ("run", "reason", "expected_sha", "repository", "branch"):
            if key not in payload:
                continue
            value = payload[key]
            if isinstance(value, bool):
                value = "true" if value else "false"
            text = str(value)
            if "\n" in text or "\r" in text:
                raise ValueError(f"unsafe multiline output: {key}")
            handle.write(f"{key}={text}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate and record E002 scheduled checkpoints.")
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("preflight")
    pre.add_argument("checkpoint", choices=CHECKPOINTS)
    pre.add_argument("--root", type=Path, default=ROOT)
    pre.add_argument("--github-output", type=Path)

    rec = sub.add_parser("record")
    rec.add_argument("checkpoint", choices=CHECKPOINTS)
    rec.add_argument("log_file", type=Path)
    rec.add_argument("--exit-code", type=int, required=True)
    rec.add_argument("--root", type=Path, default=ROOT)
    rec.add_argument("--run-url")

    args = parser.parse_args(argv)

    if args.command == "preflight":
        report = preflight(args.root.resolve(), args.checkpoint)
        if args.github_output:
            _write_outputs(args.github_output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    observation = record(
        args.root.resolve(),
        checkpoint=args.checkpoint,
        log_path=args.log_file.resolve(),
        exit_code=args.exit_code,
        run_url=args.run_url,
    )
    print(json.dumps(observation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
