from __future__ import annotations

import json
from pathlib import Path

from controller.e002_schedule import parse_result_log, preflight


def _state(root: Path, *, status: str = "RUNNING", lifecycle: str = "ACTIVE") -> None:
    (root / "state").mkdir(parents=True, exist_ok=True)
    payload = {
        "project_id": "crypto_funding_basis",
        "repository": "owner/repo",
        "branch": "research/e002",
        "head_sha": "a" * 40,
        "lifecycle_status": lifecycle,
        "experiment": {"id": "E002", "stage": "A pending", "status": status},
        "human_action_required": False,
    }
    (root / "state" / "crypto_funding_basis.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def test_a_preflight_runs_when_e002_is_active(tmp_path: Path) -> None:
    _state(tmp_path)
    report = preflight(tmp_path, "A")
    assert report["run"] is True
    assert report["expected_sha"] == "a" * 40


def test_b_requires_a_pass(tmp_path: Path) -> None:
    _state(tmp_path)
    report = preflight(tmp_path, "B")
    assert report["run"] is False

    (tmp_path / "observations").mkdir()
    (tmp_path / "observations" / "e002_crypto_funding_basis_checkpoint_A.json").write_text(
        json.dumps({"status": "PASS"}), encoding="utf-8"
    )
    report = preflight(tmp_path, "B")
    assert report["run"] is True


def test_blocked_prior_checkpoint_stops_sequence(tmp_path: Path) -> None:
    _state(tmp_path)
    (tmp_path / "observations").mkdir()
    (tmp_path / "observations" / "e002_crypto_funding_basis_checkpoint_A.json").write_text(
        json.dumps({"status": "BLOCKED"}), encoding="utf-8"
    )
    report = preflight(tmp_path, "B")
    assert report["run"] is False


def test_parse_result_accepts_redacted_pass() -> None:
    payload = {
        "experiment_id": "E002",
        "checkpoint": "A",
        "passed": True,
        "failure_reasons": [],
        "metadata": {"compatible": True},
        "books": {},
        "funding_schema": {
            "estimated_rate_present_and_finite": True,
            "finalized_rate_present_and_finite": True,
            "schema_ok": True,
        },
        "authentication_used": False,
        "orders_or_writes_performed": False,
        "profitability_calculated": False,
    }
    result = parse_result_log(
        "E002_FEASIBILITY_RESULT=" + json.dumps(payload),
        "A",
    )
    assert result["passed"] is True


def test_parse_result_rejects_funding_magnitude() -> None:
    payload = {
        "experiment_id": "E002",
        "checkpoint": "A",
        "passed": True,
        "failure_reasons": [],
        "metadata": {"compatible": True},
        "books": {},
        "funding_schema": {"schema_ok": True, "funding_rate": "0.1"},
        "authentication_used": False,
        "orders_or_writes_performed": False,
        "profitability_calculated": False,
    }
    try:
        parse_result_log("E002_FEASIBILITY_RESULT=" + json.dumps(payload), "A")
    except ValueError as exc:
        assert "funding magnitude" in str(exc)
    else:
        raise AssertionError("expected funding-magnitude rejection")
