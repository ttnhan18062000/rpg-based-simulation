"""Doc-content tests for CLAUDE.md's "CI Failure Triage" absent-run branch
(TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH).

Pins each of the ticket's own Acceptance Criteria as a real, reproducible content check against
CLAUDE.md itself, rather than trusting the prose was written as intended.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CLAUDE_MD = _REPO_ROOT / "CLAUDE.md"


def _ci_triage_section() -> str:
    text = _CLAUDE_MD.read_text(encoding="utf-8")
    start = text.index("### CI Failure Triage")
    end = text.index("### PR Lifecycle", start)
    return text[start:end]


def test_ci_triage_section_exists():
    assert "### CI Failure Triage" in _CLAUDE_MD.read_text(encoding="utf-8")


def test_absent_run_branch_covers_the_mergeable_check():
    section = _ci_triage_section()
    assert "mergeable" in section
    assert "gh pr view" in section


def test_absent_run_branch_covers_the_trigger_block_check():
    section = _ci_triage_section()
    assert "trigger block" in section
    assert "pull_request" in section
    assert "CONFLICTING" in section


def test_absent_run_branch_prohibits_retrigger_force_push_and_branch_recreation():
    section = _ci_triage_section()
    assert "re-trigger commit" in section
    assert "force-push" in section
    assert "branch recreation" in section
    assert "Never" in section


def test_absent_run_branch_includes_git_ls_remote_disambiguator():
    section = _ci_triage_section()
    assert "git ls-remote" in section
    assert "headRefOid" in section


def test_absent_run_branch_states_the_general_principle_not_only_the_specific_case():
    section = _ci_triage_section()
    assert "diagnosed differently" in section


def test_absent_run_branch_appears_before_the_failing_job_branch():
    # An absent-run check must happen first -- you cannot triage a failing job's logs for a run
    # that was never created.
    section = _ci_triage_section()
    absent_idx = section.index("An absent CI run is diagnosed differently")
    failing_idx = section.index("Never conclude root cause from the job name or a guess")
    assert absent_idx < failing_idx


def test_ci_triage_list_still_numbered_consistently_after_insertion():
    # Regression guard: inserting a new first item must renumber the rest, not leave a duplicate
    # or skipped number.
    section = _ci_triage_section()
    for n in ("1.", "2.", "3.", "4.", "5."):
        assert f"\n{n} **" in section or f"\n{n} Report" in section, (
            f"expected a top-level numbered item starting with {n!r}"
        )
