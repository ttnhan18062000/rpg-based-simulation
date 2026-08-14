"""Deterministic ground-truth check for the `implement-ticket.js` Plan-phase gate.

Built for TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS: the Plan phase used to decide whether to
pause for human review by substring-matching the planner agent's free-text return summary
(`planText.toLowerCase().includes('unresolved question')`). That check false-triggers on a
planner summary like "No unresolved questions: ..." since "unresolved questions" contains
"unresolved question" as a substring. This module replaces it with a check against the actual
`plan.md` file the planner wrote, which is what the planner's own prompt instructs it to flag
open questions in (a `## Unresolved Questions` heading).
"""
import re

_HEADING_RE = re.compile(r"^##\s+Unresolved Questions\s*$", re.MULTILINE)


def plan_has_unresolved_questions_heading(plan_path: str) -> bool:
    """True if the file at plan_path contains a genuine `## Unresolved Questions` H2 heading.

    Missing file or unreadable content is treated as no heading (False), never raises — mirrors
    this package's established fail-open convention for gate-check helpers.
    """
    try:
        with open(plan_path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return False
    return bool(_HEADING_RE.search(text))
