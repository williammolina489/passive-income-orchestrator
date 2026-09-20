# Passive Income Orchestrator

Central controller for William's automated passive-income research projects.\n\nCurrent machine-generated portfolio view: `PORTFOLIO_STATUS.md`.

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

The OpenAI controller and a deterministic Crypto E001 worker path are now implemented. Autonomous scheduling is not enabled yet.

Required GitHub secret permissions for `ORCHESTRATOR_GITHUB_TOKEN` during this pilot:

- repository access: the orchestrator and managed bot repositories;
- Contents: Read-only;
- Actions: Read and write.

Actions write is needed only to trigger and inspect existing GitHub Actions workflows. The cross-repository token does not need Contents write for this pilot.

## Current portfolio posture

- Crypto Funding Basis: active; E001 Stage 1 is blocked on executable BTCUSD validation. A deterministic read-only worker retries this gate.
- Kalshi Market Maker: active but recovery-blocked; exact prior E001 collector recovery is incomplete and no replacement-source reconstruction is permitted.
- Crypto Trading Bot: active prospective paper research; existing repo-owned incumbent/challenger schedulers remain authoritative, so the orchestrator is monitor-only.
- Alpaca Paper Trading Bot: active paper research; registered monitor-only until current Railway runtime monitoring and a bounded development worker are integrated.
- Systematic Futures: closed after E003 STOP / REJECT.
- Prediction Market Arbitrage: closed after strict-arbitrage payoff-proof failures.

## Current execution milestone

The read-only controller has passed. The first configured execution path is:

```text
Luna scheduler
   -> crypto_funding_basis candidate
   -> existing live-validation.yml on research/e001-prospective-collector
   -> wait for completion
   -> parse LIVE_VALIDATION_RESULT
   -> deterministic PASS/BLOCKED evaluation
   -> write tasks/<task_id>.json
   -> write results/<task_id>.json
   -> refresh state/crypto_funding_basis.json
```

A PASS does not start the collector. It transitions the orchestrator to `NEEDS_HUMAN` so the worker repository's durable research state can be reconciled before any later-stage work.

Kalshi remains non-dispatchable until an exact-recovery-specific worker is implemented.

## Automated scheduling

`Orchestrate Once` runs hourly at minute 17 and may execute at most one bounded worker task per run.

Cost control:

- zero eligible tasks: deterministic WAIT, zero OpenAI tokens;
- exactly one eligible task: deterministic RUN_TASK, zero OpenAI tokens;
- multiple eligible tasks: GPT-5.6 Luna arbitrates among only the verified worker-ready candidates.

The first end-to-end worker cycle passed on 2026-09-20. It dispatched the existing Crypto Funding Basis read-only validation workflow, parsed the production evidence, recorded a structured BLOCKED result, and refreshed central state without changing the worker repository or methodology.

## Next milestone

Add PR-only Codex development workers for projects whose next authorized action requires repository code/research work. Those workers will require explicit cross-repository Contents write permission, will work on branches only, and will not merge to default branches, modify frozen methodology, enable real-money trading, or unseal protected evidence.


## Kalshi exact-recovery local intake

Remote GitHub/email recovery is exhausted for the missing prior E001 collector implementation. The remaining exact source was previously described as local work that had not yet been committed/pushed.

When the original machine is available, do not manually copy/rewrite files first. From a clone of this orchestrator, run:

    kalshi-recovery-intake /path/to/suspected/kalshi-worktree --output kalshi-e001-local-inventory.json

The command is read-only with respect to the suspected worktree. It calculates SHA-256 and Git blob identities, compares every known recovered file, and highlights source/tests that are absent from the current remote recovery set. Presence alone is not treated as proof of provenance.
