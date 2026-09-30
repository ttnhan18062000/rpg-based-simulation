"""Static checks for the test-workflow prose contracts: the investigator's Proof Plan fields, the
architecture-reviewer's advisory test-quality checklist, the implement-epic coordination note, and
the single triage document in regression_policy.md.

Text-level checks only; they pin that each contract exists and stays advisory, not how an agent
behaves at runtime.
"""

import re
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
_AGENTS = _ROOT / ".claude" / "agents"
_POLICY = _ROOT / "docs" / "testing" / "regression_policy.md"
_DELIVERY = _ROOT / "docs" / "guides" / "delivery_process.md"
_EPIC_JS = _ROOT / ".claude" / "workflows" / "implement-epic.js"

_MANDATORY_FIELDS = ("level", "proof kind", "oracle source", "expected effect", "selected commands")
_OPTIONAL_FIELDS = ("negative cases", "fixtures", "non-functional risk")


def _section(text: str, heading: str, level: str = "##") -> str:
    match = re.search(rf"^{re.escape(level)} {re.escape(heading)}.*?(?=^#{{1,{len(level)}}} |\Z)", text, re.S | re.M)
    assert match, f"section {heading!r} not found"
    return match.group(0)


def test_investigator_proof_plan_lists_mandatory_and_optional_fields():
    plan = _section((_AGENTS / "investigator.md").read_text(), "Proof Plan").lower()
    for field in _MANDATORY_FIELDS + _OPTIONAL_FIELDS:
        assert field in plan, field
    assert "mandatory" in plan and "optional" in plan


def test_investigator_oracle_field_only_cites_no_approval_step():
    plan = _section((_AGENTS / "investigator.md").read_text(), "Proof Plan").lower()
    assert "only *cites*" in plan
    assert "approve" in plan and "do not invent or approve" in plan
    assert "review step" not in plan


def test_architecture_reviewer_checklist_is_advisory_and_allows_clean_review():
    text = (_AGENTS / "architecture-reviewer.md").read_text()
    checklist = _section(text, "Test-quality checklist (advisory)", "###")
    assert "Advisory only" in checklist
    assert "never changes the" in checklist and "verdict" in checklist
    assert "new `NEEDS_CHANGES` trigger" in checklist
    assert "A clean review is a valid outcome" in checklist


def test_architecture_reviewer_verdict_vocabulary_unchanged():
    text = (_AGENTS / "architecture-reviewer.md").read_text()
    assert "**APPROVED / NEEDS_CHANGES / BLOCKED** verdict." in text


def test_epic_coordination_note_is_seeded_by_epic_template_and_read_by_investigator():
    assert "### Shared test fixtures and patterns" in _EPIC_JS.read_text()
    assert "### Shared test fixtures and patterns" in (_AGENTS / "investigator.md").read_text()


def test_regression_policy_has_single_triage_section_with_all_classes():
    section = _section(_POLICY.read_text(), "13. Failure-Triage Procedure")
    for cls in (
        "Product regression",
        "Test defect / wrong oracle",
        "Intentional spec change",
        "Order dependence / nondeterminism",
        "Environment / fixture",
        "Stale baseline / missing data",
        "CI selection failure",
        "Unknown",
    ):
        assert f"| {cls} |" in section, cls
    for field in ("Source", "Identity", "Reproduction", "Expected vs observed", "Rerun result"):
        assert f"| {field} |" in section, field
    assert "13.3 Prohibitions" in section and "13.4 Defects found by tests" in section


def test_delivery_process_links_to_triage_section_instead_of_restating():
    text = _DELIVERY.read_text()
    assert "docs/testing/regression_policy.md` §13" in text


def test_regression_policy_quarantine_row_is_the_bounded_policy():
    # D-MF (approved 2026-09-30) replaced the unbounded xfail(strict=False) row; the old text must be gone.
    text = _POLICY.read_text()
    assert 'xfail(strict=False, reason="flaky: <ticket>")' not in text
    assert "under review for a bounded-quarantine replacement" not in text
    assert "### 6.1 Bounded quarantine" in text
    for required in ("xfail(strict=True, raises=", "28 days from the original start date", "failure signature",
                     "No quarantine is applied until a minimal expiry check exists"):
        assert required in text
