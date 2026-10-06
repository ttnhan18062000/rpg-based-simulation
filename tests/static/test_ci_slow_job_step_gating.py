"""Static guard for TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN.

In the `slow` job of `.github/workflows/test.yml`, the corpus-diversity step (5) failed or was
cancelled on most `main` runs, and the two later test steps (6 slow tests, 7 legacy regression)
had no `if:`, so they inherited the default `success()` and were skipped. Owner decision
2026-10-05: steps 6 and 7 run whether step 5 passes or fails, but a cancelled run stays
cancelled. This pins that shape: `!cancelled()` on 6 and 7, no `always()` or `continue-on-error`
on 5-7, and a closing summary step that reports each step's outcome.

Same `yaml.safe_load` pattern as `tests/static/test_corpus_diversity_ci_isolation.py`; no live
GitHub Actions execution is possible from pytest.
"""

from pathlib import Path

import yaml

_WORKFLOW_PATH = Path(__file__).resolve().parent.parent.parent / ".github" / "workflows" / "test.yml"

_CORPUS_RUN = "make simq-corpus-diversity-slow-isolated"
_SLOW_TESTS_RUN = '-m "slow or extra_slow"'
_LEGACY_RUN = "make lane-legacy-regression"
_NOT_CANCELLED = "${{ !cancelled() }}"


def _slow_job_steps() -> list[dict]:
    workflow = yaml.safe_load(_WORKFLOW_PATH.read_text(encoding="utf-8"))
    return workflow["jobs"]["slow"]["steps"]


def _step_running(needle: str) -> dict:
    matches = [s for s in _slow_job_steps() if needle in s.get("run", "")]
    assert len(matches) == 1, f"expected exactly one slow-job step running {needle!r}, found {len(matches)}"
    return matches[0]


def _summary_step() -> dict:
    matches = [s for s in _slow_job_steps() if "GITHUB_STEP_SUMMARY" in s.get("run", "")]
    assert len(matches) == 1, "expected exactly one slow-job step writing GITHUB_STEP_SUMMARY"
    return matches[0]


def test_slow_tests_step_runs_even_when_corpus_diversity_fails() -> None:
    assert _step_running(_SLOW_TESTS_RUN).get("if") == _NOT_CANCELLED


def test_legacy_regression_step_runs_even_when_corpus_diversity_fails() -> None:
    assert _step_running(_LEGACY_RUN).get("if") == _NOT_CANCELLED


def test_steps_five_to_seven_never_use_always_or_continue_on_error() -> None:
    """`always()` would turn an evicted (cancelled) run into a reported result;
    `continue-on-error` would hide a red step from the job conclusion."""
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        step = _step_running(needle)
        assert "always()" not in str(step.get("if", "")), step["name"]
        assert "continue-on-error" not in step, step["name"]


def test_each_test_step_has_an_id_for_the_summary_to_read() -> None:
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        assert _step_running(needle).get("id"), needle


def test_summary_step_reports_every_test_step_outcome() -> None:
    summary = _summary_step()
    assert summary.get("if") == _NOT_CANCELLED
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        step_id = _step_running(needle)["id"]
        assert f"steps.{step_id}.outcome" in summary["run"], step_id


def test_summary_step_runs_after_the_three_test_steps() -> None:
    steps = _slow_job_steps()
    summary_index = steps.index(_summary_step())
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        assert steps.index(_step_running(needle)) < summary_index
