from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from controller.codex_job import ROOT, _normalize_scope, validate_job


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def _is_within(path: str, scope: str) -> bool:
    normalized_path = PurePosixPath(path.replace("\\", "/")).as_posix()
    normalized_scope = _normalize_scope(scope)
    return (
        normalized_path == normalized_scope
        or normalized_path.startswith(normalized_scope + "/")
    )


def changed_paths(repo: Path, expected_sha: str) -> list[str]:
    tracked = {
        line.strip()
        for line in _git(repo, "diff", "--name-only", expected_sha, "--").splitlines()
        if line.strip()
    }
    untracked = {
        line.strip()
        for line in _git(
            repo, "ls-files", "--others", "--exclude-standard"
        ).splitlines()
        if line.strip()
    }
    return sorted(tracked | untracked)


def validate_changes(
    root: Path,
    job_path: Path,
    target_repo: Path,
) -> dict[str, Any]:
    job, project, _ = validate_job(root, job_path, require_enabled=True)
    worker = project["code_worker"]
    paths = changed_paths(target_repo, job["expected_head_sha"])
    if not paths:
        return {
            "schema_version": "1.0",
            "status": "NO_CHANGES",
            "changed_paths": [],
        }
    if len(paths) > 50:
        raise ValueError(f"Codex changed {len(paths)} files; maximum is 50")

    violations: list[str] = []
    for path in paths:
        if not any(_is_within(path, scope) for scope in job["allowed_paths"]):
            violations.append(f"{path}: outside allowed_paths")
        if any(_is_within(path, scope) for scope in worker.get("protected_paths", [])):
            violations.append(f"{path}: overlaps protected path")
        fs_path = target_repo / path
        if fs_path.exists() and fs_path.is_symlink():
            violations.append(f"{path}: changed symlinks are not permitted")

    if violations:
        raise ValueError("Codex change guard failed: " + "; ".join(violations))

    _git(target_repo, "diff", "--check", job["expected_head_sha"], "--")
    return {
        "schema_version": "1.0",
        "status": "PASS",
        "changed_paths": paths,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Codex edits before any push.")
    parser.add_argument("job_file", type=Path)
    parser.add_argument("target_repo", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = validate_changes(
        args.root.resolve(),
        args.job_file.resolve(),
        args.target_repo.resolve(),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
