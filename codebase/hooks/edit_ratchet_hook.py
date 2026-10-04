"""Claude Code PostToolUse hook: tell the agent about a new or worse ruff finding in the `src` file it just edited.

    python3 -m codebase.hooks.edit_ratchet_hook < PostToolUse-JSON

Advisory only. It always exits 0 and prints either one JSON object (`hookSpecificOutput.additionalContext`
holding the ratchet's NEW / WORSE report) or nothing. Everything that stops it from checking (not an Edit,
Write or MultiEdit of an existing `src/**/*.py` file inside this checkout, no ruff, no registry, the
time budget, any error) is silent, so an unsynced worktree is not noisy. The comparison is
`codebase.gates.staged_ratchet.check`, the pre-commit one. The checkout is found from this file, never from the
working directory, so a file is only ever compared with its own tree's registry. Imports of the health modules
are lazy: almost every edit is not a `src` file and must cost little more than interpreter start-up.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit"})
TIME_BUDGET_S = 5.0
MAX_LINES = 20
POINTER = "Rules: docs/guidelines/python_code_standard.md (the rule ID is in the Enforcement column)."


def _src_path(payload: object, root: Path) -> str | None:
    """The repo-relative `src/**/*.py` path of the edited file, or None when this edit is not one."""
    if not isinstance(payload, dict) or payload.get("tool_name") not in EDIT_TOOLS:
        return None
    tool_input = payload.get("tool_input")
    raw = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(raw, str) or not raw.endswith(".py"):
        return None
    path = Path(raw)
    try:
        rel = (path if path.is_absolute() else Path.cwd() / path).resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    text = rel.as_posix()
    return text if text.startswith("src/") else None


def _context(report: str) -> str:
    lines = report.splitlines()
    if len(lines) > MAX_LINES:
        lines = [*lines[:MAX_LINES], f"... and {len(lines) - MAX_LINES} more line(s)"]
    return "\n".join([*lines, POINTER])


def advice(payload: object, root: Path = REPO_ROOT) -> str | None:
    """The hook's JSON output for `payload`, or None when there is nothing to say."""
    rel = _src_path(payload, root)
    if rel is None:
        return None
    from codebase.gates import staged_ratchet  # noqa: PLC0415 - lazy: most edits are not src files
    from codebase.health import ratchet  # noqa: PLC0415 - lazy: most edits are not src files

    venv_python = root / ".venv" / "bin" / "python3"
    try:
        result = staged_ratchet.check(
            root, [rel], python=str(venv_python) if venv_python.is_file() else None, timeout=TIME_BUDGET_S
        )
    except staged_ratchet.HookSkipped:
        return None
    if result is None or not result.failed:
        return None
    report = ratchet.format_report(ratchet.RatchetResult(new=result.new, worse=result.worse))
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": _context(report)}})


def main() -> int:
    """Read the hook payload from stdin, print the advice if any. Always returns 0."""
    try:
        out = advice(json.loads(sys.stdin.read() or "null"))
        if out:
            print(out)
    except Exception:  # noqa: BLE001 - advisory hook: any failure is silence, never a blocked tool call
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
