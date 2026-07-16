"""Tests for tools/gate_checks/plan_gate_static.py
(TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS).

Reproduces the exact false-positive that motivated this module: a planner return summary
containing "No unresolved questions" (which the old `planText.includes('unresolved question')`
check wrongly matched) must NOT be what this check looks at — it must look at the real plan.md
file for a genuine `## Unresolved Questions` heading instead.
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
