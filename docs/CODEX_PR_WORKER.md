# PR-only Codex worker

This worker is intentionally **not enabled** until a separate fine-grained GitHub token is configured as `ORCHESTRATOR_CODE_WRITE_TOKEN`.

## Security model

The worker:

- accepts only a committed, schema-valid job from the orchestrator repository;
- derives the target repository and setup/validation commands from trusted `projects.yaml`, not from model output;
- requires the job's expected SHA to match canonical project state;
- refuses closed, stopped, complete, or human-gated projects;
- requires explicit allowed paths and rejects overlap with protected paths;
- checks out the target at the exact authorized commit;
- installs dependencies before Codex starts;
- removes checkout credentials before Codex runs;
- runs Codex using OpenAI's official `openai/codex-action@v1` with the `:workspace` permission profile and `drop-sudo` safety strategy;
- does not provide the GitHub write token to the Codex step;
- runs deterministic change guards before and after project validation;
- refuses to push if the base branch moved;
- pushes only an isolated branch;
- opens a pull request and never merges it.

Version 1 Codex jobs structurally prohibit methodology changes, VALIDATION/OOS access, spending, purchases, live trades, transfers/withdrawals, and default-branch merges.

## Activation gate

Do not enable a project's `code_worker` until:

1. `ORCHESTRATOR_CODE_WRITE_TOKEN` exists;
2. it is scoped only to the intended repositories;
3. Contents and Pull requests are the only write permissions required;
4. a narrow first job is preregistered with explicit allowed paths and completion criteria;
5. the first execution is manually supervised.

The current Alpaca configuration remains disabled until that credential is added.
