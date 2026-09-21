# Portfolio Status

Generated: 2026-09-21T23:16:51.645477+00:00

Projects: **6** · Enabled: **4** · Dispatch-eligible now: **0** · Needs human: **2**

| Project | Lifecycle | Experiment | Worker | Monitor | Human |
| --- | --- | --- | --- | --- | --- |
| crypto_funding_basis | NEEDS_HUMAN | E001 / Stage 1 final classification / BLOCKED | ready | — | YES |
| kalshi_market_maker | NEEDS_HUMAN | E001 / Exact prior collector recovery / BLOCKED | not configured | — | YES |
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
- Last result: crypto_funding_basis:E001:20260921T140833Z
- Human action required: **YES** — E001 Stage 1 is durably classified BLOCKED in the worker repository. A human decision is required to either close E001 at this blocker or explicitly authorize a materially new experiment/preregistration. The existing E001 methodology must not be altered or retried.
- Current blockers:
  - Final Checkpoint B during ordinary Monday daytime again returned BTCUSD with a nonzero acknowledgement ID but zero bid and ask levels while PBTCUCZ50 was executable.
  - The frozen E001 Stage 1 executable BTCUSD requirement did not pass. The finite protocol is complete and no further retries are authorized.

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
- Operational monitor: WARNING (checked 2026-09-21T23:16:46.464378+00:00)
- Next permitted actions:
  - Continue the repository's existing autonomous prospective paper collection and health monitoring without duplicating execution, retuning strategies, or advancing maturity gates early.

## alpaca_paper_trading_bot

- Repository: williammolina489/alpaca-paper-trading-bot
- Enabled: true
- Lifecycle: ACTIVE
- Decision hint: WAIT
- Dispatch eligible: false
- Operational monitor: HEALTHY (checked 2026-09-21T23:16:46.464378+00:00)
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
