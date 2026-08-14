"""Tests for TCK-20260721-CODEX-CAPABILITY-MATRIX.

Codifies the investigation's manually-gathered direct-experiment evidence (`codex features
list` reporting `hooks stable true` on this environment's installed Codex CLI, see
`docs/ai/codex_capability_matrix.md` section 6) into a re-runnable diagnostic, rather than
leaving it as a one-off manual finding. This is a read-only CLI diagnostic only — it never
invokes any production hook script (`tools/agent-monitoring/post_tool_hook.py`,
`pre_tool_hook.py`, `record_run.py`, `record_events.py`) and never triggers an actual Codex
hook invocation.
"""
import re
import shutil
import subprocess

import pytest


def test_codex_hooks_feature_reported_enabled():
    codex_path = shutil.which("codex")
    if codex_path is None:
        pytest.skip("codex CLI not installed in this environment")

    result = subprocess.run(
        ["codex", "features", "list"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    hooks_line = next(
        (line for line in result.stdout.splitlines() if line.strip().startswith("hooks")),
        None,
    )
    assert hooks_line is not None, (
        f"expected a 'hooks' row in `codex features list` output, got:\n{result.stdout}"
    )
    assert re.search(r"\b(stable|true)\b", hooks_line, re.IGNORECASE), (
        f"expected the 'hooks' row to report an enabled/stable state, got: {hooks_line!r}"
    )
