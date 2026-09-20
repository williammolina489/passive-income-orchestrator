from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any


API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"


class GitHubActionsError(RuntimeError):
    pass


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "passive-income-orchestrator",
    }


def _request_json(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: int = 30,
) -> tuple[int, dict[str, Any] | list[Any] | None]:
    data = None
    headers = _headers(token)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            if not body:
                return response.status, None
            return response.status, json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubActionsError(
            f"GitHub API {method} {url} returned HTTP {exc.code}: {body[:1000]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise GitHubActionsError(f"GitHub API request failed for {url}: {exc}") from exc


def _request_text(url: str, token: str, *, timeout: int = 60) -> str:
    request = urllib.request.Request(url, headers=_headers(token), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubActionsError(
            f"GitHub API GET {url} returned HTTP {exc.code}: {body[:1000]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise GitHubActionsError(f"GitHub API request failed for {url}: {exc}") from exc


def dispatch_workflow(
    repository: str,
    workflow: str,
    ref: str,
    token: str,
) -> dict[str, Any]:
    owner, name = repository.split("/", 1)
    workflow_q = urllib.parse.quote(workflow, safe="")
    url = f"{API_ROOT}/repos/{owner}/{name}/actions/workflows/{workflow_q}/dispatches"
    dispatched_at = datetime.now(UTC)
    status, payload = _request_json("POST", url, token, {"ref": ref})

    if status not in (200, 201, 204):
        raise GitHubActionsError(f"unexpected dispatch status {status}")

    if isinstance(payload, dict) and payload.get("workflow_run_id"):
        return {
            "run_id": int(payload["workflow_run_id"]),
            "run_url": payload.get("run_url"),
            "html_url": payload.get("html_url"),
            "dispatched_at": dispatched_at.isoformat(),
        }

    # Older GitHub API behavior returns 204 with no body. Discover the run.
    runs_url = (
        f"{API_ROOT}/repos/{owner}/{name}/actions/workflows/{workflow_q}/runs"
        f"?branch={urllib.parse.quote(ref, safe='')}&event=workflow_dispatch&per_page=20"
    )
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        _, runs_payload = _request_json("GET", runs_url, token)
        workflow_runs = (
            runs_payload.get("workflow_runs", [])
            if isinstance(runs_payload, dict)
            else []
        )
        for run in workflow_runs:
            created_raw = run.get("created_at")
            if not created_raw:
                continue
            created = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            if created >= dispatched_at.replace(microsecond=0):
                return {
                    "run_id": int(run["id"]),
                    "run_url": run.get("url"),
                    "html_url": run.get("html_url"),
                    "dispatched_at": dispatched_at.isoformat(),
                }
        time.sleep(2)

    raise GitHubActionsError("workflow dispatch succeeded but no matching run was discovered")


def wait_for_run(
    repository: str,
    run_id: int,
    token: str,
    *,
    timeout_seconds: int = 420,
    poll_seconds: int = 5,
) -> dict[str, Any]:
    owner, name = repository.split("/", 1)
    url = f"{API_ROOT}/repos/{owner}/{name}/actions/runs/{run_id}"
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        _, payload = _request_json("GET", url, token)
        if not isinstance(payload, dict):
            raise GitHubActionsError("malformed workflow-run response")
        if payload.get("status") == "completed":
            return payload
        time.sleep(poll_seconds)

    raise GitHubActionsError(
        f"workflow run {run_id} did not complete within {timeout_seconds} seconds"
    )


def fetch_run_job_logs(repository: str, run_id: int, token: str) -> list[dict[str, Any]]:
    owner, name = repository.split("/", 1)
    jobs_url = f"{API_ROOT}/repos/{owner}/{name}/actions/runs/{run_id}/jobs?per_page=100"
    _, payload = _request_json("GET", jobs_url, token)
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

    results: list[dict[str, Any]] = []
    for job in jobs:
        job_id = int(job["id"])
        log_url = f"{API_ROOT}/repos/{owner}/{name}/actions/jobs/{job_id}/logs"
        text = _request_text(log_url, token)
        results.append(
            {
                "job_id": job_id,
                "name": job.get("name"),
                "conclusion": job.get("conclusion"),
                "logs": text,
            }
        )
    return results
