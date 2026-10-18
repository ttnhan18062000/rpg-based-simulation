"""TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS: no tool writes a raw-dict corpus baseline. No heavy run."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from tools import bench_corpus_world

REPO_ROOT = Path(__file__).resolve().parents[3]
#: The only tools that may mention a corpus scenario id and write a file: the candidate writer (to ``reports/``) and the promoter.
ALLOWED_WRITERS = {"tools/perf/rerun_baselines.py", "tools/perf/baseline_lifecycle.py"}
WRITES = re.compile(r"write_text|write_bytes|open\([^)]*[\"'][wax]b?[\"']")


def test_commit_flag_is_gone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["bench_corpus_world.py", "--world", "frontier_extended", "--commit"])
    with pytest.raises(SystemExit) as exit_info:
        bench_corpus_world.main()
    assert exit_info.value.code == 2  # argparse: unrecognized arguments


def writes_corpus_baseline(text: str) -> bool:
    """A module naming a corpus scenario id (``simq_corpus_``) that also writes and mentions the baselines directory."""
    return "simq_corpus_" in text and "baselines" in text.lower() and bool(WRITES.search(text))


def test_the_guard_bites_on_the_removed_writer() -> None:
    removed = (
        'BASELINES_DIR = Path("tests/perf/baselines")\n'
        'out_path = BASELINES_DIR / f"simq_corpus_{args.world}.json"\n'
        "out_path.write_text(json.dumps(result))\n"
    )  # the shape of bench_corpus_world.py --commit before TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS
    assert writes_corpus_baseline(removed)
    assert not writes_corpus_baseline(removed.replace(".write_text(", ".read_text("))


def test_bench_corpus_world_writes_nothing() -> None:
    source = Path(bench_corpus_world.__file__).read_text(encoding="utf-8")
    assert not WRITES.search(source)
    assert "BASELINES_DIR" not in source


def test_no_other_tool_writes_a_corpus_baseline_file() -> None:
    offenders = []
    for root in ("tools", "src"):
        for path in sorted((REPO_ROOT / root).rglob("*.py")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            if relative in ALLOWED_WRITERS:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if writes_corpus_baseline(text):
                offenders.append(relative)
    assert offenders == []
