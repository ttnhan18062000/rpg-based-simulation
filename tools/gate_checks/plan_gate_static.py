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
import argparse
import re
import sys
from pathlib import Path

# The heading may carry a qualifier introduced by punctuation, e.g. "## Unresolved Questions (decide
# before the implementer runs; do not decide in-plan)" or "## Unresolved Questions: owner decisions"
# (TCK-20260930-PLAN-GATE-HEADING-SUFFIX-FALSE-NEGATIVE: the bare-heading-only form let a real plan
# with 3 open owner decisions through the gate, silently, because this module is fail-open). A plain
# word after the title ("## Unresolved Questions Resolved Later") is deliberately NOT matched: it
# reads as a different section, and the planner is told to flag open questions "under 'Unresolved
# Questions'", not to qualify the title with prose.
_HEADING_RE = re.compile(r"^##\s+Unresolved Questions(?:[ \t]*[(:\[\u2013\u2014-].*)?[ \t]*$", re.MULTILINE)
_NEXT_H2_RE = re.compile(r"^##\s+\S", re.MULTILINE)
# Word-boundary match, not a bare substring check — "None." / "None" / "none:" all count as the
# resolved word "None", but "Nonetheless, ..." must not (it isn't the same word, even though
# "Nonetheless" starts with the four characters "none").
_NONE_BODY_RE = re.compile(r"^none\b", re.IGNORECASE)

# Markdown decoration a planner may wrap "None." in: emphasis (*, _), code (`), list/quote
# markers (-, +, >). Stripped before the word-boundary match so "**None.**", "_None_", "`None`" and
# "- None" read as the resolved word, exactly like a plain "None." (TCK-20261004). The match itself is
# not loosened: "Nonetheless" and "- Which owner decides X?" still read as open.
_MARKUP = " \t*_`-+>"


def _strip_markup(line: str) -> str:
    # Both ends: a trailing "_" is a word character, so "_None_" has no word boundary after "None".
    return line.strip(_MARKUP)


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
        return not bool(_NONE_BODY_RE.match(_strip_markup(stripped)))

    # Heading present but the section body is empty/whitespace-only all the way to the next
    # heading (or EOF) — same as a genuine "None." body: no real unresolved question.
    return False


def main(argv=None) -> int:
    """Thin CLI so a hand closure can run the Plan gate and have the verdict recorded
    (TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES). Exit 1 when the plan has unresolved questions."""
    parser = argparse.ArgumentParser(description="Plan gate: does plan.md carry a genuine `## Unresolved Questions` section?")
    parser.add_argument("--plan-path", required=True)
    parser.add_argument("--ticket-id", default=None)
    parser.add_argument("--no-record", action="store_true", help="Do not write this verdict to the gate_verdicts shard.")
    args = parser.parse_args(argv)
    unresolved = plan_has_unresolved_questions_heading(args.plan_path)
    print(f"{'FAIL' if unresolved else 'PASS'}: {args.plan_path} "
          f"{'has' if unresolved else 'has no'} unresolved questions")
    monitoring_dir = str(Path(__file__).resolve().parents[1] / "agent-monitoring")
    if monitoring_dir not in sys.path:
        sys.path.insert(0, monitoring_dir)
    import gate_verdicts  # noqa: PLC0415 - kept out of module import: the gate function is imported by the pipeline
    gate_verdicts.record_gate_verdict(
        enabled=not args.no_record,
        gate_id=gate_verdicts.gate_id_for("plan_gate_static", "plan_has_unresolved_questions_heading"),
        gate_type="static_check",
        phase="Plan",
        verdict="FAIL" if unresolved else "PASS",
        blocking=unresolved,
        ticket_id=args.ticket_id,
        inputs_ref={"head_sha": gate_verdicts.head_sha(), "cmd_sha": gate_verdicts.sha256_hex(args.plan_path)},
    )
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
