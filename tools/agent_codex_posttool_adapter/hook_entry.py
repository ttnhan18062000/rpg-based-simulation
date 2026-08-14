"""Fail-open runnable boundary for the reviewed Codex PostToolUse adapter.

The production command accepts no arguments.  It derives the repository monitoring target from
this installed source tree and receives only reviewed identity metadata through the environment.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Mapping, TextIO

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.agent_codex_posttool_adapter.adapter import process_post_tool_use


_IDENTITY_ENV = {
    "execution_id": "CODEX_HOOK_EXECUTION_ID",
    "ticket_id": "CODEX_HOOK_TICKET_ID",
    "run_id": "CODEX_HOOK_RUN_ID",
    "phase": "CODEX_HOOK_PHASE",
    "agent": "CODEX_HOOK_AGENT",
    "seq_start": "CODEX_HOOK_SEQ_START",
}


def _identity_from_env(env: Mapping[str, str]) -> tuple[str, str, str, str, str, int]:
    values = {name: env.get(key) for name, key in _IDENTITY_ENV.items()}
    if not all(isinstance(values[name], str) and values[name] for name in _IDENTITY_ENV):
        raise ValueError("required hook identity environment is missing")
    try:
        seq_start = int(values["seq_start"])
    except (TypeError, ValueError) as exc:
        raise ValueError("hook sequence start is invalid") from exc
    if seq_start < 1:
        raise ValueError("hook sequence start is invalid")
    return (
        values["execution_id"], values["ticket_id"], values["run_id"], values["phase"],
        values["agent"], seq_start,
    )


def _next_seq(target_path: Path, execution_id: str, seq_start: int) -> int:
    if not target_path.exists():
        return seq_start
    count = 0
    for raw in target_path.read_bytes().splitlines():
        row = json.loads(raw)
        if isinstance(row, dict) and row.get("execution_id") == execution_id:
            count += 1
    return seq_start + count


def main(
    stdin: TextIO | None = None,
    env: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> int:
    """Process one callback and always return zero; injection parameters are test seams only."""
    try:
        raw_payload = json.load(stdin if stdin is not None else sys.stdin)
        source_env = os.environ if env is None else env
        execution_id, ticket_id, run_id, phase, agent, seq_start = _identity_from_env(source_env)
        root = _ROOT if repo_root is None else Path(repo_root).resolve()
        target_path = root / "agent-monitoring" / "tools.jsonl"
        process_post_tool_use(
            raw_payload,
            target_path=target_path,
            execution_id=execution_id,
            ticket_id=ticket_id,
            run_id=run_id,
            seq=_next_seq(target_path, execution_id, seq_start),
            phase=phase,
            agent=agent,
            env=source_env,
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
