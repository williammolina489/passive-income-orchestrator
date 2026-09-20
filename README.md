# Passive Income Orchestrator

Central controller for William's automated passive-income research projects.

## Purpose

This repository coordinates multiple research/bot repositories without relying on ChatGPT conversation history as shared state.

GitHub is the source of truth.

The orchestrator will eventually:

1. Read each managed project's current repository state.
2. Verify that the state still matches the exact worker branch/SHA.
3. Determine whether an unambiguous next action is permitted.
4. Dispatch approved work to that project's worker.
5. Receive structured results back through GitHub.
6. Continue, wait, stop, or request human approval according to policy.

## Design principles

- Repository state beats chat memory.
- Existing experiment preregistrations and frozen methodology must be preserved.
- Workers should do only the task explicitly dispatched to them.
- Routine inspection, testing, evidence collection, documentation, and PR creation may be automated.
- Sensitive or consequential actions remain human-gated.
- Closed or rejected projects must not be silently revived.
- No agent may weaken an experiment's acceptance criteria to make it pass.
- Machine-readable contracts fail closed when state is ambiguous.

## Planned architecture

```text
GitHub Actions scheduler
        |
        v
Master controller
        |
        +--> validate central state
        +--> verify worker branch/SHA
        +--> choose WAIT / RUN_TASK / BLOCKED / STOP / NEEDS_HUMAN
        |
        v
repository_dispatch
        |
        v
Project worker
        |
        +--> inspect repo
        +--> perform permitted task
        +--> run tests / collect evidence
        +--> create branch / PR / structured result
        |
        v
Master controller records result + refreshes state
```

## Current bootstrap stage

The shared communication contract and initial portfolio registry are defined.

Current foundation:

- `projects.yaml` — project registry and active/closed dispatch status.
- `policies/global-policy.md` — global constraints that apply to every project.
- `schemas/project-state.schema.json` — current-state contract.
- `schemas/task.schema.json` — bounded worker-task contract.
- `schemas/result.schema.json` — worker-result contract.
- `docs/STATE_PROTOCOL.md` — state/task/result communication protocol.
- `state/*.json` — canonical snapshots of the exact worker branches/SHA they describe.

Version 1 of the task contract cannot authorize spending, purchasing data/services, live trades, transfers/withdrawals, methodology changes, or direct merges to the default branch.

No API keys, live-trading credentials, autonomous workers, or scheduled workflows are configured yet.

## Current portfolio posture

- Crypto Funding Basis: active, E001 Stage 1 blocked on executable BTCUSD validation.
- Kalshi Market Maker: active, exact prior E001 collector recovery is incomplete.
- Systematic Futures: closed after E003 STOP / REJECT.
- Prediction Market Arbitrage: closed after strict-arbitrage payoff-proof failures.

## Next milestone

Build a read-only controller that validates the registry and state files, checks the referenced GitHub branch SHAs for staleness, and emits a deterministic portfolio status report. No task dispatching will be enabled until that read-only layer passes.
