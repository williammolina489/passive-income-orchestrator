# Consolidation audit — 2026-11-13

## Evidence preserved before shutdown

- Crypto: 1,182 original Actions ZIPs, 118,563,476 bytes; no expired artifacts at capture. Permanent release: https://github.com/williammolina489/crypto-trading-bot/releases/tag/evidence-preservation-43402383745
- Orchestrator: 258 original Actions ZIPs, 194,377 bytes; no expired artifacts at capture. Permanent release: https://github.com/williammolina489/passive-income-orchestrator/releases/tag/evidence-preservation-43402388485
- Both complete release archives were downloaded independently, SHA-256 checked, and every ZIP compared with its manifest and CRC checked. Alpaca has zero current Actions artifacts. No original artifact or historical record was deleted.
- Final BTC checkpoint state, ledgers, balances, returns, fees and benchmarks are additionally preserved in crypto PR #14. Selection observations from November 12 are unchanged.

## Execution and cost changes

Old BTC cycle schedules (48 nominal daily triggers) are removed, together with their health/smoke/recovery paths. One unnecessary daily historical dashboard publication is removed; it had accumulated pending Railway deployments. The currently serving authenticated read-only dashboard remains intact. Orchestration drops from hourly to every four hours (24 to 6 nominal daily triggers); tests remain in CI rather than being repeated inside every scheduled controller run. New EXP-010 collects at most six scheduled observations daily and stores evidence in a durable Git branch rather than repeated cumulative Actions artifacts.

These changes reduce this portfolio's configured scheduled trigger count from 73/day to 12/day once EXP-010 is active: 61 fewer nominal triggers/day. This is a schedule comparison, not measured paid minutes or dollar savings. GitHub cron may delay or omit triggers.

Actual GitHub billing is unavailable to this integration: both current usage and legacy Actions billing endpoints returned HTTP 403, Resource not accessible by integration. Railway MCP supplies metrics but no invoice/billing operation; no authenticated billing UI/CLI is available. Unknown charges are not zero. No verified dollar reduction can be claimed. Release storage and retained Git history are preserved; 119 MB of existing Actions artifacts may expire normally because durable copies now exist.

## Railway audit

See `railway-audit.json` for configuration, deployment IDs and seven-day metrics for each of six services. All six have zero sampled CPU/memory usage, no mounted volumes, no domains and no cron. Five completed finite jobs have zero running replicas and restart NEVER. Their train/validation/coverage conclusions remain in `alpaca-paper-trading-bot@research/momentum-12-1-baseline:experiments/momentum_12_1/` (E011 canonical momentum selection failed its matched-control test; OOS remains sealed).

The five deployed research services are retained: runtime logs are no longer returned and original /tmp output files cannot be independently verified/exported from stopped containers. Deleting their deployment history would remove potentially required evidence. Their paid charges remain unverified; observed compute is zero, not proof of a zero invoice.

The empty service `momentum-12-1-e011-validation-audit` (010c73f2-80bc-4145-aeaa-15538f986c73) is the only verified removal candidate: never deployed, no source, no runtime, no volume, no domain, no TCP endpoint, no cron and no output files. It cannot serve a runtime dependency. Its metadata is preserved in this PR before removal. No paid compute saving is attributed to removing it.

Required services are preserved. Alpaca's /health reports process/database OK and paper=true, but entries_disabled=true, reconciliation_status=halted and flatten_status=not_flat. Leave the safety halt intact; resolving it is a separate trading-risk decision. The dashboard /health reports paper_only=true, live_trading_enabled=false and data_available=true; serving snapshot is dated October 25 while newer deployments await approval. No pending deployment is approved by this consolidation.

## Closed stays closed

Original BTC and EXP-009 are operationally closed; mean reversion can run only in separate EXP-010. Funding-basis remains CLOSED with E002 scientifically INCONCLUSIVE/STOPPED. Systematic futures and prediction-market arbitrage remain closed. No Kalshi economic evidence, new smoke, or trading is authorized by this work. Historical registry/state snapshots remain alongside this report.
