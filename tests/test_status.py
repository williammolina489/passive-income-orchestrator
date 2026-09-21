from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from controller import status


def _write_fixture(
    tmp_path: Path,
    *,
    enabled: bool = True,
    worker_enabled: bool = True,
    worker_window: bool = False,
) -> Path:
    (tmp_path / "schemas").mkdir()
    (tmp_path / "state").mkdir()

    source_root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (source_root / "schemas" / "project-state.schema.json").read_text(encoding="utf-8")
    )
    (tmp_path / "schemas" / "project-state.schema.json").write_text(
        json.dumps(schema), encoding="utf-8"
    )

    project = {
        "repo": "owner/repo",
        "enabled": enabled,
        "role": "research",
        "state_file": "state/example.json",
    }
    if enabled:
        project["worker"] = (
            {
                "enabled": True,
                "kind": "github_workflow",
                "workflow": "worker.yml",
                "ref": "research/e001",
                "evaluator": "crypto_stage1_live_validation",
                **(
                    {
                        "dispatch_not_before": "2026-09-21T10:00:00-04:00",
                        "dispatch_not_after": "2026-09-21T15:00:00-04:00",
                        "final_attempt": True,
                    }
                    if worker_window
                    else {}
                ),
            }
            if worker_enabled
            else {"enabled": False, "reason": "NOT_READY"}
        )
    else:
        project["reason"] = "PROJECT_CLOSED"

    registry = {"version": 1, "projects": {"example": project}}
    (tmp_path / "projects.yaml").write_text(
        yaml.safe_dump(registry), encoding="utf-8"
    )

    state_payload = {
        "schema_version": "1.0",
        "state_revision": 1,
        "project_id": "example",
        "repository": "owner/repo",
        "branch": "research/e001",
        "head_sha": "a" * 40,
        "lifecycle_status": "BLOCKED",
        "experiment": {
            "id": "E001",
            "stage": "Stage 1",
            "status": "BLOCKED",
        },
        "governance": {
            "methodology_frozen": True,
            "performance_viewed": False,
            "validation_state": "NOT_APPLICABLE",
            "oos_state": "NOT_APPLICABLE",
            "data_integrity_status": "BLOCKED",
        },
        "current_blockers": ["Need one exact observation."],
        "next_permitted_actions": ["Repeat the read-only observation."],
        "forbidden_actions": ["Do not trade."],
        "human_action_required": False,
        "human_action_reason": None,
        "updated_at": "2026-09-20T12:26:00Z",
        "source_documents": ["PROJECT_STATE.md"],
        "last_result_task_id": None,
        "notes": None,
    }
    (tmp_path / "state" / "example.json").write_text(
        json.dumps(state_payload), encoding="utf-8"
    )
    return tmp_path


def test_valid_local_state_is_candidate(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)
    report = status.build_report(root)
    project = report["projects"][0]

    assert report["ok"] is True
    assert project["valid"] is True
    assert project["worker_ready"] is True
    assert project["decision_hint"] == "RUN_TASK_CANDIDATE"
    assert project["dispatch_eligible"] is True


def test_enabled_project_without_worker_waits(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path, worker_enabled=False)
    report = status.build_report(root)
    project = report["projects"][0]

    assert report["ok"] is True
    assert project["worker_ready"] is False
    assert project["decision_hint"] == "WAIT"
    assert project["dispatch_eligible"] is False


def test_disabled_project_cannot_dispatch(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path, enabled=False)
    report = status.build_report(root)
    project = report["projects"][0]

    assert project["decision_hint"] == "STOP"
    assert project["dispatch_eligible"] is False


def test_remote_sha_mismatch_fails_closed(tmp_path: Path, monkeypatch) -> None:
    root = _write_fixture(tmp_path)
    monkeypatch.setattr(status, "github_branch_sha", lambda *_args, **_kwargs: "b" * 40)

    report = status.build_report(root, verify_remote=True, token="test")
    project = report["projects"][0]

    assert report["ok"] is False
    assert project["fresh"] is False
    assert project["decision_hint"] == "BLOCKED"
    assert project["dispatch_eligible"] is False
    assert any("state is stale" in error for error in project["errors"])


def test_project_id_mismatch_is_invalid(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path)
    state_path = root / "state" / "example.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["project_id"] = "wrong"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    report = status.build_report(root)
    project = report["projects"][0]

    assert report["ok"] is False
    assert project["valid"] is False
    assert project["dispatch_eligible"] is False


def test_worker_waits_before_dispatch_window(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path, worker_window=True)
    report = status.build_report(
        root,
        now=datetime(2026, 9, 21, 13, 59, tzinfo=UTC),
    )
    project = report["projects"][0]

    assert project["worker_window_status"] == "BEFORE"
    assert project["decision_hint"] == "WAIT"
    assert project["dispatch_eligible"] is False


def test_worker_dispatches_inside_window(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path, worker_window=True)
    report = status.build_report(
        root,
        now=datetime(2026, 9, 21, 14, 30, tzinfo=UTC),
    )
    project = report["projects"][0]

    assert project["worker_window_status"] == "OPEN"
    assert project["decision_hint"] == "RUN_TASK_CANDIDATE"
    assert project["dispatch_eligible"] is True


def test_worker_waits_after_dispatch_window(tmp_path: Path) -> None:
    root = _write_fixture(tmp_path, worker_window=True)
    report = status.build_report(
        root,
        now=datetime(2026, 9, 21, 19, 1, tzinfo=UTC),
    )
    project = report["projects"][0]

    assert project["worker_window_status"] == "AFTER"
    assert project["decision_hint"] == "WAIT"
    assert project["dispatch_eligible"] is False
