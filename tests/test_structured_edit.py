from __future__ import annotations

import json
from pathlib import Path

import pytest

from controller.structured_edit import _exact_allowed_files, _response_schema


def test_response_schema_restricts_paths() -> None:
    schema = _response_schema(["tests/test_execution.py"])
    assert schema["properties"]["files"]["items"]["properties"]["path"]["enum"] == [
        "tests/test_execution.py"
    ]


def test_structured_fallback_requires_exact_existing_files(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "tests").mkdir()
    (target / "tests" / "test_execution.py").write_text("x = 1\n", encoding="utf-8")

    job = {"allowed_paths": ["tests/test_execution.py"]}
    assert _exact_allowed_files(job, target) == ["tests/test_execution.py"]


def test_structured_fallback_rejects_directory_scope(tmp_path: Path) -> None:
    target = tmp_path / "target"
    (target / "tests").mkdir(parents=True)

    with pytest.raises(ValueError, match="exact existing files"):
        _exact_allowed_files({"allowed_paths": ["tests/"]}, target)
