"""Output-only CLI for preparing one future controlled-pilot policy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .preparation import prepare_context


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare, but never invoke, the fixed Codex pilot")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--execution-id", required=True)
    args = parser.parse_args()
    context = prepare_context(args.repo_root, args.execution_id)
    print(json.dumps({"ticket_id": context.ticket_id, "policy_path": context.policy_path, "mode": "prepare-only"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
