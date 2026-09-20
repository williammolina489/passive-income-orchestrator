from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


KNOWN_BLOBS = {
    ".github/workflows/ci.yml": "751eb467a909f75b70c7a44f47cec0f7283a62df",
    ".github/workflows/e001-smoke-bootstrap.yml": "efe2045600eca6360f65e253d48bf9a86101c986",
    ".github/workflows/e001-smoke-finalize.yml": "eacaeb93469eefe57534268c4f5053e0d7cd2e1b",
    "ARCHITECTURE.md": "e7c90b01fe5b13d7fca4f04de7c69c6529ac8180",
    "DATA_SOURCES.md": "09bd20cb0aa71a8498a7b644a44015a8406b3b9a",
    "EXPERIMENTS.md": "a27a65c63d5ec106c02831f7aa0d2e7e0986f9a1",
    "PROJECT_STATE.md": "0badffb431d8aa433e1c47556e0fe5fee48862bc",
    "ROADMAP.md": "fba2168bfad218937a375d3900381b76059d9b2d",
    "SECURITY.md": "d502d6aeacfc4a9438593b695b7ab11b59d12a37",
    "docs/COLLECTOR_RUNBOOK.md": "23b5197848451a3db32c120bce9d6bdd0c99b637",
    "pyproject.toml": "7b17ce693cb1d31f192288a5c3b3739b0ec11adb",
    "research/API_CONTRACT_REVALIDATION.md": "13f244f73e7cfc863f6a06046094bd4599b3cec9",
    "research/E001_SMOKE_PROTOCOL.md": "436edb494deb34567b1841c36eeaed091fcff6c0",
    "research/E001_SMOKE_RESULT.md": "17268372f629b37d5d1ea6a7060a406fcb7a7831",
    "src/kalshi_mm/api.py": "ff9f17f3ce25b17d959de754169a2e2cbf77d2e3",
}

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "node_modules",
}

EXPECTED_LATER_AREAS = [
    "src/kalshi_mm",
    "tests",
]


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def file_record(root: Path, path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    rel = path.relative_to(root).as_posix()
    blob = git_blob_sha(data)
    known_expected = KNOWN_BLOBS.get(rel)
    return {
        "path": rel,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob_sha": blob,
        "known_expected_git_blob_sha": known_expected,
        "known_identity_match": (
            blob == known_expected if known_expected is not None else None
        ),
        "is_python": path.suffix == ".py",
        "is_test": rel.startswith("tests/") or "/test_" in rel or rel.endswith("_test.py"),
    }


def inventory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")

    files: list[dict[str, Any]] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)
        for name in sorted(names):
            path = Path(current) / name
            if path.is_symlink() or not path.is_file():
                continue
            files.append(file_record(root, path))

    by_path = {row["path"]: row for row in files}
    known_checks = []
    for path, expected in sorted(KNOWN_BLOBS.items()):
        row = by_path.get(path)
        known_checks.append(
            {
                "path": path,
                "expected_git_blob_sha": expected,
                "present": row is not None,
                "actual_git_blob_sha": row["git_blob_sha"] if row else None,
                "exact_match": bool(row and row["git_blob_sha"] == expected),
            }
        )

    python_source = [
        row["path"]
        for row in files
        if row["is_python"] and row["path"].startswith("src/")
    ]
    tests = [row["path"] for row in files if row["is_test"]]
    unknown_source = [
        row["path"]
        for row in files
        if row["path"].startswith("src/") and row["path"] not in KNOWN_BLOBS
    ]
    unknown_tests = [
        row["path"]
        for row in files
        if row["is_test"] and row["path"] not in KNOWN_BLOBS
    ]

    return {
        "schema_version": "1.0",
        "mode": "READ_ONLY_FORENSIC_INVENTORY",
        "root": str(root),
        "file_count": len(files),
        "known_identity_checks": known_checks,
        "all_known_present_and_exact": all(
            row["present"] and row["exact_match"] for row in known_checks
        ),
        "python_source_files": python_source,
        "test_files": tests,
        "additional_source_files_not_in_known_recovery_set": unknown_source,
        "additional_test_files_not_in_known_recovery_set": unknown_tests,
        "has_additional_recovery_candidates": bool(unknown_source or unknown_tests),
        "files": files,
        "interpretation": (
            "Additional source/tests are recovery candidates only. Their presence does not "
            "prove they are the exact prior implementation until their provenance and Git "
            "history/object identities are independently verified."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only forensic inventory for a surviving local Kalshi E001 worktree. "
            "No files are modified."
        )
    )
    parser.add_argument("worktree", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("kalshi-e001-local-inventory.json"),
    )
    args = parser.parse_args(argv)

    report = inventory(args.worktree)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "mode": report["mode"],
        "file_count": report["file_count"],
        "all_known_present_and_exact": report["all_known_present_and_exact"],
        "additional_source_files": report["additional_source_files_not_in_known_recovery_set"],
        "additional_test_files": report["additional_test_files_not_in_known_recovery_set"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
