# Portfolio Status

Generated: 2026-09-23T05:58:35.896100+00:00

Projects: **6** · Enabled: **4** · Dispatch-eligible now: **0** · Needs human: **0**

| Project | Lifecycle | Experiment | Worker | Monitor | Human |
| --- | --- | --- | --- | --- | --- |
| crypto_funding_basis | ACTIVE | E002 / Checkpoint A pending / RUNNING | not configured | — | no |
| kalshi_market_maker | ACTIVE | E001 / Clean collector rebuild / PREREGISTERED | not configured | — | no |
| crypto_trading_bot | ACTIVE | EXP-009 / Prospective BTC paper evidence collection / RUNNING | not configured | WARNING | no |
| alpaca_paper_trading_bot | ACTIVE | E001 / Paper execution validation and historical-fidelity audit / RUNNING | not configured | HEALTHY | no |
| systematic_futures | CLOSED | E003 / TRAIN / STOPPED | disabled | — | no |
| prediction_market_arbitrage | CLOSED | E003 / Payoff-invariant proof gate / STOPPED | disabled | — | no |

## crypto_funding_basis

- Repository: williammolina489/crypto-funding-basis-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Next permitted actions:
  - Execute only authorized E002 checkpoint A during 2026-09-23 10:00–12:00 America/New_York using the frozen XBTUSD/PBTCUC public read-only feasibility validator.

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
- Operational monitor: WARNING (checked 2026-09-23T05:58:31.719701+00:00)
- Next permitted actions:
  - Continue the repository's existing autonomous prospective paper collection and health monitoring without duplicating execution, retuning strategies, or advancing maturity gates early.

## alpaca_paper_trading_bot

- Repository: williammolina489/alpaca-paper-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: HEALTHY (checked 2026-09-23T05:58:31.719701+00:00)
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
