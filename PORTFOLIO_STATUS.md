# Portfolio Status

Generated: 2026-10-01T23:12:34.635775+00:00

Projects: **6** · Enabled: **4** · Dispatch-eligible now: **0** · Needs human: **2**

| Project | Lifecycle | Experiment | Worker | Monitor | Human |
| --- | --- | --- | --- | --- | --- |
| crypto_funding_basis | NEEDS_HUMAN | E002 / Finite feasibility sequence ended without valid checkpoint evidence / STOPPED | not configured | — | YES |
| kalshi_market_maker | ACTIVE | E001 / Clean collector rebuild PR ready / human review / PREREGISTERED | not configured | — | YES |
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
- Lifecycle: ACTIVE
- Decision hint: NEEDS_HUMAN
- Dispatch eligible: false
- Last result: kalshi-e001-clean-rebuild
- Human action required: **YES** — Kalshi rebuild PR #1 is green and ready for human review. Automatic merge and smoke start are prohibited.
- Current blockers:
  - Rebuild PR #1 is open at head 3a5cc4404d8eb199772ad156f38cf82fe7469f62 and awaits human review. Branch-head CI run 36935054968 passed ruff and 58/58 pytest tests.
  - The frozen E001 preregistration remains byte-identical to main. The 24-hour non-performance smoke and official 30-day E001 evidence window have not started.
- Next permitted actions:
  - Human-review Kalshi rebuild PR #1 against the frozen E001 specification. Do not merge it automatically.
  - If the rebuild is explicitly approved and merged, make a separate explicit decision before starting the non-performance 24-hour integrity smoke.
  - Keep the official 30-day E001 evidence window stopped until the smoke passes its integrity review and a later explicit start decision is made.

## crypto_trading_bot

- Repository: williammolina489/crypto-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: WARNING (checked 2026-10-01T23:12:20.501999+00:00)
- Next permitted actions:
  - Continue the repository's existing autonomous prospective paper collection and health monitoring without duplicating execution, retuning strategies, or advancing maturity gates early.

## alpaca_paper_trading_bot

- Repository: williammolina489/alpaca-paper-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: HEALTHY (checked 2026-10-01T23:12:20.501999+00:00)
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
