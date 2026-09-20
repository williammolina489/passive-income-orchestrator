# Passive Income Orchestrator

Central controller for William's automated passive-income research projects.

## Purpose

This repository coordinates multiple research/bot repositories without relying on ChatGPT conversation history as shared state.

GitHub is the source of truth.

The orchestrator will eventually:

1. Read each managed project's current repository state.
2. Determine whether an unambiguous next action is permitted.
3. Dispatch approved work to that project's worker.
4. Receive structured results back through GitHub.
5. Continue, wait, stop, or request human approval according to policy.

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
        +--> read project state
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
Master controller evaluates result
```

## Current bootstrap stage

The shared communication contract is now defined.

Current foundation:

- `projects.yaml` — registry of projects the orchestrator may manage.
- `policies/global-policy.md` — global constraints that apply to every project.
- `schemas/project-state.schema.json` — current-state contract.
- `schemas/task.schema.json` — bounded worker-task contract.
- `schemas/result.schema.json` — worker-result contract.
- `docs/STATE_PROTOCOL.md` — where managed repositories publish state/tasks/results.

Version 1 of the task contract cannot authorize spending, purchasing data/services, live trades, transfers/withdrawals, methodology changes, or direct merges to the default branch.

No API keys, live-trading credentials, autonomous workers, or scheduled workflows are configured yet.

## Next milestone

Seed each enabled managed repository with a truthful `.orchestrator/PROJECT_STATE.json` based on its current GitHub state, then build a read-only controller that validates those states before any autonomous dispatching is enabled.
