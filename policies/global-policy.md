# Global Orchestrator Policy

These rules apply to the master controller and every worker it dispatches.

## 1. Source of truth

GitHub is the source of truth.

Before taking action, an agent must inspect the current repository state relevant to the task. Current repository evidence overrides remembered chat context or stale summaries.

## 2. Preserve research integrity

Agents must preserve all existing experiment controls, including:

- preregistered methodology;
- frozen parameters;
- acceptance and rejection criteria;
- TRAIN / VALIDATION / OOS boundaries;
- data-integrity requirements;
- stage gates;
- stop conditions;
- documented project decisions.

An agent must never alter a rule merely because an experiment is blocked, failing, or unprofitable.

## 3. Allowed autonomous work

Subject to project-specific policy, agents may autonomously:

- inspect repository state and history;
- inspect open pull requests and CI;
- run existing tests and validation commands;
- diagnose implementation defects;
- make bounded implementation fixes required by an approved task;
- collect permitted public or production evidence;
- update research/status documentation;
- create branches and commits;
- open pull requests;
- report PASS, FAIL, BLOCKED, STOP, or NEEDS_HUMAN;
- continue to the next already-authorized stage only when the repository's gate explicitly permits it.

## 4. Human approval required

Agents must stop and return NEEDS_HUMAN before:

- spending money or purchasing data/services;
- placing a live trade or deploying capital;
- enabling or changing live-trading credentials;
- changing preregistered methodology;
- weakening acceptance criteria or evidence standards;
- unsealing protected VALIDATION or OOS data unless the existing project rules explicitly authorize that transition;
- merging consequential changes directly to a protected/default branch;
- starting a new strategy family or materially different research program;
- reviving a project marked closed, stopped, or rejected when no existing rule authorizes continuation;
- taking an irreversible action not already authorized by repository policy.

## 5. No self-expansion of scope

Workers must perform only the dispatched task and the minimum supporting work necessary to complete it.

If the requested task is impossible under the current constraints, return BLOCKED or NEEDS_HUMAN. Do not invent a replacement methodology or broaden the research question.

## 6. No hidden performance leakage

If a repository marks performance, validation, or OOS evidence as sealed, agents must not inspect, summarize, derive, expose, or use that evidence before the documented gate permits access.

## 7. Result discipline

Every worker result must eventually be machine-readable and include at least:

- project;
- task identifier;
- starting commit;
- resulting commit or PR, if any;
- outcome;
- evidence summary;
- tests/checks performed;
- whether methodology changed;
- whether protected data was accessed;
- whether human action is required;
- recommended next permitted action.

## 8. Fail closed

If repository state is contradictory, incomplete, or ambiguous in a way that could affect research integrity or financial risk, the agent must not guess.

Return BLOCKED or NEEDS_HUMAN with the exact ambiguity.

## 9. Financial safety

The orchestrator is a research and automation system, not an unrestricted autonomous money manager.

Live-capital deployment, purchases, withdrawals, transfers, and other consequential financial actions remain human-gated unless a later explicit policy narrowly authorizes a specific operation with appropriate technical safeguards.
