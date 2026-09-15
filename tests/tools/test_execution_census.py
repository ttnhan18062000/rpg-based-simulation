"""Tests for tools/execution_census.py's classification engine.

Uses real coverage.py instrumentation against a tiny fixture module rather than mocking
coverage.py's internals — the classification logic depends on coverage.py's real Analysis
objects (branch_stats(), statements/missing sets), and mocking those risks testing against an
assumption about the API rather than the API itself.
"""
import sys
import textwrap
from pathlib import Path

import pytest

coverage = pytest.importorskip("coverage")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from execution_census import _classify, LIMITATION_HEADER  # noqa: E402


FIXTURE_SOURCE = textwrap.dedent(
    """
    def check_gate(value):
        # A branch that a "test" run takes both sides of, but a "corpus" run never takes the
        # True side of — the check_for_boss_spawn() shape this whole census exists to find.
        if value >= 50:
            return "high"
        return "low"

    def never_called_at_all():
        return "dead"

    def called_by_test_only():
        return "test-shape"
    """
)


@pytest.fixture()
def fixture_module(tmp_path):
    mod_path = tmp_path / "census_fixture_mod.py"
    mod_path.write_text(FIXTURE_SOURCE)
    return mod_path


def _run_under_coverage(mod_path: Path, data_file: Path, body):
    """Runs `body(module)` under branch coverage, writing to data_file."""
    import importlib.util

    cov = coverage.Coverage(data_file=str(data_file), branch=True, source=[str(mod_path.parent)])
    cov.start()
    try:
        spec = importlib.util.spec_from_file_location("census_fixture_mod", mod_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        body(module)
    finally:
        cov.stop()
        cov.save()


def test_classify_finds_test_only_and_incomplete_branch(tmp_path, fixture_module):
    unit_data = tmp_path / ".coverage.unit_test"
    corpus_data = tmp_path / ".coverage.corpus_test"

    # "Unit" run: exercises every function, both branch directions of check_gate.
    def unit_body(module):
        module.check_gate(100)  # True branch
        module.check_gate(1)    # False branch
        module.called_by_test_only()
        # never_called_at_all() is deliberately never invoked by either run.

    # "Corpus" run: exercises check_gate only with values that never take the True branch, and
    # never calls called_by_test_only() at all.
    def corpus_body(module):
        module.check_gate(1)
        module.check_gate(2)

    _run_under_coverage(fixture_module, unit_data, unit_body)
    _run_under_coverage(fixture_module, corpus_data, corpus_body)

    unit_cov = coverage.Coverage(data_file=str(unit_data), branch=True, source=[str(fixture_module.parent)])
    unit_cov.load()
    corpus_cov = coverage.Coverage(data_file=str(corpus_data), branch=True, source=[str(fixture_module.parent)])
    corpus_cov.load()

    findings = _classify(unit_cov, corpus_cov, str(fixture_module))
    by_line = {f.line: f for f in findings}

    # The `if value >= 50:` line ran in the corpus run (line is "tick-live") but never took the
    # True exit — branch_complete must be False, not just "covered".
    gate_line = next(f for f in findings if "value >= 50" in fixture_module.read_text().splitlines()[f.line - 1])
    assert gate_line.reachability == "tick-live"
    assert gate_line.branch_complete is False
    assert gate_line.taken_exits < gate_line.total_exits

    # `return "high"` (the True-branch-only line) must show as test-only: executed by the unit
    # run, never reached by the corpus run at all.
    high_line = next(
        f for f in findings
        if 'return "high"' in fixture_module.read_text().splitlines()[f.line - 1]
    )
    assert high_line.reachability == "test-only"

    # A function never called by either run must be never-called.
    dead_line = next(
        f for f in findings
        if "return \"dead\"" in fixture_module.read_text().splitlines()[f.line - 1]
    )
    assert dead_line.reachability == "never-called"

    # Effectiveness is deliberately not automated in this version -- every finding must say so
    # explicitly, not silently omit the field.
    assert all(f.effectiveness == "not_automated" for f in findings)


def test_classify_without_unit_baseline_treats_unreached_as_never_called(tmp_path, fixture_module):
    corpus_data = tmp_path / ".coverage.corpus_only"

    def corpus_body(module):
        module.check_gate(1)

    _run_under_coverage(fixture_module, corpus_data, corpus_body)

    corpus_cov = coverage.Coverage(data_file=str(corpus_data), branch=True, source=[str(fixture_module.parent)])
    corpus_cov.load()

    # No unit_cov at all (None) -- matches cmd_report's own behavior when no baseline exists yet.
    findings = _classify(None, corpus_cov, str(fixture_module))
    assert findings, "expected at least one finding even with no unit baseline"
    # Without a unit baseline, nothing not reached by the corpus can be distinguished as
    # "test-only" -- it must fall back to never-called rather than crash or silently vanish.
    never_reached = [f for f in findings if f.reachability != "tick-live"]
    assert all(f.reachability == "never-called" for f in never_reached)


def test_limitation_header_names_its_own_boundary():
    # The report's own limitation text must state, in plain language, both the "cannot see a
    # live-but-wrong mechanism" boundary and that effectiveness is not automated -- this is the
    # thing peer review asked to be unsuppressable in the tool's own output, not just the docs.
    assert "cannot detect a live mechanism producing a wrong outcome" in LIMITATION_HEADER
    assert "not automated" in LIMITATION_HEADER
