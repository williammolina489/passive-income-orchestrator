# Passive Income Orchestrator

Central controller for William's automated passive-income research projects.

## Purpose

This repository will coordinate multiple research/bot repositories without relying on ChatGPT conversation history as shared state.

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

This repository is intentionally minimal.

Current files:

- `projects.yaml` — registry of projects the orchestrator may manage.
- `policies/global-policy.md` — global constraints that apply to every project.

No API keys, live-trading credentials, automated workers, or scheduled workflows are configured yet.

## Next milestone

Define a common machine-readable project-state and task/result schema before enabling any autonomous execution.
