"""Deterministic ground-truth check for the `implement-ticket.js` Plan-phase gate.

Built for TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS: the Plan phase used to decide whether to
pause for human review by substring-matching the planner agent's free-text return summary
(`planText.toLowerCase().includes('unresolved question')`). That check false-triggers on a
planner summary like "No unresolved questions: ..." since "unresolved questions" contains
"unresolved question" as a substring. This module replaces it with a check against the actual
`plan.md` file the planner wrote, which is what the planner's own prompt instructs it to flag
open questions in (a `## Unresolved Questions` heading).

TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS: the heading-presence-only version of this
check moved the same false-positive bug class one layer down instead of eliminating it — the
planner's own prompt tells it to *always* write the `## Unresolved Questions` heading, filling it
with "None." when nothing applies rather than omitting it, so a genuinely resolved plan still
false-triggered `NEEDS_HUMAN_INPUT`. `plan_has_unresolved_questions_heading` is now content-aware:
it inspects the text of the section under the heading (up to the next `##` H2 heading or EOF), not
just the heading's presence.
"""
import re

_HEADING_RE = re.compile(r"^##\s+Unresolved Questions\s*$", re.MULTILINE)
_NEXT_H2_RE = re.compile(r"^##\s+\S", re.MULTILINE)
# Word-boundary match, not a bare substring check — "None." / "None" / "none:" all count as the
# resolved word "None", but "Nonetheless, ..." must not (it isn't the same word, even though
# "Nonetheless" starts with the four characters "none").
_NONE_BODY_RE = re.compile(r"^none\b", re.IGNORECASE)


def plan_has_unresolved_questions_heading(plan_path: str) -> bool:
    """True if plan_path contains a genuine, unresolved `## Unresolved Questions` H2 section.

    Content rule: heading absent -> False. Heading present and the section body's first non-blank
    line is empty/whitespace-only, or starts with the word "None" (case-insensitive, with or
    without trailing punctuation/explanation) -> False (treated as resolved, same as a heading
    that was never written). Heading present with any other body content -> True, same as before
    this fix.

    Missing file, unreadable content, or a missing heading are all treated as no unresolved
    questions (False), never raises — mirrors this package's established fail-open convention for
    gate-check helpers.
    """
    try:
        with open(plan_path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return False

    heading_match = _HEADING_RE.search(text)
    if not heading_match:
        return False

    body = text[heading_match.end():]
    next_heading_match = _NEXT_H2_RE.search(body)
    if next_heading_match:
        body = body[:next_heading_match.start()]

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return not bool(_NONE_BODY_RE.match(stripped))

    # Heading present but the section body is empty/whitespace-only all the way to the next
    # heading (or EOF) — same as a genuine "None." body: no real unresolved question.
    return False
