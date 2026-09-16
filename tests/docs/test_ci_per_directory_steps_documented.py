"""Doc-content tests for CLAUDE.md's "CI Failure Triage" step-conclusion diagnostic
(TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS).

Pins the ticket's own CLAUDE.md acceptance criterion as a real, reproducible content check
against CLAUDE.md itself, rather than trusting the prose was written as intended.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CLAUDE_MD = _REPO_ROOT / "CLAUDE.md"


def _ci_triage_section() -> str:
    text = _CLAUDE_MD.read_text(encoding="utf-8")
    start = text.index("### CI Failure Triage")
    end = text.index("### PR Lifecycle", start)
    return text[start:end]


def test_step_conclusion_technique_documented():
    section = _ci_triage_section()
    assert "Step-level conclusions stay readable" in section
    assert "actions/jobs/{job_id}" in section
    assert "if: always()" in section


def test_step_conclusion_technique_names_the_owning_ticket():
    section = _ci_triage_section()
    assert "TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS" in section


def test_partial_fetch_caveat_documented():
    section = _ci_triage_section()
    assert "partial log fetch is not evidence" in section
    assert "silently" in section
