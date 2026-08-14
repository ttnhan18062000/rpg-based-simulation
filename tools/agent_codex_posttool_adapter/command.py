"""Review-only rendering of the future fixed PostToolUse command."""
from __future__ import annotations

import shlex
from pathlib import Path


def render_review_command(repo_root: Path | str) -> str:
    root = Path(repo_root).resolve()
    interpreter = root / ".venv" / "bin" / "python3"
    entrypoint = root / "tools" / "agent_codex_posttool_adapter" / "hook_entry.py"
    return f"{shlex.quote(str(interpreter))} {shlex.quote(str(entrypoint))}"
