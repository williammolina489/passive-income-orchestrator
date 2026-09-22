from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from typing import Any


BASE = "https://external-api.kalshi.com/trade-api/v2"
UA = "passive-income-orchestrator/kalshi-stage0 read-only"


def get(path: str, params: dict[str, object] | None = None) -> dict[str, Any]:
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
    url = BASE + path + (("?" + query) if query else "")
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            return {
                "url": url,
                "status": int(response.status),
                "headers": {
                    k.lower(): v
                    for k, v in response.headers.items()
                    if k.lower().startswith("ratelimit")
                    or k.lower().startswith("x-ratelimit")
                },
                "payload": json.loads(body),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        payload: Any
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body[:1000]}
        return {
            "url": url,
            "status": int(exc.code),
            "headers": {
                k.lower(): v
                for k, v in exc.headers.items()
                if k.lower().startswith("ratelimit")
                or k.lower().startswith("x-ratelimit")
            },
            "payload": payload,
        }


def keys(value: Any) -> list[str]:
    return sorted(value) if isinstance(value, dict) else []


def main() -> int:
    findings: dict[str, Any] = {
        "mode": "READ_ONLY_UNAUTHENTICATED_STAGE0",
        "authorization_headers_sent": False,
        "write_requests_sent": False,
        "base_url": BASE,
    }

    series = get("/series/KXHIGHNY")
    markets = get("/markets", {"series_ticker": "KXHIGHNY", "status": "open", "limit": 1000})
    exchange = get("/exchange/status")
    incentives = get("/incentive_programs", {"status": "active", "limit": 1000})
    fee_changes = get("/series/fee_changes", {"series_ticker": "KXHIGHNY"})

    findings["series_status"] = series["status"]
    findings["markets_status"] = markets["status"]
    findings["exchange_status_status"] = exchange["status"]
    findings["incentives_status"] = incentives["status"]
    findings["series_fee_changes_status"] = fee_changes["status"]

    series_obj = series["payload"].get("series", {}) if isinstance(series["payload"], dict) else {}
    market_rows = markets["payload"].get("markets", []) if isinstance(markets["payload"], dict) else []
    findings["series"] = {
        "keys": keys(series_obj),
        "ticker": series_obj.get("ticker"),
        "fee_type": series_obj.get("fee_type"),
        "fee_multiplier": series_obj.get("fee_multiplier"),
        "settlement_sources_present": bool(series_obj.get("settlement_sources")),
        "contract_url_present": bool(series_obj.get("contract_url")),
        "contract_terms_url_present": bool(series_obj.get("contract_terms_url")),
    }
    findings["open_market_count"] = len(market_rows)

    if not market_rows:
        print("KALSHI_STAGE0_RESULT=" + json.dumps(findings, sort_keys=True))
        print("KALSHI_STAGE0_BLOCKED=no_open_kxhighny_markets", file=sys.stderr)
        return 2

    def volume(row: dict[str, Any]) -> Decimal:
        try:
            return Decimal(str(row.get("volume_fp", "0")))
        except Exception:
            return Decimal(0)

    sample = max(market_rows, key=volume)
    ticker = str(sample["ticker"])
    event_ticker = str(sample["event_ticker"])

    market = get(f"/markets/{ticker}")
    event = get(f"/events/{event_ticker}", {"with_nested_markets": "true"})
    orderbook = get(f"/markets/{ticker}/orderbook", {"depth": 0})
    trades = get("/markets/trades", {"ticker": ticker, "limit": 100})
    announcements = get("/exchange/announcements")
    schedule = get("/exchange/schedule")

    findings["sample_ticker"] = ticker
    findings["sample_event_ticker"] = event_ticker
    findings["market_status"] = market["status"]
    findings["event_status"] = event["status"]
    findings["orderbook_status"] = orderbook["status"]
    findings["trades_status"] = trades["status"]
    findings["announcements_status"] = announcements["status"]
    findings["schedule_status"] = schedule["status"]
    findings["rate_limit_headers"] = {
        "series": series["headers"],
        "markets": markets["headers"],
        "orderbook": orderbook["headers"],
        "trades": trades["headers"],
    }

    market_obj = market["payload"].get("market", {}) if isinstance(market["payload"], dict) else {}
    event_obj = event["payload"].get("event", {}) if isinstance(event["payload"], dict) else {}
    ob = orderbook["payload"].get("orderbook_fp", {}) if isinstance(orderbook["payload"], dict) else {}
    trade_rows = trades["payload"].get("trades", []) if isinstance(trades["payload"], dict) else []

    findings["market_contract"] = {
        "keys": keys(market_obj),
        "status": market_obj.get("status"),
        "close_time": market_obj.get("close_time"),
        "expiration_time": market_obj.get("expiration_time"),
        "price_ranges": market_obj.get("price_ranges"),
        "fractional_trading_enabled": market_obj.get("fractional_trading_enabled"),
        "rules_primary_present": bool(market_obj.get("rules_primary")),
        "rules_secondary_present": bool(market_obj.get("rules_secondary")),
        "fee_waiver_expiration_time": market_obj.get("fee_waiver_expiration_time"),
    }
    findings["event_contract"] = {
        "keys": keys(event_obj),
        "nested_market_count": len(event_obj.get("markets", []) or []),
        "fee_type_override": event_obj.get("fee_type_override"),
        "fee_multiplier_override": event_obj.get("fee_multiplier_override"),
    }
    findings["orderbook_contract"] = {
        "keys": keys(ob),
        "yes_levels": len(ob.get("yes_dollars", []) or []),
        "no_levels": len(ob.get("no_dollars", []) or []),
        "sample_yes_level": (ob.get("yes_dollars", []) or [None])[-1],
        "sample_no_level": (ob.get("no_dollars", []) or [None])[-1],
    }
    findings["trade_contract"] = {
        "cursor_present": isinstance(trades["payload"], dict) and "cursor" in trades["payload"],
        "trade_count": len(trade_rows),
        "trade_keys": keys(trade_rows[0]) if trade_rows else [],
        "sample_trade": trade_rows[0] if trade_rows else None,
    }
    findings["incentive_contract"] = {
        "top_level_keys": keys(incentives["payload"]),
        "program_count": len(incentives["payload"].get("incentive_programs", []) or [])
        if isinstance(incentives["payload"], dict)
        else None,
        "sample_program_keys": keys((incentives["payload"].get("incentive_programs", []) or [{}])[0])
        if isinstance(incentives["payload"], dict)
        else [],
    }
    findings["fee_change_contract"] = {
        "top_level_keys": keys(fee_changes["payload"]),
    }

    essential = {
        "series": series["status"],
        "markets": markets["status"],
        "market": market["status"],
        "event": event["status"],
        "orderbook": orderbook["status"],
        "trades": trades["status"],
        "exchange_status": exchange["status"],
        "incentives": incentives["status"],
    }
    auth_required = [name for name, status in essential.items() if status in {401, 403}]
    non_200 = {name: status for name, status in essential.items() if status != 200}

    findings["essential_statuses"] = essential
    findings["authentication_required_for"] = auth_required
    findings["essential_non_200"] = non_200
    findings["stage0_pass"] = not auth_required and not non_200

    print("KALSHI_STAGE0_RESULT=" + json.dumps(findings, sort_keys=True))
    if auth_required:
        print(
            "KALSHI_STAGE0_BLOCKED=CURRENT_DATA_CONTRACT_REQUIRES_AUTHENTICATION:"
            + ",".join(auth_required),
            file=sys.stderr,
        )
        return 3
    if non_200:
        print("KALSHI_STAGE0_BLOCKED=ESSENTIAL_ENDPOINT_FAILURE", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
