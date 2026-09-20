from __future__ import annotations

from datetime import UTC, datetime, timedelta

from controller.monitor import evaluate_workflow_runs


NOW = datetime(2026, 9, 20, 15, 0, tzinfo=UTC)


def _run(
    *,
    run_id: int,
    name: str = "Forward paper BTC cycle",
    status: str = "completed",
    conclusion: str | None = "success",
    age_minutes: int = 60,
) -> dict:
    created = NOW - timedelta(minutes=age_minutes)
    return {
        "id": run_id,
        "name": name,
        "status": status,
        "conclusion": conclusion,
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "updated_at": created.isoformat().replace("+00:00", "Z"),
        "html_url": f"https://github.com/run/{run_id}",
    }


def test_healthy_successful_run() -> None:
    row = evaluate_workflow_runs(
        [_run(run_id=1, age_minutes=30)],
        workflow_name="Forward paper BTC cycle",
        max_age_minutes=180,
        now=NOW,
    )
    assert row["status"] == "HEALTHY"


def test_stale_successful_run() -> None:
    row = evaluate_workflow_runs(
        [_run(run_id=1, age_minutes=181)],
        workflow_name="Forward paper BTC cycle",
        max_age_minutes=180,
        now=NOW,
    )
    assert row["status"] == "STALE"


def test_latest_failure_is_failure() -> None:
    row = evaluate_workflow_runs(
        [
            _run(run_id=1, age_minutes=60, conclusion="success"),
            _run(run_id=2, age_minutes=30, conclusion="failure"),
        ],
        workflow_name="Forward paper BTC cycle",
        max_age_minutes=180,
        now=NOW,
    )
    assert row["latest_completed_run_id"] == 2
    assert row["status"] == "FAILED"


def test_missing_workflow_is_missing() -> None:
    row = evaluate_workflow_runs(
        [],
        workflow_name="Forward paper BTC cycle",
        max_age_minutes=180,
        now=NOW,
    )
    assert row["status"] == "MISSING"


def test_active_run_is_reported_without_hiding_latest_completed() -> None:
    row = evaluate_workflow_runs(
        [
            _run(run_id=1, age_minutes=60, conclusion="success"),
            _run(run_id=2, age_minutes=1, status="in_progress", conclusion=None),
        ],
        workflow_name="Forward paper BTC cycle",
        max_age_minutes=180,
        now=NOW,
    )
    assert row["status"] == "HEALTHY"
    assert row["active_run_ids"] == [2]
