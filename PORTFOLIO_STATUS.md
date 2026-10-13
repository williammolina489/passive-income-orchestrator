# Portfolio Status

Generated: 2026-10-13T11:47:44.620624+00:00

Projects: **6** · Enabled: **4** · Dispatch-eligible now: **0** · Needs human: **2**

| Project | Lifecycle | Experiment | Worker | Monitor | Human |
| --- | --- | --- | --- | --- | --- |
| crypto_funding_basis | NEEDS_HUMAN | E002 / Finite feasibility sequence ended without valid checkpoint evidence / STOPPED | not configured | — | YES |
| kalshi_market_maker | NEEDS_HUMAN | E001 / First 24h non-performance smoke completed; integrity review required / PREREGISTERED | not configured | — | YES |
| crypto_trading_bot | ACTIVE | EXP-009 / Prospective BTC paper evidence collection / RUNNING | not configured | WARNING | no |
| alpaca_paper_trading_bot | ACTIVE | E001 / Paper execution validation and historical-fidelity audit / RUNNING | not configured | HEALTHY | no |
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
- Human action required: **YES** — First 24-hour smoke finished with REVIEW_REQUIRED and 10,698 cadence-gap records. After the code hardening, a new separate non-performance infrastructure verification requires project-owner authorization; E001's 30-day evidence window remains stopped.
- Current blockers:
  - Authorized run 36944108882 completed on 2026-10-03 and its immutable-replay job succeeded, but the final integrity-only artifact reports REVIEW_REQUIRED with 10,698 cadence-gap records. Smoke completion is not integrity PASS.
  - Read-only engineering PRs #5–#7 addressed slow serial public polling, per-stream missing-slot reporting, and 3,873,924 global trade IDs in a 178 MB restart file. These CI-passing changes have not yet passed a separately authorized sustained data-integrity verification run; the original missing observations remain missing.
  - The October 1 authorization was for one smoke only. A fresh integrity-only verification run needs a separate explicit owner decision; the official E001 30-day evidence window remains unstarted and not authorized.
- Next permitted actions:
  - Review the existing first-smoke gaps by stream and timing without inspecting strategy economics or rewriting raw data.
  - After explicit owner authorization of a new separately scoped non-performance verification smoke, preregister its dates, evidence isolation, fail-closed protocol, retention and acceptance checks before launching it.
  - Keep the official E001 evidence window and economic analysis stopped until a verified infrastructure gate and separate explicit owner start decision.

## crypto_trading_bot

- Repository: williammolina489/crypto-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: WARNING (checked 2026-10-13T11:47:24.320309+00:00)
- Next permitted actions:
  - Continue the repository's existing autonomous prospective paper collection and health monitoring without duplicating execution, retuning strategies, or advancing maturity gates early.

## alpaca_paper_trading_bot

- Repository: williammolina489/alpaca-paper-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: HEALTHY (checked 2026-10-13T11:47:24.320309+00:00)
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
