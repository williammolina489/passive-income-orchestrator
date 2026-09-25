# Portfolio Status

Generated: 2026-09-25T22:19:52.551618+00:00

Projects: **6** · Enabled: **4** · Dispatch-eligible now: **0** · Needs human: **1**

| Project | Lifecycle | Experiment | Worker | Monitor | Human |
| --- | --- | --- | --- | --- | --- |
| crypto_funding_basis | NEEDS_HUMAN | E002 / Finite feasibility sequence ended without valid checkpoint evidence / STOPPED | not configured | — | YES |
| kalshi_market_maker | ACTIVE | E001 / Clean collector rebuild / PREREGISTERED | not configured | — | no |
| crypto_trading_bot | ACTIVE | EXP-009 / Prospective BTC paper evidence collection / RUNNING | not configured | INFRASTRUCTURE_BLOCKED | no |
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
- Decision hint: WAIT
- Dispatch eligible: false
- Next permitted actions:
  - Build the clean replacement E001 collector from current main using only the canonical frozen GitHub specification; add deterministic tests, documentation, and CI/smoke tooling; open a PR for human review without merging or starting smoke/E001.

## crypto_trading_bot

- Repository: williammolina489/crypto-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: INFRASTRUCTURE_BLOCKED (checked 2026-09-25T22:19:46.110637+00:00)
- Infrastructure blocker: INFRASTRUCTURE_BLOCKED — GITHUB_ACTIONS_QUOTA
- Next permitted actions:
  - Continue the repository's existing autonomous prospective paper collection and health monitoring without duplicating execution, retuning strategies, or advancing maturity gates early.

## alpaca_paper_trading_bot

- Repository: williammolina489/alpaca-paper-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: HEALTHY (checked 2026-09-25T22:19:46.110637+00:00)
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
