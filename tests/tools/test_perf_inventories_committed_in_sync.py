"""The committed perf inventory reports must equal the live tool output (TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN).

`phase_inventory.json` went stale after `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT` changed a heading
the tool reads, and nothing failed because no test or CI job ran the `--check`. Each tool ignores
source line numbers and the embedded commit id, so unrelated commits do not trip this; only a real
change to a counted fact does. Fix a failure by regenerating the report with the tool, never by hand.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PERF_DIR = REPO_ROOT / "docs" / "performance"
INVENTORIES = ["phase_inventory", "hash_callsite_inventory", "wall_clock_inventory"]


def _check(name: str, committed: Path) -> subprocess.CompletedProcess:
    script = REPO_ROOT / "tools" / "perf" / f"{name}.py"
    return subprocess.run(
        [sys.executable, str(script), "--check", str(committed)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


@pytest.mark.parametrize("name", INVENTORIES)
def test_committed_inventory_matches_live_tool_output(name):
    result = _check(name, PERF_DIR / f"{name}.json")
    assert result.returncode == 0, (
        f"docs/performance/{name}.json is stale. Regenerate it with the commands in "
        f"docs/performance/{name}.md.\n{result.stdout}{result.stderr}"
    )


def test_a_drifted_committed_value_fails_the_check(tmp_path):
    """Guards the guard: an edited committed value must make the check exit 1, not pass."""
    data = json.loads((PERF_DIR / "phase_inventory.json").read_text(encoding="utf-8"))
    data["documented_sources"][0]["stated_count"] = 12345
    drifted = tmp_path / "drifted.json"
    drifted.write_text(json.dumps(data), encoding="utf-8")
    result = _check("phase_inventory", drifted)
    assert result.returncode == 1
    assert "stated_count" in result.stdout + result.stderr
