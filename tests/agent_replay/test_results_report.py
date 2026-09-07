"""Tests for the pilot's results report (TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, AC #5).

Structural completeness check only (all 5 statements present) — never a check on which way any
of them resolved, per test_plan.md test #13's own scope.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_RESULTS_PATH = (
    _REPO_ROOT
    / "stored_artifacts"
    / "TCK-20260907-FILTERED-REPLAY-EVAL-PILOT"
    / "results.md"
)

_EXIT_CRITERIA = (
    "Repeatable scoring established",
    "Sample quality accepted for the 2 target defect classes",
    "Replay contamination risk is understood and demonstrably controlled",
)
_KILL_CRITERIA = (
    "Scores are noisy/non-repeatable",
    "Worktree isolation cannot fully eliminate the shared-sidecar contamination risk",
)


def test_results_report_states_all_3_exit_criteria_and_both_kill_criteria():
    """Structural completeness check only: each of the 3 Exit Criteria must be stated verbatim
    with an explicit MET/NOT MET label attached, and each of the 2 Kill Criteria must be stated
    verbatim with an explicit FIRED/NOT FIRED label attached — never a check on which way any of
    them actually resolved (test_plan.md test #13's own scope)."""
    assert _RESULTS_PATH.exists(), f"{_RESULTS_PATH} does not exist — Step 8 must produce it"
    text = _RESULTS_PATH.read_text(encoding="utf-8")

    for criterion in _EXIT_CRITERIA:
        assert criterion in text, f"Exit Criterion not stated verbatim in results.md: {criterion!r}"
        idx = text.index(criterion)
        nearby = text[idx : idx + len(criterion) + 40]
        assert "MET" in nearby, f"Exit Criterion has no MET/NOT MET label attached: {criterion!r}"

    for criterion in _KILL_CRITERIA:
        assert criterion in text, f"Kill Criterion not stated verbatim in results.md: {criterion!r}"
        idx = text.index(criterion)
        nearby = text[idx : idx + len(criterion) + 40]
        assert "FIRED" in nearby, f"Kill Criterion has no FIRED/NOT FIRED label attached: {criterion!r}"
