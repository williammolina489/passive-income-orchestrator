from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from controller.decide import DEFAULT_MODEL, call_controller
from controller.execute import execute_candidate
from controller.status import ROOT


def run_once(root: Path, model: str) -> dict:
    decision = call_controller(root=root, model=model)
    if decision["decision"]["decision"] != "RUN_TASK":
        return {
            "mode": "NO_DISPATCH",
            "controller": decision,
            "execution": None,
        }

    execution = execute_candidate(decision, root=root)
    return {
        "mode": "EXECUTED_ONE_TASK",
        "controller": decision,
        "execution": execution,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify state, make one bounded controller decision, and execute at most one configured worker."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--model",
        default=os.environ.get("ORCHESTRATOR_MODEL", DEFAULT_MODEL),
    )
    args = parser.parse_args(argv)

    result = run_once(args.root.resolve(), args.model)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
