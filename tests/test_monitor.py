from __future__ import annotations

from datetime import UTC, datetime, timedelta

from controller.monitor import (
    evaluate_http_health,
    evaluate_workflow_runs,
    known_quota_block_active,
    runner_was_never_allocated,
    scheduler_recovery_needed,
)


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


def test_http_health_is_healthy_when_required_fields_match() -> None:
    payload = {
        "status": "ok",
        "process": "ok",
        "database": "ok",
        "paper": True,
        "entries_disabled": False,
        "reconciliation_status": "ok",
        "heartbeat_age_seconds": 1.5,
        "service_status": "idle_non_trading_day",
    }
    status, findings, observed = evaluate_http_health(
        payload,
        required_equals={
            "status": "ok",
            "process": "ok",
            "database": "ok",
            "paper": True,
            "entries_disabled": False,
            "reconciliation_status": "ok",
        },
        max_heartbeat_age_seconds=300,
        include_fields=["status", "service_status", "heartbeat_age_seconds"],
    )
    assert status == "HEALTHY"
    assert findings == []
    assert observed["service_status"] == "idle_non_trading_day"


def test_http_health_fails_closed_on_required_mismatch() -> None:
    payload = {
        "status": "ok",
        "process": "not_running",
        "database": "ok",
        "paper": True,
        "entries_disabled": True,
        "reconciliation_status": "pending",
        "heartbeat_age_seconds": 1,
    }
    status, findings, _ = evaluate_http_health(
        payload,
        required_equals={
            "status": "ok",
            "process": "ok",
            "database": "ok",
            "paper": True,
            "entries_disabled": False,
            "reconciliation_status": "ok",
        },
        max_heartbeat_age_seconds=300,
        include_fields=["status"],
    )
    assert status == "ERROR"
    assert any("process expected" in finding for finding in findings)
    assert any("entries_disabled expected" in finding for finding in findings)


def test_http_health_warns_on_stale_heartbeat() -> None:
    status, findings, _ = evaluate_http_health(
        {
            "status": "ok",
            "process": "ok",
            "database": "ok",
            "paper": True,
            "heartbeat_age_seconds": 301,
        },
        required_equals={
            "status": "ok",
            "process": "ok",
            "database": "ok",
            "paper": True,
        },
        max_heartbeat_age_seconds=300,
        include_fields=["heartbeat_age_seconds"],
    )
    assert status == "WARNING"
    assert any("heartbeat age" in finding for finding in findings)



def test_known_quota_block_expires_after_through_date() -> None:
    block = {
        "active": True,
        "reason_code": "GITHUB_ACTIONS_QUOTA",
        "through_date": "2026-09-30",
    }
    assert known_quota_block_active(
        block,
        now=datetime(2026, 9, 30, 23, 59, tzinfo=UTC),
    )
    assert not known_quota_block_active(
        block,
        now=datetime(2026, 10, 1, 0, 0, tzinfo=UTC),
    )


def test_runner_allocation_block_requires_jobs_with_no_steps_or_runner() -> None:
    assert runner_was_never_allocated(
        [{"id": 1, "steps": [], "runner_name": None}]
    )
    assert not runner_was_never_allocated([])
    assert not runner_was_never_allocated(
        [{"id": 1, "steps": [{"name": "Set up job"}], "runner_name": "GitHub Actions 1"}]
    )


def test_scheduler_recovery_only_for_successful_stale_inactive_cycle() -> None:
    stale = {
        "latest_completed_conclusion": "success",
        "age_minutes": 121.0,
        "active_run_ids": [],
    }
    assert scheduler_recovery_needed(stale, max_age_minutes=120)

    failed = dict(stale, latest_completed_conclusion="failure")
    assert not scheduler_recovery_needed(failed, max_age_minutes=120)

    active = dict(stale, active_run_ids=[42])
    assert not scheduler_recovery_needed(active, max_age_minutes=120)

    recent = dict(stale, age_minutes=119.0)
    assert not scheduler_recovery_needed(recent, max_age_minutes=120)
