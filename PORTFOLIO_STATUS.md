# Portfolio Status

Generated: 2026-10-14T04:53:10.060066+00:00

Projects: **6** · Enabled: **4** · Dispatch-eligible now: **0** · Needs human: **2**

| Project | Lifecycle | Experiment | Worker | Monitor | Human |
| --- | --- | --- | --- | --- | --- |
| crypto_funding_basis | NEEDS_HUMAN | E002 / Finite feasibility sequence ended without valid checkpoint evidence / STOPPED | not configured | — | YES |
| kalshi_market_maker | NEEDS_HUMAN | E001 / V2 read-only 24h infrastructure verification approved conditionally; storage check pending / PREREGISTERED | not configured | — | YES |
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
- Human action required: **YES** — Owner approved exactly one new public-data-only, 24-hour Kalshi integrity verification on 2026-10-13, conditional on verifying storage. New gated workflow merged by PR #8, but no V2 authorization marker exists and no run has launched. Old smoke artifacts still use approximately 576.10 MB, and current GitHub account-wide free artifact capacity is not accessible. Confirm at least 1.5 GiB free storage and zero paid-spend authorization before creating a new prospective narrow launch marker.
- Current blockers:
  - First smoke completed but retained 10,698 cadence-gap records and did not meet its data-integrity gate; original data remain immutable.
  - Original test artifacts occupy approximately 576.10 MB as of 2026-10-13, and owner account's remaining shared Actions artifact storage/spend guard cannot be read via the available GitHub connector; V2 launch requires at least 1.5 GiB confirmed free capacity.
  - V2 workflow is safely staged on main (PR #8 merged), but new marker research/E001_VERIFICATION_V2_AUTHORIZATION.json is absent. No second smoke or 30-day E001 collection is running.
- Next permitted actions:
  - Owner checks GitHub Billing & Licensing for free artifact storage, spending guard, and whether at least 1.5 GiB additional capacity is available; do not enable paid usage.
  - If adequately free verified capacity is reported, precommit a fresh limited post-quote-close ET window, pin collector source SHA, and create the separate V2 authorization marker; fail closed if time, capacity, or safety gates cannot be met.
  - Run exactly one prospective 24h public-data-only infrastructure verification with immutable artifacts and performance-blinded integrity review, only after all launch guards pass. Leave 30-day E001 evidence and real money stopped.

## crypto_trading_bot

- Repository: williammolina489/crypto-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: WARNING (checked 2026-10-14T04:52:54.983290+00:00)
- Next permitted actions:
  - Continue the repository's existing autonomous prospective paper collection and health monitoring without duplicating execution, retuning strategies, or advancing maturity gates early.

## alpaca_paper_trading_bot

- Repository: williammolina489/alpaca-paper-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: HEALTHY (checked 2026-10-14T04:52:54.983290+00:00)
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
