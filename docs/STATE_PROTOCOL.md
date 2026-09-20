# State Protocol

This document defines how the master orchestrator and managed project repositories communicate.

## Managed repository paths

Each enabled project repository should expose:

```text
.orchestrator/
  PROJECT_STATE.json
  inbox/
  results/
```

### PROJECT_STATE.json

`.orchestrator/PROJECT_STATE.json` is the worker repository's machine-readable current state.

It must validate against:

```text
passive-income-orchestrator/schemas/project-state.schema.json
```

The repository's normal research documents remain authoritative evidence. The state file is a compact index of that evidence, not a replacement for it.

If the state file conflicts with current repository evidence, the controller must fail closed and return BLOCKED or NEEDS_HUMAN.

## Task delivery

The master controller creates one bounded task conforming to:

```text
schemas/task.schema.json
```

The canonical task identifier must be unique.

During the first implementation, tasks may be delivered through GitHub `repository_dispatch`. A worker may also persist the received task under:

```text
.orchestrator/inbox/<task_id>.json
```

for auditability.

Workers must verify that `expected_head_sha` still matches the intended starting state before doing consequential work. A stale task must stop rather than silently executing against a changed repository.

## Worker results

Every attempted task must produce a result conforming to:

```text
schemas/result.schema.json
```

When persisted in the worker repository, use:

```text
.orchestrator/results/<task_id>.json
```

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

- `PROJECT_STATE.json` is missing or invalid;
- the recorded head SHA is stale and the state has not been refreshed;
- repository evidence contradicts the state file;
- required protected-data permissions are absent;
- the requested action violates global or project-specific policy;
- the project is disabled in `projects.yaml`;
- the next action is materially ambiguous.

## Versioning

All current contracts use:

```json
"schema_version": "1.0"
```

Breaking changes require a new schema version. Version 1 deliberately cannot authorize live financial actions, spending, methodology changes, or direct default-branch merges.
