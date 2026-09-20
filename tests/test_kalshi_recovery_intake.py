from pathlib import Path

from controller.kalshi_recovery_intake import git_blob_sha, inventory


def test_git_blob_sha_matches_git_algorithm() -> None:
    assert git_blob_sha(b"test content\n") == "d670460b4b4aece5915caf5c68d12f560a9fe3e4"


def test_inventory_finds_additional_source_and_tests(tmp_path: Path) -> None:
    (tmp_path / "src" / "kalshi_mm").mkdir(parents=True)
    (tmp_path / "tests").mkdir()

    (tmp_path / "src" / "kalshi_mm" / "collector.py").write_text(
        "x = 1\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_collector.py").write_text(
        "def test_x(): assert True\n", encoding="utf-8"
    )

    report = inventory(tmp_path)

    assert report["mode"] == "READ_ONLY_FORENSIC_INVENTORY"
    assert "src/kalshi_mm/collector.py" in report[
        "additional_source_files_not_in_known_recovery_set"
    ]
    assert "tests/test_collector.py" in report[
        "additional_test_files_not_in_known_recovery_set"
    ]
    assert report["has_additional_recovery_candidates"] is True


def test_inventory_ignores_git_and_cache_dirs(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / ".git" / "secret").write_text("x", encoding="utf-8")
    (tmp_path / "__pycache__" / "a.pyc").write_bytes(b"x")
    (tmp_path / "README.md").write_text("ok\n", encoding="utf-8")

    report = inventory(tmp_path)
    paths = {row["path"] for row in report["files"]}

    assert paths == {"README.md"}
