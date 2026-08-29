"""Tests for tools/gate_checks/plan_gate_static.py
(TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS, TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS).

Reproduces the exact false-positive that motivated this module: a planner return summary
containing "No unresolved questions" (which the old `planText.includes('unresolved question')`
check wrongly matched) must NOT be what this check looks at — it must look at the real plan.md
file for a genuine `## Unresolved Questions` heading instead.

The heading-presence-only version of this check itself turned out to have the same false-positive
bug class one layer down (TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS): the planner's
own prompt always writes the heading, filling it with "None." when there is nothing to flag rather
than omitting it, so a genuinely resolved plan still false-triggered `NEEDS_HUMAN_INPUT`. The
`test_heading_with_*` tests below cover the content-aware fix for that.
"""
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.plan_gate_static import plan_has_unresolved_questions_heading  # noqa: E402


def test_true_positive_genuine_heading(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## Steps\n\nSome content.\n\n## Unresolved Questions\n\n- What should X do?\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is True


def test_false_positive_prose_no_unresolved_questions_does_not_match(tmp_path):
    """The exact scenario that motivated this ticket: a planner's own prose stating there are
    NO unresolved questions must not be mistaken for a real heading. The old substring check on
    the agent's free-text summary would have matched "unresolved questions" here; this
    file-based check must not, since there is no `## Unresolved Questions` heading in the file."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## Decision\n\n"
        "No unresolved questions: both open items were decided in the plan's Decision "
        "section using the ticket's own Scope text as authority.\n"
    )
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_no_heading_at_all(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## Steps\n\nJust ordinary plan content, no mention of questions.\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_h3_heading_does_not_match_h2_only_contract(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("### Unresolved Questions\n\n- Not an H2, should not match.\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_heading_with_trailing_whitespace_matches(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## Unresolved Questions   \n\n- trailing spaces after heading text\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is True


def test_missing_file_returns_false_not_raise(tmp_path):
    missing = tmp_path / "does_not_exist.md"
    assert plan_has_unresolved_questions_heading(str(missing)) is False


def test_heading_with_bare_none_and_period_returns_false(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## Steps\n\nSome content.\n\n## Unresolved Questions\n\nNone.\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_heading_with_bare_none_no_trailing_punctuation_returns_false(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## Unresolved Questions\n\nNone\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_heading_with_none_and_explanation_returns_false(tmp_path):
    """The exact real-world scenario from TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS
    (found live during TCK-20260824-OCCUPATION-CHANGE-TRIGGER): a genuinely resolved plan whose
    body reads "None. <explanation of what was checked and resolved>..." must not false-trigger."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## Unresolved Questions\n\n"
        "None. The one question investigation.md flagged as a potential blocker for this plan "
        "was checked directly during planning and resolved: it does not apply.\n"
    )
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_heading_with_none_case_insensitive_returns_false(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## Unresolved Questions\n\nnone.\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_heading_with_only_whitespace_body_before_next_heading_returns_false(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## Unresolved Questions\n\n   \n\n\n## Next Section\n\nSomething else.\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_heading_with_only_whitespace_body_to_eof_returns_false(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## Unresolved Questions\n\n   \n")
    assert plan_has_unresolved_questions_heading(str(plan)) is False


def test_heading_with_real_content_still_returns_true(tmp_path):
    """Sibling case to the "None." tests above: heading present with genuine open-question
    content must still gate to True, same as before this fix."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## Unresolved Questions\n\n- Should X use approach A or B? Needs human input.\n"
    )
    assert plan_has_unresolved_questions_heading(str(plan)) is True


def test_heading_with_none_prefixed_word_not_treated_as_resolved(tmp_path):
    """"Nonetheless" starts with the four characters "none" but is not the word "None" — the
    content rule matches on the word, not a bare character-prefix substring, so this must still
    gate to True."""
    plan = tmp_path / "plan.md"
    plan.write_text("## Unresolved Questions\n\nNonetheless, X is unresolved: should Y happen?\n")
    assert plan_has_unresolved_questions_heading(str(plan)) is True
