from __future__ import annotations

import json
from pathlib import Path

import pytest

from controller.decide import build_candidates, build_dynamic_schema, validate_decision


def _report() -> dict:
    return {
        "projects": [
            {
                "project_id": "active",
                "repository": "owner/active",
                "branch": "research/e001",
                "recorded_head_sha": "a" * 40,
                "lifecycle_status": "BLOCKED",
                "experiment": {"id": "E001", "stage": "Stage 1", "status": "BLOCKED"},
                "dispatch_eligible": True,
                "next_permitted_actions": ["Repeat read-only validation."],
            },
            {
                "project_id": "closed",
                "repository": "owner/closed",
                "branch": "research/e003",
                "recorded_head_sha": "b" * 40,
                "lifecycle_status": "CLOSED",
                "experiment": {"id": "E003", "stage": "TRAIN", "status": "STOPPED"},
                "dispatch_eligible": False,
                "next_permitted_actions": [],
            },
        ]
    }


def _base_schema() -> dict:
    path = Path(__file__).resolve().parents[1] / "schemas" / "controller-decision.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidates_include_only_dispatchable_actions() -> None:
    candidates = build_candidates(_report())
    assert len(candidates) == 1
    assert candidates[0]["candidate_id"] == "active::0"
    assert candidates[0]["action"] == "Repeat read-only validation."


def test_dynamic_schema_limits_candidate_ids() -> None:
    candidates = build_candidates(_report())
    schema = build_dynamic_schema(_base_schema(), candidates)
    assert schema["properties"]["candidate_id"]["enum"] == ["NONE", "active::0"]


def test_run_task_must_select_verified_candidate() -> None:
    candidates = build_candidates(_report())
    schema = build_dynamic_schema(_base_schema(), candidates)
    decision = {
        "schema_version": "1.0",
        "decision": "RUN_TASK",
        "candidate_id": "active::0",
        "rationale": "It is the only verified bounded action.",
    }
    selected = validate_decision(decision, schema, candidates)
    assert selected is not None
    assert selected["project_id"] == "active"


def test_non_run_decision_must_select_none() -> None:
    candidates = build_candidates(_report())
    schema = build_dynamic_schema(_base_schema(), candidates)
    decision = {
        "schema_version": "1.0",
        "decision": "WAIT",
        "candidate_id": "active::0",
        "rationale": "Wait.",
    }
    with pytest.raises(ValueError):
        validate_decision(decision, schema, candidates)
