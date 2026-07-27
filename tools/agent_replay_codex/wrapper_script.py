"""Standalone entry point the real Codex CLI process invokes via `codex exec` (see invoker.py).

Imports and calls the exact same tools.agent_replay.fixture_envelope.load_fixture() /
tools.agent_replay.runner.replay_slice() functions the Python-only replay proof already calls,
unmodified — proving a real Codex-invoked process can drive the identical deterministic code
path, not a Codex-side reimplementation.

Never imports/subprocesses/references the four forbidden monitoring/hook scripts under
tools/agent-monitoring/ (pre_tool_hook, post_tool_hook, record_run, record_events), directly or
transitively — replay_slice()'s own in-memory fake stand-ins already guarantee this at the
function level; this file additionally never names those four script files literally anywhere in
its own source (see tests/agent_replay_codex/test_no_forbidden_calls.py's whole-file
string-constant scan, a new sibling instance of tools/agent_replay's own guard).

Reads ONLY: the fixture YAML at --fixture (read-only) and the tools/agent_replay/*,
tools/gate_checks/*, tools/tag_registry.py Python source (import, read-only). Writes ONLY the
JSON result file at --out — never any path under tickets/ or agent-monitoring/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.fixture_envelope import load_fixture  # noqa: E402
from agent_replay.runner import replay_slice  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    fixture = load_fixture(args.fixture)
    outcome = replay_slice(fixture)

    Path(args.out).write_text(
        json.dumps({"final_status": outcome.final_status, "phases_completed": outcome.phases_completed}),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
