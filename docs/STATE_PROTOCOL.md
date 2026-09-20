# State Protocol

This document defines how the master orchestrator and managed project repositories communicate.

## Canonical orchestrator paths

Canonical machine-readable coordination state lives in this repository:

```text
state/
  <project_id>.json

tasks/
  <task_id>.json

results/
  <task_id>.json
```

Keeping canonical state outside the worker repository avoids a self-reference problem where a state file would need to contain the SHA of the same commit that contains the state file.

## Project state

Each entry in `projects.yaml` points to a canonical state file, for example:

```text
state/crypto_funding_basis.json
```

Each state file must validate against:

```text
schemas/project-state.schema.json
```

The state file records the exact worker repository branch and commit SHA that it describes.

The worker repository's normal research documents remain the authoritative evidence. The orchestrator state is a compact, machine-readable index of that evidence, not a replacement for it.

If repository evidence conflicts with the orchestrator state, the controller must fail closed and return `BLOCKED` or `NEEDS_HUMAN`.

Before dispatching work, the controller must verify that the recorded worker branch still points to the recorded `head_sha`. If it has moved, the state must be refreshed before execution.

## Task delivery

The master controller creates one bounded task conforming to:

```text
schemas/task.schema.json
```

The canonical copy is stored at:

```text
tasks/<task_id>.json
```

The task may then be delivered to the worker repository through GitHub `repository_dispatch`.

Workers must verify that `expected_head_sha` still matches the intended starting branch before doing work. A stale task must stop rather than silently executing against changed code or research state.

## Worker results

Every attempted task must produce a result conforming to:

```text
schemas/result.schema.json
```

The canonical result is stored at:

```text
results/<task_id>.json
```

Worker branches, commits, pull requests, workflow artifacts, and logs remain in the worker repository and are referenced by the result.

The result must truthfully report:

- starting and ending commit;
- outcome;
- evidence references;
- checks/tests performed;
- whether methodology changed;
- whether protected data was accessed;
- whether any financial action occurred;
- whether human action is required;
- the next permitted action, if one is known.

## Controller decision vocabulary

The controller's high-level decisions are:

- `RUN_TASK` — one bounded autonomous task is permitted.
- `WAIT` — nothing should execute yet.
- `BLOCKED` — a technical/evidence prerequisite is unmet.
- `STOP` — repository rules say the project/experiment should not continue.
- `NEEDS_HUMAN` — a human-gated or ambiguous decision is required.

## Fail-closed rules

The controller must not dispatch autonomous work when:

- the project's canonical state file is missing or invalid;
- the project is disabled in `projects.yaml`;
- the recorded worker branch no longer matches the recorded head SHA;
- repository evidence contradicts the state file;
- required protected-data permissions are absent;
- the requested action violates global or project-specific policy;
- the next action is materially ambiguous.

## Versioning

All current contracts use:

```json
"schema_version": "1.0"
```

Breaking changes require a new schema version. Version 1 deliberately cannot authorize live financial actions, spending, methodology changes, or direct default-branch merges.
