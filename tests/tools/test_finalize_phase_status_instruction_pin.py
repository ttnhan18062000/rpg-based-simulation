"""Pin for `implement-ticket.js`'s Finalize instruction to set `phase: done` / `status: historical`
(TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT).

Investigation for that ticket found the instruction has existed since commit ff0235a71
(2026-06-12, currently around line 1671) yet ~24.6% of tickets closed via `implement-ticket.js`
after that commit still land in `tickets/done/` with non-canonical frontmatter — the fix that
ticket lands is enforcement (a cross-field validator rule + a corpus-wide test, both in
tools/validate_frontmatter.py), not more prompt text. This instruction is left unchanged, but
pinned here so a future edit can't silently drop it without a test noticing — mirrors
tests/tools/test_finalize_knowledge_index_refresh.py's established raw-source-text-parsing
pattern for this non-Python workflow file (no JS test runner exists in this repo for
.claude/workflows/*.js).
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"


def _read() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def test_finalize_instructs_phase_done_and_status_historical():
    text = _read()
    assert "set `phase: done` and `status: historical`" in text, (
        "implement-ticket.js's Finalize instruction to normalize the closing ticket's frontmatter "
        "phase/status has been changed or removed — see TCK-20260907-DONE-TICKET-FRONTMATTER-"
        "PHASE-STATUS-DRIFT investigation.md §8 for why this instruction alone is not sufficient "
        "enforcement (the validator/corpus-test rule in tools/validate_frontmatter.py is)"
    )


def test_phase_status_instruction_is_inside_finalize_phase():
    text = _read()
    finalize_start = text.find("phase('Finalize')")
    instruction_idx = text.find("set `phase: done` and `status: historical`")
    assert finalize_start != -1
    assert instruction_idx != -1
    assert finalize_start < instruction_idx, (
        "the phase/status normalization instruction must live inside the Finalize phase block"
    )


def test_phase_status_instruction_precedes_the_move_to_done():
    text = _read()
    instruction_idx = text.find("set `phase: done` and `status: historical`")
    move_idx = text.find("tickets/inprogress/${tid}.md → tickets/done/${tid}.md")
    assert instruction_idx != -1
    assert move_idx != -1
    assert instruction_idx < move_idx, (
        "frontmatter must be normalized before the ticket file is physically moved to "
        "tickets/done/, matching the location-aware validator rule's expectation of that ordering"
    )
