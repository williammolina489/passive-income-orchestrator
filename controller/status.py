from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]


class RemoteVerificationError(RuntimeError):
    """Raised when a worker branch cannot be verified safely."""


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_registry(root: Path) -> dict[str, Any]:
    with (root / "projects.yaml").open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("projects"), dict):
        raise ValueError("projects.yaml must contain a top-level projects mapping")
    return data


def _validation_errors(
    project_id: str,
    config: dict[str, Any],
    state: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    for error in sorted(validator.iter_errors(state), key=lambda e: list(e.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{location}: {error.message}")

    if state.get("project_id") != project_id:
        errors.append(
            f"project_id mismatch: registry={project_id!r}, state={state.get('project_id')!r}"
        )

    if state.get("repository") != config.get("repo"):
        errors.append(
            "repository mismatch: "
            f"registry={config.get('repo')!r}, state={state.get('repository')!r}"
        )

    if config.get("enabled") is False and not config.get("reason"):
        errors.append("disabled project must declare a reason in projects.yaml")

    return errors


def github_branch_sha(repository: str, branch: str, token: str | None) -> str:
    encoded_branch = urllib.parse.quote(branch, safe="")
    url = f"https://api.github.com/repos/{repository}/branches/{encoded_branch}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "passive-income-orchestrator",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 404):
            raise RemoteVerificationError(
                f"cannot verify {repository}@{branch}: GitHub returned HTTP {exc.code}; "
                "a cross-repository token may be required"
            ) from exc
        raise RemoteVerificationError(
            f"cannot verify {repository}@{branch}: GitHub returned HTTP {exc.code}"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RemoteVerificationError(
            f"cannot verify {repository}@{branch}: {exc}"
        ) from exc

    try:
        return str(payload["commit"]["sha"])
    except (KeyError, TypeError) as exc:
        raise RemoteVerificationError(
            f"cannot verify {repository}@{branch}: malformed GitHub response"
        ) from exc


def _decision_hint(config: dict[str, Any], state: dict[str, Any], fresh: bool) -> str:
    if not config.get("enabled", False):
        return "STOP"
    if not fresh:
        return "BLOCKED"
    if state.get("human_action_required"):
        return "NEEDS_HUMAN"
    if state.get("lifecycle_status") in {"CLOSED", "STOPPED", "COMPLETE"}:
        return "STOP"
    if (
        state.get("lifecycle_status") in {"ACTIVE", "BLOCKED"}
        and state.get("next_permitted_actions")
    ):
        return "RUN_TASK_CANDIDATE"
    return "WAIT"


def build_report(
    root: Path = ROOT,
    *,
    verify_remote: bool = False,
    token: str | None = None,
) -> dict[str, Any]:
    registry = _load_registry(root)
    schema = _load_json(root / "schemas" / "project-state.schema.json")

    projects: list[dict[str, Any]] = []
    overall_ok = True

    for project_id, config in registry["projects"].items():
        entry: dict[str, Any] = {
            "project_id": project_id,
            "repository": config.get("repo"),
            "enabled": bool(config.get("enabled", False)),
            "state_file": config.get("state_file"),
            "valid": False,
            "fresh": None,
            "dispatch_eligible": False,
            "decision_hint": "BLOCKED",
            "errors": [],
        }

        state_file = config.get("state_file")
        if not state_file:
            entry["errors"].append("registry entry is missing state_file")
            projects.append(entry)
            overall_ok = False
            continue

        state_path = root / state_file
        if not state_path.is_file():
            entry["errors"].append(f"missing state file: {state_file}")
            projects.append(entry)
            overall_ok = False
            continue

        try:
            state = _load_json(state_path)
        except (OSError, json.JSONDecodeError) as exc:
            entry["errors"].append(f"cannot read state file: {exc}")
            projects.append(entry)
            overall_ok = False
            continue

        validation_errors = _validation_errors(project_id, config, state, schema)
        entry["errors"].extend(validation_errors)
        entry["valid"] = not validation_errors
        entry["branch"] = state.get("branch")
        entry["recorded_head_sha"] = state.get("head_sha")
        entry["lifecycle_status"] = state.get("lifecycle_status")
        entry["experiment"] = state.get("experiment")
        entry["human_action_required"] = state.get("human_action_required")
        entry["next_permitted_actions"] = state.get("next_permitted_actions", [])

        if validation_errors:
            projects.append(entry)
            overall_ok = False
            continue

        fresh = True
        if verify_remote:
            try:
                remote_sha = github_branch_sha(
                    state["repository"], state["branch"], token
                )
                entry["remote_head_sha"] = remote_sha
                fresh = remote_sha == state["head_sha"]
                if not fresh:
                    entry["errors"].append(
                        "state is stale: recorded head does not match worker branch"
                    )
                    overall_ok = False
            except RemoteVerificationError as exc:
                entry["errors"].append(str(exc))
                entry["remote_verification_error"] = True
                fresh = False
                overall_ok = False

        entry["fresh"] = fresh if verify_remote else None
        entry["decision_hint"] = _decision_hint(config, state, fresh)

        entry["dispatch_eligible"] = bool(
            config.get("enabled", False)
            and (fresh or not verify_remote)
            and not state.get("human_action_required")
            and state.get("lifecycle_status") in {"ACTIVE", "BLOCKED"}
            and state.get("next_permitted_actions")
        )

        projects.append(entry)

    return {
        "schema_version": "1.0",
        "remote_verification": verify_remote,
        "ok": overall_ok,
        "projects": projects,
    }


def _print_human(report: dict[str, Any]) -> None:
    print(
        f"Portfolio state: {'PASS' if report['ok'] else 'BLOCKED'} "
        f"(remote verification={'on' if report['remote_verification'] else 'off'})"
    )
    for project in report["projects"]:
        status = project.get("lifecycle_status", "INVALID")
        hint = project.get("decision_hint", "BLOCKED")
        eligibility = "yes" if project.get("dispatch_eligible") else "no"
        print(
            f"- {project['project_id']}: {status}; "
            f"decision={hint}; dispatch_eligible={eligibility}"
        )
        for error in project.get("errors", []):
            print(f"    ERROR: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate orchestrator state and optionally verify worker branch SHAs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root (defaults to the installed source tree).",
    )
    parser.add_argument(
        "--verify-remote",
        action="store_true",
        help="Verify every recorded worker branch SHA through the GitHub API.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the complete machine-readable report as JSON.",
    )
    args = parser.parse_args(argv)

    token = os.environ.get("ORCHESTRATOR_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    report = build_report(
        args.root.resolve(),
        verify_remote=args.verify_remote,
        token=token,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
