from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from controller.status import ROOT


API_ROOT = "https://api.github.com"
MARKER_RE = re.compile(
    r"<!-- orchestrator-human-gate project=([a-z0-9_-]+) fingerprint=([0-9a-f]{16}) -->"
)


def _headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "passive-income-orchestrator",
    }


def _request_json(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    data = None
    headers = _headers(token)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            return json.loads(body.decode("utf-8")) if body else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub {method} {url} returned HTTP {exc.code}: {detail[:500]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub {method} {url} failed: {exc}") from exc


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def gate_fingerprint(state: dict[str, Any]) -> str:
    experiment = state.get("experiment") or {}
    material = {
        "project_id": state.get("project_id"),
        "lifecycle_status": state.get("lifecycle_status"),
        "experiment_id": experiment.get("id"),
        "experiment_stage": experiment.get("stage"),
        "human_action_reason": state.get("human_action_reason"),
        "current_blockers": state.get("current_blockers", []),
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def gate_marker(project_id: str, fingerprint: str) -> str:
    return (
        f"<!-- orchestrator-human-gate project={project_id} "
        f"fingerprint={fingerprint} -->"
    )


def build_issue_body(state: dict[str, Any], state_file: str) -> str:
    project_id = str(state["project_id"])
    fingerprint = gate_fingerprint(state)
    experiment = state.get("experiment") or {}
    blockers = state.get("current_blockers") or []
    reason = state.get("human_action_reason") or "Human review is required."

    lines = [
        gate_marker(project_id, fingerprint),
        "",
        "The passive-income orchestrator has reached a fail-closed human gate.",
        "",
        f"Project: {project_id}",
        f"Repository: {state['repository']}",
        f"Lifecycle: {state['lifecycle_status']}",
        f"Experiment: {experiment.get('id')} — {experiment.get('stage')}",
        "",
        f"Why human input is required: {reason}",
    ]
    if blockers:
        lines.extend(["", "Current blockers:"])
        lines.extend(f"- {item}" for item in blockers)
    lines.extend(
        [
            "",
            f"Canonical state: {state_file}",
            "",
            "No live trading, spending, methodology change, protected-data access, "
            "or default-branch merge is authorized by this issue.",
        ]
    )
    return "\n".join(lines)


def _list_issues(repository: str, token: str) -> list[dict[str, Any]]:
    owner, name = repository.split("/", 1)
    url = f"{API_ROOT}/repos/{owner}/{name}/issues?state=all&per_page=100"
    payload = _request_json("GET", url, token)
    return [
        issue
        for issue in (payload or [])
        if isinstance(issue, dict) and "pull_request" not in issue
    ]


def sync_human_gates(
    root: Path = ROOT,
    *,
    repository: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    repository = repository or os.environ.get("GITHUB_REPOSITORY")
    token = token or os.environ.get("GITHUB_TOKEN")
    if not repository:
        raise RuntimeError("GITHUB_REPOSITORY is required")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")

    with (root / "projects.yaml").open("r", encoding="utf-8") as handle:
        registry = yaml.safe_load(handle)["projects"]

    gates: list[tuple[str, str, dict[str, Any]]] = []
    for project_id, config in registry.items():
        state_file = str(config["state_file"])
        state = _load_json(root / state_file)
        if state.get("human_action_required") is True:
            gates.append((project_id, state_file, state))

    issues = _list_issues(repository, token)
    indexed: dict[tuple[str, str], dict[str, Any]] = {}
    open_by_project: dict[str, list[dict[str, Any]]] = {}
    for issue in issues:
        body = str(issue.get("body") or "")
        match = MARKER_RE.search(body)
        if not match:
            continue
        project_id, fingerprint = match.groups()
        indexed[(project_id, fingerprint)] = issue
        if issue.get("state") == "open":
            open_by_project.setdefault(project_id, []).append(issue)

    created: list[int] = []
    retained: list[int] = []
    closed: list[int] = []
    active_projects = {project_id for project_id, _, _ in gates}

    owner, name = repository.split("/", 1)
    for project_id, state_file, state in gates:
        fingerprint = gate_fingerprint(state)
        existing = indexed.get((project_id, fingerprint))
        if existing is not None:
            retained.append(int(existing["number"]))
        else:
            title = f"[Human Gate] {project_id}"
            body = build_issue_body(state, state_file)
            url = f"{API_ROOT}/repos/{owner}/{name}/issues"
            created_issue = _request_json(
                "POST", url, token, {"title": title, "body": body}
            )
            created.append(int(created_issue["number"]))
            existing = created_issue

        current_number = int(existing["number"])
        for old in open_by_project.get(project_id, []):
            old_number = int(old["number"])
            if old_number == current_number:
                continue
            url = f"{API_ROOT}/repos/{owner}/{name}/issues/{old_number}"
            _request_json(
                "PATCH",
                url,
                token,
                {"state": "closed", "state_reason": "completed"},
            )
            closed.append(old_number)

    for project_id, open_issues in open_by_project.items():
        if project_id in active_projects:
            continue
        for issue in open_issues:
            issue_number = int(issue["number"])
            url = f"{API_ROOT}/repos/{owner}/{name}/issues/{issue_number}"
            _request_json(
                "PATCH",
                url,
                token,
                {"state": "closed", "state_reason": "completed"},
            )
            closed.append(issue_number)

    return {
        "schema_version": "1.0",
        "human_gate_count": len(gates),
        "created_issue_numbers": sorted(set(created)),
        "retained_issue_numbers": sorted(set(retained)),
        "closed_issue_numbers": sorted(set(closed)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create or deduplicate orchestrator human-gate GitHub issues."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = sync_human_gates(args.root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
