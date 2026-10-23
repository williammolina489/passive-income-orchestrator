# Portfolio Status

Generated: 2026-10-23T01:30:52.916069+00:00

Projects: **6** · Enabled: **4** · Dispatch-eligible now: **0** · Needs human: **2**

| Project | Lifecycle | Experiment | Worker | Monitor | Human |
| --- | --- | --- | --- | --- | --- |
| crypto_funding_basis | NEEDS_HUMAN | E002 / Finite feasibility sequence ended without valid checkpoint evidence / STOPPED | not configured | — | YES |
| kalshi_market_maker | NEEDS_HUMAN | E001 / V2 one-time read-only 24h infrastructure verification ARMED; scheduled Oct 14 17:37 EDT but NOT YET RUNNING / PREREGISTERED | not configured | — | YES |
| crypto_trading_bot | ACTIVE | EXP-009 / Prospective BTC paper evidence collection / RUNNING | not configured | WARNING | no |
| alpaca_paper_trading_bot | ACTIVE | E001 / Paper execution validation and historical-fidelity audit / RUNNING | not configured | ERROR | no |
| systematic_futures | CLOSED | E003 / TRAIN / STOPPED | disabled | — | no |
| prediction_market_arbitrage | CLOSED | E003 / Payoff-invariant proof gate / STOPPED | disabled | — | no |

## crypto_funding_basis

- Repository: williammolina489/crypto-funding-basis-bot
- Enabled: true
- Lifecycle: NEEDS_HUMAN
- Decision hint: NEEDS_HUMAN
- Dispatch eligible: false
- Human action required: **YES** — E002 ended INCONCLUSIVE / STOPPED because the scheduled runner missed the frozen Checkpoint A window before any live evidence request. The same-window retry exception has expired. Any new feasibility attempt requires a new explicit human experiment/preregistration decision; E002 itself must not be rescheduled or amended retroactively.
- Current blockers:
  - Checkpoint A was launched by GitHub Actions after the frozen 2026-09-23 10:00–12:00 America/New_York authorization window had already closed, so the validator failed before any production network request.
  - The preregistered technical retry was allowed only inside the same frozen checkpoint window. That window has expired, so no E002 retry remains authorized.
  - Because Checkpoint A never produced valid E002 evidence, Checkpoints B and C correctly did not advance the experiment.

## kalshi_market_maker

- Repository: williammolina489/kalshi-market-maker-research
- Enabled: true
- Lifecycle: NEEDS_HUMAN
- Decision hint: NEEDS_HUMAN
- Dispatch eligible: false
- Last result: kalshi-e001-24h-integrity-smoke
- Human action required: **YES** — One new public GET-only 24-hour Kalshi V2 verification was owner-approved on 2026-10-13 and armed on 2026-10-14 for a prospective 17:25–18:25 EDT launch gate (cron 17:37). GitHub Release assets replace all Actions artifacts, so no 1.5 GiB account artifact-storage check is required. Initial marker-push run 38598167462 correctly skipped collection before the authorized start; main CI passed. No further launch approval is pending. A later human decision remains mandatory for any official 30-day E001 evidence start.
- Current blockers:
  - Original 24h infrastructure smoke retained 10,698 genuine cadence-gap records and is REVIEW_REQUIRED; do not change original evidence or infer 99.5% coverage.
  - New 24h infrastructure verification is authorized and ARMED but not yet started: one dated GitHub schedule on 2026-10-14 at 21:37 UTC must pass 21:25–22:25 UTC fail-closed gate. If the scheduled runner is too late, no data are collected; check the actual future run before claiming start.
  - Any official E001 30-day economic evidence, promotion decision or live trading still needs separate explicit authorization. V2 integrity review must inspect real raw slots, complete replay, not economics.
- Next permitted actions:
  - At/after the scheduled October 14 21:37 UTC run, inspect GitHub Actions for a new SCHEDULE event, successful V2 gate and a draft evidence Release; do not mistake the earlier successful push/skip as active sampling.
  - Allow the single read-only V2 observer to finish its fixed 24h window, preserving Release-backed raw parts, SHA-256 manifests, checkpoint replay and genuine failures; do not reset or rewrite missing samples.
  - After the complete V2 run, evaluate frozen 99.5% orderbook coverage and all immutable integrity checks; keep E001 30-day official period and any trading stopped without further human approval.

## crypto_trading_bot

- Repository: williammolina489/crypto-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: WARNING (checked 2026-10-23T01:30:35.661184+00:00)
- Next permitted actions:
  - Continue the repository's existing autonomous prospective paper collection and health monitoring without duplicating execution, retuning strategies, or advancing maturity gates early.

## alpaca_paper_trading_bot

- Repository: williammolina489/alpaca-paper-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: ERROR (checked 2026-10-23T01:30:35.661184+00:00)
- Current blockers:
  - Historical validation remains incomplete for scan opportunity sampling, point-in-time screener seeds, partial-fill realism, and protective-order/fill fidelity.
- Next permitted actions:
  - Continue paper trading without retuning the strategy from the small sample.
  - Continue the remaining backtest/live fidelity audit under the repository's documented validation rules.

## systematic_futures

- Repository: williammolina489/systematic-futures-bot
- Enabled: false
- Lifecycle: CLOSED
- Decision hint: STOP
- Dispatch eligible: false

## prediction_market_arbitrage

- Repository: williammolina489/prediction-market-arbitrage-scanner
- Enabled: false
- Lifecycle: CLOSED
- Decision hint: STOP
- Dispatch eligible: false

## Safety posture

This page is generated from machine-readable GitHub state. It does not authorize live trading, spending, methodology changes, protected-data access, or default-branch merges.
