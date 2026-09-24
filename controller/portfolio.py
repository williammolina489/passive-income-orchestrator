from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from controller.status import ROOT, build_report


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_portfolio(root: Path = ROOT) -> dict[str, Any]:
    with (root / "projects.yaml").open("r", encoding="utf-8") as handle:
        registry = yaml.safe_load(handle)["projects"]

    status_report = build_report(root, verify_remote=False)
    status_by_id = {row["project_id"]: row for row in status_report["projects"]}

    projects: list[dict[str, Any]] = []
    for project_id, config in registry.items():
        state = _load_json(root / config["state_file"])
        observation = _load_json(root / "observations" / f"{project_id}.json")
        status = status_by_id[project_id]

        projects.append(
            {
                "project_id": project_id,
                "repository": config["repo"],
                "role": config.get("role"),
                "enabled": bool(config.get("enabled", False)),
                "lifecycle_status": state.get("lifecycle_status") if state else "MISSING",
                "experiment": state.get("experiment") if state else None,
                "human_action_required": state.get("human_action_required") if state else None,
                "human_action_reason": state.get("human_action_reason") if state else None,
                "worker_ready": bool(status.get("worker_ready")),
                "dispatch_eligible": bool(status.get("dispatch_eligible")),
                "decision_hint": status.get("decision_hint"),
                "current_blockers": state.get("current_blockers", []) if state else [],
                "next_permitted_actions": state.get("next_permitted_actions", []) if state else [],
                "last_result_task_id": state.get("last_result_task_id") if state else None,
                "state_updated_at": state.get("updated_at") if state else None,
                "operational_monitor_status": observation.get("overall_status") if observation else None,
                "operational_monitor_reason_code": observation.get("reason_code") if observation else None,
                "operational_checked_at": observation.get("checked_at") if observation else None,
            }
        )

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "project_count": len(projects),
        "enabled_count": sum(1 for row in projects if row["enabled"]),
        "dispatch_eligible_count": sum(1 for row in projects if row["dispatch_eligible"]),
        "human_action_required_count": sum(
            1 for row in projects if row["human_action_required"] is True
        ),
        "projects": projects,
    }


def _short_experiment(experiment: dict[str, Any] | None) -> str:
    if not experiment:
        return "—"
    exp_id = experiment.get("id") or "—"
    stage = experiment.get("stage") or "—"
    status = experiment.get("status") or "—"
    return f"{exp_id} / {stage} / {status}"


def render_markdown(portfolio: dict[str, Any]) -> str:
    lines = [
        "# Portfolio Status",
        "",
        f"Generated: {portfolio['generated_at']}",
        "",
        (
            f"Projects: **{portfolio['project_count']}** · "
            f"Enabled: **{portfolio['enabled_count']}** · "
            f"Dispatch-eligible now: **{portfolio['dispatch_eligible_count']}** · "
            f"Needs human: **{portfolio['human_action_required_count']}**"
        ),
        "",
        "| Project | Lifecycle | Experiment | Worker | Monitor | Human |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for row in portfolio["projects"]:
        worker = "ready" if row["worker_ready"] else "not configured"
        monitor = row["operational_monitor_status"] or "—"
        human = "YES" if row["human_action_required"] else "no"
        if not row["enabled"]:
            worker = "disabled"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["project_id"],
                    str(row["lifecycle_status"]),
                    _short_experiment(row["experiment"]).replace("|", "/"),
                    worker,
                    monitor,
                    human,
                ]
            )
            + " |"
        )

    for row in portfolio["projects"]:
        lines.extend(["", f"## {row['project_id']}", ""])
        lines.append(f"- Repository: {row['repository']}")
        lines.append(f"- Enabled: {str(row['enabled']).lower()}")
        lines.append(f"- Lifecycle: {row['lifecycle_status']}")
        lines.append(f"- Decision hint: {row['decision_hint']}")
        lines.append(f"- Dispatch eligible: {str(row['dispatch_eligible']).lower()}")
        if row["operational_monitor_status"]:
            lines.append(
                f"- Operational monitor: {row['operational_monitor_status']} "
                f"(checked {row['operational_checked_at']})"
            )
        if row["operational_monitor_reason_code"]:
            lines.append(
                "- Infrastructure blocker: "
                f"{row['operational_monitor_status']} — "
                f"{row['operational_monitor_reason_code']}"
            )
        if row["last_result_task_id"]:
            lines.append(f"- Last result: {row['last_result_task_id']}")
        if row["human_action_required"]:
            lines.append(
                f"- Human action required: **YES** — {row['human_action_reason']}"
            )

        blockers = row["current_blockers"]
        if blockers:
            lines.append("- Current blockers:")
            for blocker in blockers:
                lines.append(f"  - {blocker}")

        actions = row["next_permitted_actions"]
        if actions:
            lines.append("- Next permitted actions:")
            for action in actions:
                lines.append(f"  - {action}")

    lines.extend(
        [
            "",
            "## Safety posture",
            "",
            "This page is generated from machine-readable GitHub state. "
            "It does not authorize live trading, spending, methodology changes, "
            "protected-data access, or default-branch merges.",
            "",
        ]
    )
    return "\n".join(lines)


def write_portfolio(root: Path = ROOT) -> dict[str, Any]:
    portfolio = build_portfolio(root)
    observations = root / "observations"
    observations.mkdir(exist_ok=True)
    (observations / "portfolio.json").write_text(
        json.dumps(portfolio, indent=2) + "\n", encoding="utf-8"
    )
    (root / "PORTFOLIO_STATUS.md").write_text(
        render_markdown(portfolio), encoding="utf-8"
    )
    return portfolio


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate central portfolio status.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    portfolio = write_portfolio(args.root.resolve())
    print(json.dumps(portfolio, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
