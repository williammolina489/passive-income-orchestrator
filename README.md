# Passive Income Orchestrator

Central controller for William's automated passive-income research projects.

Current machine-generated portfolio view: `PORTFOLIO_STATUS.md`.

## Purpose

This repository coordinates multiple research/bot repositories without relying on ChatGPT conversation history as shared state.

GitHub is the source of truth.

The orchestrator can:

1. read each managed project's canonical state;
2. verify the exact worker branch/SHA before action;
3. monitor configured operational health signals;
4. choose a bounded next action only from already-permitted project actions;
5. dispatch configured workers;
6. record structured task/result evidence;
7. refresh a central portfolio status page;
8. stop at human gates and create a deduplicated GitHub issue.

## Design principles

- Repository state beats chat memory.
- Existing experiment preregistrations and frozen methodology are preserved.
- Workers perform only explicitly authorized bounded tasks.
- Routine inspection, testing, evidence collection, monitoring, and PR creation may be automated.
- Sensitive or consequential actions remain human-gated.
- Closed or rejected projects are not silently revived.
- No agent may weaken acceptance criteria to make an experiment pass.
- Ambiguity fails closed.

## Current architecture

```text
GitHub Actions scheduler
        |
        v
Verify canonical project states + exact SHAs
        |
        +--> refresh read-only operational monitors
        |
        v
Bounded scheduler
        |
        +--> 0 candidates: deterministic WAIT
        +--> 1 candidate: deterministic RUN_TASK
        +--> 2+ candidates: GPT-5.6 Luna arbitrates only among verified candidates
        |
        v
Configured worker
        |
        +--> execute permitted read-only/research task
        +--> collect structured evidence
        +--> write task/result/state
        |
        v
Refresh PORTFOLIO_STATUS.md
        |
        v
Deduplicated NEEDS_HUMAN issue when required
```

## Core contracts

- `projects.yaml` — project registry, worker/monitor configuration, active/closed status.
- `policies/global-policy.md` — global research and financial safety constraints.
- `schemas/project-state.schema.json` — canonical project-state contract.
- `schemas/task.schema.json` — bounded deterministic worker task.
- `schemas/result.schema.json` — structured worker result.
- `schemas/controller-decision.schema.json` — scheduler decision.
- `schemas/codex-job.schema.json` — PR-only Codex editing job.
- `docs/STATE_PROTOCOL.md` — state/task/result protocol.
- `state/*.json` — canonical project snapshots.
- `observations/*.json` — read-only operational observations.
- `PORTFOLIO_STATUS.md` — generated central dashboard.

Version 1 structurally cannot authorize spending, data/service purchases, live trades, transfers/withdrawals, methodology changes, protected VALIDATION/OOS access, or direct default-branch merges.

## Automated scheduling

`Orchestrate Once` runs hourly at minute 17 and may execute at most one bounded worker task per run.

Before execution it:

- installs the pinned project package;
- runs the orchestrator test suite;
- verifies every canonical worker branch SHA;
- refreshes operational observations.

After execution it:

- records the task/result/state;
- regenerates `PORTFOLIO_STATUS.md`;
- commits central evidence;
- syncs deduplicated human-gate issues.

Cost behavior:

- zero eligible tasks: zero OpenAI tokens;
- exactly one eligible task: zero OpenAI tokens;
- multiple eligible tasks: GPT-5.6 Luna is called only to choose among the verified worker-ready candidates.

A separate manual `Refresh Portfolio Status` workflow updates observations and the dashboard without dispatching a worker or using OpenAI.

## Current portfolio

### Crypto Funding Basis

Active E001 Stage 1 validation. The only autonomous worker currently enabled is the existing read-only Bitnomial live-validation workflow on `research/e001-prospective-collector`.

The first end-to-end orchestrated worker cycle passed operationally on 2026-09-20. BTCUSD still returned a closed/empty executable book, so Stage 1 remains BLOCKED. A future PASS transitions to `NEEDS_HUMAN`; it does not automatically build/start the collector or any later stage.

### Kalshi Market Maker

`NEEDS_HUMAN`.

Remote exact-recovery sources are exhausted. The preserved bundle is truncated, known dangling objects do not contain the complete later collector/test tree, and no additional backup/object ID was found in available email/history.

The remaining exact implementation was previously described as local uncommitted/unpushed work. Do not reconstruct it.

Human-gate issue: #1 in this repository.

A read-only local forensic intake tool is ready:

```bash
kalshi-recovery-intake /path/to/suspected/kalshi-worktree \
  --output kalshi-e001-local-inventory.json
```

See `docs/KALSHI_LOCAL_RECOVERY.md`.

### Crypto Trading Bot

Active prospective paper research.

The repository's own incumbent/challenger workflows remain authoritative for paper execution; the orchestrator does not duplicate them. The central monitor checks:

- Forward paper BTC cycle;
- Forward challenger BTC basket;
- Forward paper health watch;
- Forward challenger health watch.

The latest central observation currently flags an incumbent-side freshness warning while the challenger side is healthy. The orchestrator observes this but does not override the repo's guarded recovery logic.

### Alpaca Paper Trading Bot

Active paper research.

The orchestrator now performs unattended read-only runtime monitoring through the service's sanitized public `/health` endpoint. The monitor requires:

- paper mode;
- process OK;
- database OK;
- entries enabled;
- reconciliation OK;
- fresh heartbeat.

Current runtime health is HEALTHY.

Historical strategy validation remains incomplete, so runtime health is not treated as proof of edge or authorization for live money.

### Systematic Futures

Closed after E003 STOP / REJECT. Disabled in the orchestrator. VALIDATION/OOS protections remain intact.

### Prediction Market Arbitrage

Closed after the strict-arbitrage payoff-proof failures. Disabled in the orchestrator. No E004 or strategy-family conversion is authorized.

## GitHub credentials

Current read/dispatch secret:

`ORCHESTRATOR_GITHUB_TOKEN`

Pilot permissions:

- repository access only to the managed repos;
- Contents: Read-only;
- Actions: Read and write.

This token is sufficient for state verification and existing workflow dispatch. It is intentionally insufficient for editing bot repositories.

## PR-only Codex worker

The PR-only Codex framework is implemented and tested but **disabled**.

See `docs/CODEX_PR_WORKER.md`.

It uses OpenAI's official `openai/codex-action@v1` with the `:workspace` permission profile and `drop-sudo` safety strategy.

Important safeguards:

- target checkout is pinned to the authorized SHA;
- checkout credentials are not persisted;
- Codex never receives the GitHub code-write token;
- each job requires explicit allowed paths;
- protected paths cannot overlap allowed paths;
- deterministic change guards run before and after validation;
- the base branch must still equal the authorized SHA before push;
- only an isolated branch can be pushed;
- the workflow can open a PR but cannot merge it.

The Alpaca code-worker configuration remains disabled until the separate write credential exists.

## Remaining manual setup

The major remaining manual infrastructure step is creating the separate fine-grained GitHub token discussed in chat and saving it as:

`ORCHESTRATOR_CODE_WRITE_TOKEN`

That token should be scoped only to intended code-worker repositories with:

- Contents: Read and write;
- Pull requests: Read and write;
- minimal/default permissions otherwise.

After that, enable one narrow code worker and manually supervise its first PR-only job before allowing the master orchestrator to dispatch Codex development work automatically.
