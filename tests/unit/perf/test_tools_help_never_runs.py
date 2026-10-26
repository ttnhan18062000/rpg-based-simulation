"""Every perf tool entry point treats ``--help`` as a request for usage, never as a run.

TCK-20261024-PERF-TOOLS-HELP-FLAG-NEVER-STARTS-A-RUN: ``perf_baseline.py --help`` once started a real benchmark suite on a shared host,
because the script read ``sys.argv`` by hand and treated anything but ``--update`` as "run". This test starts every ``tools/perf/*.py`` file with
a ``__main__`` block, plus ``tools/bench_corpus_world.py``, with ``--help`` and checks four things: it exits 0, it prints usage, it starts no
child process, and it writes nothing. Nothing here runs a benchmark.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PER_TOOL_TIMEOUT_S = 20

# Runs the tool the way `python tool.py --help` would, with child processes forbidden: any attempt to spawn one raises, so the tool exits non-zero.
_RUNNER = """
import runpy, subprocess, sys
def _no_child(*args, **kwargs):
    raise RuntimeError("--help started a child process")
subprocess.Popen = _no_child
path = sys.argv[1]
sys.argv = [path, "--help"]
sys.path.insert(0, {root!r})
runpy.run_path(path, run_name="__main__")
"""


def _entry_points() -> List[Path]:
    tools = sorted(p for p in (REPO_ROOT / "tools" / "perf").glob("*.py") if '__name__ == "__main__"' in p.read_text(encoding="utf-8"))
    return tools + [REPO_ROOT / "tools" / "bench_corpus_world.py"]


ENTRY_POINTS = _entry_points()


def test_entry_points_were_found() -> None:
    """The discovery finds the four tools that once had no parser, so the parametrised test below cannot pass by checking nothing."""
    names = {p.name for p in ENTRY_POINTS}
    assert {"perf_baseline.py", "run_perf_baseline.py", "perf_report.py", "turbo_run.py", "bench_corpus_world.py"} <= names


@pytest.mark.parametrize("tool", ENTRY_POINTS, ids=lambda p: p.name)
def test_help_exits_zero_and_runs_nothing(tool: Path, tmp_path: Path) -> None:
    """``--help`` exits 0 within the timeout, prints usage, spawns no child and leaves an empty working directory."""
    result = subprocess.run(  # noqa: S603  (fixed interpreter, repo-owned script, no shell)
        [sys.executable, "-c", _RUNNER.format(root=str(REPO_ROOT)), str(tool)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=PER_TOOL_TIMEOUT_S,
        check=False,
    )
    assert result.returncode == 0, f"{tool.name} --help exited {result.returncode}: {result.stderr[-400:]}"
    assert "usage" in result.stdout.lower(), f"{tool.name} --help printed no usage text"
    assert list(tmp_path.iterdir()) == [], f"{tool.name} --help wrote files: {[p.name for p in tmp_path.iterdir()]}"


@pytest.mark.parametrize("tool", [REPO_ROOT / "tools" / "perf" / n for n in ("perf_baseline.py", "run_perf_baseline.py", "perf_report.py", "turbo_run.py")], ids=lambda p: p.name)
def test_unknown_flag_exits_two_without_running(tool: Path, tmp_path: Path) -> None:
    """An unknown flag is an argparse error (exit 2), never a fall-through to a run."""
    runner = _RUNNER.replace('["--help"]', '["--definitely-not-a-flag"]').replace('[path, "--help"]', '[path, "--definitely-not-a-flag"]')
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", runner.format(root=str(REPO_ROOT)), str(tool)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=PER_TOOL_TIMEOUT_S,
        check=False,
    )
    assert result.returncode == 2, f"{tool.name} with an unknown flag exited {result.returncode}: {result.stderr[-400:]}"
    assert list(tmp_path.iterdir()) == []
