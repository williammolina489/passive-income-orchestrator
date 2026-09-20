from __future__ import annotations

import json
from pathlib import Path

import yaml

from controller import status


def _write_fixture(tmp_path: Path, *, enabled: bool = True) -> Path:
    (tmp_path / "schemas").mkdir()
    (tmp_path / "state").mkdir()

    source_root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (source_root / "schemas" / "project-state.schema.json").read_text(encoding="utf-8")
    )
    (tmp_path / "schemas" / "project-state.schema.json").write_text(
        json.dumps(schema), encoding="utf-8"
    )

    registry = {
        "version": 1,
        "projects": {
            "example": {
                "repo": "owner/repo",
                "enabled": enabled,
                "role": "research",
                "state_file": "state/example.json",
                **({"reason": "PROJECT_CLOSED"} if not enabled else {}),
            }
        },
    }
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
    assert project["decision_hint"] == "RUN_TASK_CANDIDATE"
    assert project["dispatch_eligible"] is True


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
