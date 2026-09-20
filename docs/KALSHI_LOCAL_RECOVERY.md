# Kalshi E001 Local Recovery Procedure

The remote recovery search is exhausted. Do not reconstruct the missing implementation from memory.

## Goal

Determine whether the original computer still contains the exact uncommitted E001 collector worktree or an exact archive of it.

## Read-only intake

From a local clone of `passive-income-orchestrator`:

```bash
python -m pip install -e .
kalshi-recovery-intake /absolute/path/to/suspected/kalshi-worktree \
  --output kalshi-e001-local-inventory.json
```

The intake tool:

- does not modify the suspected worktree;
- skips `.git`, virtual environments, caches, and `node_modules`;
- hashes every file with SHA-256;
- calculates the canonical Git blob SHA for every file;
- checks the exact known recovered Git blob identities;
- identifies additional `src/` and test files not present in the remote recovery set.

## Do not do these first

Do not:

- run formatters;
- install dependencies into the suspected worktree;
- run code-generation tools;
- rename or move files;
- commit the worktree;
- merge it with current GitHub branches;
- recreate missing modules from remembered behavior.

Any of those actions can make provenance harder to establish.

## If additional source/tests are found

Preserve the directory as-is. Create a byte-for-byte archive or filesystem copy before changing anything. The inventory output alone does not prove that additional files are the exact prior implementation; provenance still needs to be reconciled against timestamps, Git object identities, local reflogs/objects, shell history, or other preserved evidence.

## Current remote evidence

The known remote recovery set includes the truncated 10,000-byte bundle, nine complete tar members, separately recovered dangling blobs including `src/kalshi_mm/api.py`, and the two retained recovery artifacts. It does not contain the complete later collector source tree or the reported focused test suite.
