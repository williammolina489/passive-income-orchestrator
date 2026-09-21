from __future__ import annotations

from controller.execute import _crypto_stage1_result, _parse_live_validation, _update_state_from_result


def _task() -> dict:
    return {
        "task_id": "crypto_funding_basis:E001:20260920T120000Z",
        "project_id": "crypto_funding_basis",
        "repository": "owner/repo",
        "experiment_id": "E001",
        "expected_head_sha": "a" * 40,
    }


def _log_payload(*, ack_id: str, bid: bool, ask: bool) -> list[dict]:
    book = {
        "ack_id": ack_id,
        "timestamp": "2026-09-20T12:00:00+00:00",
        "best_bid_ticks": [100, 1] if bid else None,
        "best_ask_ticks": [101, 1] if ask else None,
        "bid_levels": 1 if bid else 0,
        "ask_levels": 1 if ask else 0,
        "best_bid_price": "100.00" if bid else None,
        "best_ask_price": "101.00" if ask else None,
    }
    payload = {
        "logical_to_live_symbol": {"BTCUSD": "BTCUSD", "PBTCUC": "PBTCUCZ50"},
        "websocket": {"books": {"BTCUSD": book}},
        "authentication_used": False,
        "orders_or_writes_performed": False,
    }
    import json

    return [
        {
            "job_id": 1,
            "name": "validate",
            "conclusion": "success",
            "logs": "prefix\nLIVE_VALIDATION_RESULT=" + json.dumps(payload) + "\n",
        }
    ]


def test_parse_live_validation() -> None:
    payload = _parse_live_validation(_log_payload(ack_id="1", bid=True, ask=True))
    assert payload["logical_to_live_symbol"]["BTCUSD"] == "BTCUSD"


def test_crypto_evaluator_pass_requires_executable_bid_and_ask() -> None:
    result, _ = _crypto_stage1_result(
        task=_task(),
        run={"conclusion": "success", "html_url": "https://github.com/run/1"},
        logs=_log_payload(ack_id="42", bid=True, ask=True),
    )
    assert result["outcome"] == "PASS"
    assert result["human_action_required"] is True


def test_crypto_evaluator_remains_blocked_on_closed_empty_book() -> None:
    result, _ = _crypto_stage1_result(
        task=_task(),
        run={"conclusion": "success", "html_url": "https://github.com/run/2"},
        logs=_log_payload(ack_id="0", bid=False, ask=False),
    )
    assert result["outcome"] == "BLOCKED"
    assert result["human_action_required"] is False


def test_crypto_final_attempt_blocks_and_requires_human() -> None:
    result, _ = _crypto_stage1_result(
        task=_task(),
        run={"conclusion": "success", "html_url": "https://github.com/run/3"},
        logs=_log_payload(ack_id="42", bid=False, ask=False),
        final_attempt=True,
    )
    assert result["outcome"] == "BLOCKED"
    assert result["human_action_required"] is True
    assert "final authorized Checkpoint B" in result["human_action_reason"]


def test_final_blocked_result_stops_automatic_retries() -> None:
    state = {
        "state_revision": 1,
        "lifecycle_status": "BLOCKED",
        "experiment": {"id": "E001", "stage": "Stage 1", "status": "BLOCKED"},
        "source_documents": [],
        "next_permitted_actions": ["Run final Checkpoint B."],
        "human_action_required": False,
        "human_action_reason": None,
        "notes": None,
    }
    result = {
        "task_id": "task-1",
        "outcome": "BLOCKED",
        "summary": "Still no executable BTCUSD quote.",
        "human_action_required": True,
        "human_action_reason": "Finite protocol exhausted.",
    }

    updated = _update_state_from_result(
        state,
        result,
        "https://github.com/run/3",
    )

    assert updated["lifecycle_status"] == "NEEDS_HUMAN"
    assert updated["next_permitted_actions"] == []
    assert updated["human_action_required"] is True
    assert updated["human_action_reason"] == "Finite protocol exhausted."
