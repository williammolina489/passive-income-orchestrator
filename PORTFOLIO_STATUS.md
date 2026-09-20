# Portfolio Status

Generated: 2026-09-20T15:54:06.371656+00:00

Projects: **6** · Enabled: **4** · Dispatch-eligible now: **1** · Needs human: **1**

| Project | Lifecycle | Experiment | Worker | Monitor | Human |
| --- | --- | --- | --- | --- | --- |
| crypto_funding_basis | BLOCKED | E001 / Stage 1 live production validation / BLOCKED | ready | — | no |
| kalshi_market_maker | NEEDS_HUMAN | E001 / Exact prior collector recovery / BLOCKED | not configured | — | YES |
| crypto_trading_bot | ACTIVE | EXP-009 / Prospective BTC paper evidence collection / RUNNING | not configured | WARNING | no |
| alpaca_paper_trading_bot | ACTIVE | E001 / Paper execution validation and historical-fidelity audit / RUNNING | not configured | — | no |
| systematic_futures | CLOSED | E003 / TRAIN / STOPPED | disabled | — | no |
| prediction_market_arbitrage | CLOSED | E003 / Payoff-invariant proof gate / STOPPED | disabled | — | no |

## crypto_funding_basis

- Repository: williammolina489/crypto-funding-basis-bot
- Enabled: true
- Lifecycle: BLOCKED
- Decision hint: RUN_TASK_CANDIDATE
- Dispatch eligible: true
- Last result: crypto_funding_basis:E001:20260920T143628Z
- Current blockers:
  - A valid executable non-empty BTCUSD public production order book has not yet been observed; repeated production snapshots returned ack_id=0 with zero bids and asks despite published 24/7 spot hours.
- Next permitted actions:
  - Repeat read-only public production validation of the frozen BTCUSD/PBTCUC pair and reconcile the BTCUSD closed-book discrepancy without changing the frozen instrument or methodology.

## kalshi_market_maker

- Repository: williammolina489/kalshi-market-maker-research
- Enabled: true
- Lifecycle: NEEDS_HUMAN
- Decision hint: NEEDS_HUMAN
- Dispatch eligible: false
- Human action required: **YES** — Access to the original machine/local worktree or another exact preserved source is required. Remote GitHub/email evidence is insufficient to recover the exact collector implementation without reconstruction.
- Current blockers:
  - All currently known GitHub recovery sources have been exhausted: the preserved 10,000-byte bundle is truncated, the known dangling objects do not contain the complete later collector source/test tree, and recovery workflow/email history exposes no additional exact object identifiers.
  - The prior project handoff states that the substantial collector/smoke implementation existed locally and had not yet been committed/pushed to GitHub. Exact recovery therefore now requires the original local worktree, an exact local archive/chunk, or new exact Git object IDs from another preserved source.

## crypto_trading_bot

- Repository: williammolina489/crypto-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: WARNING (checked 2026-09-20T15:54:04.618156+00:00)
- Next permitted actions:
  - Continue the repository's existing autonomous prospective paper collection and health monitoring without duplicating execution, retuning strategies, or advancing maturity gates early.

## alpaca_paper_trading_bot

- Repository: williammolina489/alpaca-paper-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Current blockers:
  - The GitHub-hosted orchestrator does not yet have an unattended Railway runtime-health credential or public health probe, so Railway health is currently refreshed through the connected Railway integration rather than by the hourly GitHub workflow.
  - Historical validation remains incomplete for scan opportunity sampling, point-in-time screener seeds, partial-fill realism, and protective-order/fill fidelity.
- Next permitted actions:
  - Continue paper trading without retuning the strategy from the small sample.
  - Integrate current Railway runtime health into the orchestrator before autonomous operational decisions.
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
