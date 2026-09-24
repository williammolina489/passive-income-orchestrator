from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from controller.github_actions import dispatch_workflow
from controller.status import ROOT


API_ROOT = "https://api.github.com"


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "passive-income-orchestrator",
    }


def _get_json(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=_headers(token), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub GET {url} returned HTTP {exc.code}: {body[:500]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub GET {url} failed: {exc}") from exc


def _get_public_json(url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("public health monitor URL must use https")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "passive-income-orchestrator-health/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"health GET returned HTTP {exc.code}: {body[:300]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"health GET failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("health endpoint returned non-object JSON")
    return payload


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def known_quota_block_active(
    quota_block: dict[str, Any] | None,
    *,
    now: datetime,
) -> bool:
    if not isinstance(quota_block, dict) or not quota_block.get("active"):
        return False
    through_date = quota_block.get("through_date")
    if through_date is None:
        return True
    return now.date() <= date.fromisoformat(str(through_date))


def runner_was_never_allocated(jobs: list[dict[str, Any]]) -> bool:
    if not jobs:
        return False
    return all(
        not job.get("steps") and not job.get("runner_name")
        for job in jobs
    )


def scheduler_recovery_needed(
    row: dict[str, Any],
    *,
    max_age_minutes: float,
) -> bool:
    age = row.get("age_minutes")
    return (
        row.get("latest_completed_conclusion") == "success"
        and isinstance(age, (int, float))
        and float(age) > max_age_minutes
        and not row.get("active_run_ids")
    )


def _fetch_run_jobs(
    repository: str,
    run_id: int,
    token: str,
) -> list[dict[str, Any]]:
    owner, name = repository.split("/", 1)
    url = f"{API_ROOT}/repos/{owner}/{name}/actions/runs/{run_id}/jobs?per_page=100"
    payload = _get_json(url, token)
    jobs = payload.get("jobs", [])
    return jobs if isinstance(jobs, list) else []


def evaluate_workflow_runs(
    runs: list[dict[str, Any]],
    *,
    workflow_name: str,
    max_age_minutes: float,
    now: datetime,
) -> dict[str, Any]:
    matching = [run for run in runs if run.get("name") == workflow_name]
    active = [
        run
        for run in matching
        if run.get("status") in {"queued", "in_progress", "waiting", "requested"}
    ]
    completed = [run for run in matching if run.get("status") == "completed"]
    completed.sort(key=lambda run: run.get("created_at") or "", reverse=True)

    if not completed:
        return {
            "name": workflow_name,
            "status": "MISSING",
            "reason": "No completed run was found in the fetched history.",
            "latest_completed_run_id": None,
            "latest_completed_conclusion": None,
            "latest_completed_created_at": None,
            "latest_completed_updated_at": None,
            "age_minutes": None,
            "active_run_ids": [int(run["id"]) for run in active if run.get("id")],
        }

    latest = completed[0]
    created_at = _parse_dt(str(latest["created_at"]))
    age_minutes = max(0.0, (now - created_at).total_seconds() / 60.0)
    conclusion = latest.get("conclusion")

    if conclusion != "success":
        status = "FAILED"
        reason = f"Latest completed run concluded {conclusion!r}."
    elif age_minutes > max_age_minutes:
        status = "STALE"
        reason = (
            f"Latest successful completed run is {age_minutes:.1f} minutes old, "
            f"above the {max_age_minutes:.1f}-minute monitor threshold."
        )
    else:
        status = "HEALTHY"
        reason = "Latest completed run succeeded and is within the freshness threshold."

    return {
        "name": workflow_name,
        "status": status,
        "reason": reason,
        "latest_completed_run_id": int(latest["id"]),
        "latest_completed_conclusion": conclusion,
        "latest_completed_created_at": latest.get("created_at"),
        "latest_completed_updated_at": latest.get("updated_at"),
        "latest_completed_url": latest.get("html_url"),
        "age_minutes": round(age_minutes, 3),
        "active_run_ids": [int(run["id"]) for run in active if run.get("id")],
    }


def monitor_github_workflows(
    *,
    project_id: str,
    config: dict[str, Any],
    token: str,
    now: datetime,
    quota_block: dict[str, Any] | None = None,
    allow_scheduler_recovery: bool = False,
) -> dict[str, Any]:
    monitor = config["monitor"]
    repository = config["repo"]
    owner, name = repository.split("/", 1)
    url = f"{API_ROOT}/repos/{owner}/{name}/actions/runs?per_page=100"
    payload = _get_json(url, token)
    runs = payload.get("workflow_runs", [])

    max_age_minutes = float(monitor["max_age_minutes"])
    rows = [
        evaluate_workflow_runs(
            runs,
            workflow_name=str(workflow_name),
            max_age_minutes=max_age_minutes,
            now=now,
        )
        for workflow_name in monitor["workflows"]
    ]

    quota_active = known_quota_block_active(quota_block, now=now)
    quota_reason_code = (
        str(quota_block.get("reason_code") or "GITHUB_ACTIONS_QUOTA")
        if quota_active and isinstance(quota_block, dict)
        else None
    )

    for row in rows:
        if (
            row["status"] == "FAILED"
            and quota_active
            and row.get("latest_completed_run_id") is not None
        ):
            jobs = _fetch_run_jobs(
                repository,
                int(row["latest_completed_run_id"]),
                token,
            )
            if runner_was_never_allocated(jobs):
                row["status"] = "INFRASTRUCTURE_BLOCKED"
                row["reason_code"] = quota_reason_code
                row["reason"] = (
                    "Latest workflow run failed before any runner step started "
                    "while the account Actions allowance is known exhausted. "
                    "Treat this as infrastructure-blocked, not a bot or strategy failure."
                )

    recovery = monitor.get("scheduler_recovery") or {}
    if (
        allow_scheduler_recovery
        and recovery.get("enabled")
        and not quota_active
    ):
        recovery_max_age = float(recovery["max_age_minutes"])
        recovery_ref = str(recovery.get("ref") or "main")
        recovery_workflows = recovery.get("workflows") or {}
        for row in rows:
            workflow_file = recovery_workflows.get(row["name"])
            if not workflow_file:
                continue
            if not scheduler_recovery_needed(
                row,
                max_age_minutes=recovery_max_age,
            ):
                continue
            try:
                dispatched = dispatch_workflow(
                    repository,
                    str(workflow_file),
                    recovery_ref,
                    token,
                )
            except Exception as exc:
                row["status"] = "FAILED"
                row["reason"] = (
                    "The latest successful cycle exceeded the scheduler-liveness "
                    f"threshold, but guarded recovery dispatch failed: {type(exc).__name__}: {exc}"
                )
                row["scheduler_recovery"] = {
                    "action": "ERROR",
                    "workflow": str(workflow_file),
                }
            else:
                row["scheduler_recovery"] = {
                    "action": "DISPATCHED",
                    "workflow": str(workflow_file),
                    "run_id": dispatched.get("run_id"),
                    "run_url": dispatched.get("html_url"),
                }

    statuses = {row["status"] for row in rows}
    if "FAILED" in statuses or "MISSING" in statuses:
        overall = "ERROR"
    elif "INFRASTRUCTURE_BLOCKED" in statuses:
        overall = "INFRASTRUCTURE_BLOCKED"
    elif "STALE" in statuses:
        overall = "WARNING"
    else:
        overall = "HEALTHY"

    reason_code = None
    if overall == "INFRASTRUCTURE_BLOCKED":
        reason_code = quota_reason_code or "GITHUB_ACTIONS_RUNNER_ALLOCATION"

    return {
        "schema_version": "1.0",
        "project_id": project_id,
        "repository": repository,
        "checked_at": now.isoformat(),
        "monitor_kind": "github_actions_workflows",
        "max_age_minutes": max_age_minutes,
        "overall_status": overall,
        "reason_code": reason_code,
        "known_quota_block_active": quota_active,
        "workflows": rows,
    }


def evaluate_http_health(
    payload: dict[str, Any],
    *,
    required_equals: dict[str, Any],
    max_heartbeat_age_seconds: float | None,
    include_fields: list[str],
) -> tuple[str, list[str], dict[str, Any]]:
    problems: list[str] = []
    warnings: list[str] = []

    for key, expected in required_equals.items():
        actual = payload.get(key)
        if actual != expected:
            problems.append(f"{key} expected {expected!r}, got {actual!r}")

    if max_heartbeat_age_seconds is not None:
        raw_age = payload.get("heartbeat_age_seconds")
        try:
            age = float(raw_age)
        except (TypeError, ValueError):
            warnings.append("heartbeat_age_seconds is missing or non-numeric")
        else:
            if age > max_heartbeat_age_seconds:
                warnings.append(
                    f"heartbeat age {age:.1f}s exceeds {max_heartbeat_age_seconds:.1f}s"
                )

    observed = {key: payload.get(key) for key in include_fields}
    if problems:
        overall = "ERROR"
    elif warnings:
        overall = "WARNING"
    else:
        overall = "HEALTHY"
    return overall, problems + warnings, observed


def monitor_http_json(
    *,
    project_id: str,
    config: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    monitor = config["monitor"]
    repository = config["repo"]
    url = str(monitor["url"])
    payload = _get_public_json(url)
    required = monitor.get("required_equals") or {}
    include_fields = [str(field) for field in monitor.get("include_fields", [])]
    max_heartbeat = monitor.get("max_heartbeat_age_seconds")
    max_heartbeat_value = (
        float(max_heartbeat) if max_heartbeat is not None else None
    )
    overall, findings, observed = evaluate_http_health(
        payload,
        required_equals=required,
        max_heartbeat_age_seconds=max_heartbeat_value,
        include_fields=include_fields,
    )
    return {
        "schema_version": "1.0",
        "project_id": project_id,
        "repository": repository,
        "checked_at": now.isoformat(),
        "monitor_kind": "http_json",
        "url": url,
        "overall_status": overall,
        "findings": findings,
        "observed": observed,
    }


def _error_observation(
    *,
    project_id: str,
    config: dict[str, Any],
    now: datetime,
    error: Exception,
) -> dict[str, Any]:
    monitor = config.get("monitor") or {}
    return {
        "schema_version": "1.0",
        "project_id": project_id,
        "repository": config.get("repo"),
        "checked_at": now.isoformat(),
        "monitor_kind": monitor.get("kind"),
        "overall_status": "ERROR",
        "findings": [f"{type(error).__name__}: {error}"],
    }


def monitor_project(
    *,
    project_id: str,
    config: dict[str, Any],
    token: str,
    now: datetime,
    quota_block: dict[str, Any] | None = None,
    allow_scheduler_recovery: bool = False,
) -> dict[str, Any]:
    monitor = config["monitor"]
    kind = monitor.get("kind")
    if kind == "github_actions_workflows":
        return monitor_github_workflows(
            project_id=project_id,
            config=config,
            token=token,
            now=now,
            quota_block=quota_block,
            allow_scheduler_recovery=allow_scheduler_recovery,
        )
    if kind == "http_json":
        return monitor_http_json(
            project_id=project_id,
            config=config,
            now=now,
        )
    raise ValueError(f"unsupported monitor kind: {kind!r}")


def run_monitors(
    root: Path = ROOT,
    *,
    token: str | None = None,
    allow_scheduler_recovery: bool = False,
) -> dict[str, Any]:
    token = token or os.environ.get("ORCHESTRATOR_GITHUB_TOKEN")
    if not token:
        raise RuntimeError("ORCHESTRATOR_GITHUB_TOKEN is required")

    with (root / "projects.yaml").open("r", encoding="utf-8") as handle:
        registry_document = yaml.safe_load(handle)
    registry = registry_document["projects"]
    github_infrastructure = (
        (registry_document.get("infrastructure") or {}).get("github_actions") or {}
    )
    quota_block = github_infrastructure.get("known_quota_block")

    observations_dir = root / "observations"
    observations_dir.mkdir(exist_ok=True)
    now = datetime.now(UTC)

    observations: list[dict[str, Any]] = []
    for project_id, config in registry.items():
        monitor = config.get("monitor")
        if not isinstance(monitor, dict) or not monitor.get("enabled"):
            continue
        try:
            observation = monitor_project(
                project_id=project_id,
                config=config,
                token=token,
                now=now,
                quota_block=quota_block,
                allow_scheduler_recovery=allow_scheduler_recovery,
            )
        except Exception as exc:
            observation = _error_observation(
                project_id=project_id,
                config=config,
                now=now,
                error=exc,
            )
        path = observations_dir / f"{project_id}.json"
        path.write_text(json.dumps(observation, indent=2) + "\n", encoding="utf-8")
        observations.append(observation)

    overall = "HEALTHY"
    statuses = {observation["overall_status"] for observation in observations}
    if "ERROR" in statuses:
        overall = "ERROR"
    elif "WARNING" in statuses:
        overall = "WARNING"

    return {
        "schema_version": "1.0",
        "checked_at": now.isoformat(),
        "overall_status": overall,
        "observations": observations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh read-only operational observations for configured projects."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--allow-scheduler-recovery",
        action="store_true",
        help=(
            "Allow guarded workflow-dispatch recovery only for configured "
            "successful-but-stale scheduler gaps."
        ),
    )
    args = parser.parse_args(argv)

    report = run_monitors(
        args.root.resolve(),
        allow_scheduler_recovery=args.allow_scheduler_recovery,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
