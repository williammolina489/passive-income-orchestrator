from controller.human_gate import build_issue_body, gate_fingerprint, gate_marker


def _state(reason: str = "Local worktree required.") -> dict:
    return {
        "project_id": "kalshi_market_maker",
        "repository": "owner/repo",
        "lifecycle_status": "NEEDS_HUMAN",
        "experiment": {"id": "E001", "stage": "Recovery", "status": "BLOCKED"},
        "human_action_required": True,
        "human_action_reason": reason,
        "current_blockers": ["Exact source is unavailable remotely."],
    }


def test_gate_fingerprint_is_stable_for_same_gate() -> None:
    assert gate_fingerprint(_state()) == gate_fingerprint(_state())


def test_gate_fingerprint_changes_when_reason_changes() -> None:
    assert gate_fingerprint(_state("A")) != gate_fingerprint(_state("B"))


def test_issue_body_contains_machine_marker_and_safety_boundary() -> None:
    state = _state()
    fingerprint = gate_fingerprint(state)
    body = build_issue_body(state, "state/kalshi_market_maker.json")

    assert gate_marker("kalshi_market_maker", fingerprint) in body
    assert "Local worktree required." in body
    assert "No live trading" in body
