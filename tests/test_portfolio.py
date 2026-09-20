from controller.portfolio import render_markdown


def test_render_markdown_contains_safety_and_human_gate() -> None:
    portfolio = {
        "generated_at": "2026-09-20T15:00:00+00:00",
        "project_count": 1,
        "enabled_count": 1,
        "dispatch_eligible_count": 0,
        "human_action_required_count": 1,
        "projects": [
            {
                "project_id": "kalshi_market_maker",
                "repository": "owner/repo",
                "enabled": True,
                "lifecycle_status": "NEEDS_HUMAN",
                "experiment": {"id": "E001", "stage": "Recovery", "status": "BLOCKED"},
                "worker_ready": False,
                "operational_monitor_status": None,
                "operational_checked_at": None,
                "human_action_required": True,
                "human_action_reason": "Local worktree required.",
                "decision_hint": "NEEDS_HUMAN",
                "dispatch_eligible": False,
                "last_result_task_id": None,
                "current_blockers": ["Missing exact local source."],
                "next_permitted_actions": [],
            }
        ],
    }

    text = render_markdown(portfolio)

    assert "# Portfolio Status" in text
    assert "Local worktree required." in text
    assert "does not authorize live trading" in text
