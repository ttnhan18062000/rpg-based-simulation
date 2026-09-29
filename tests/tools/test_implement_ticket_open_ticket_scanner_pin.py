"""Pin for `.claude/workflows/implement-ticket.js`'s Scope phase open-ticket overlap scanner
wiring, both paths (TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER).

Mirrors `test_finalize_working_log_uses_helper_pin.py`'s raw-source-text-parsing pattern (no JS
test runner exists in this repo for `.claude/workflows/*.js` files).
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"


def _read() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# New-ticket Scope path
# ---------------------------------------------------------------------------

_NEW_TICKET_OPEN_ANCHOR = "Create a new ticket for this request using the ticket-scoper role."
_NEW_TICKET_CLOSE_ANCHOR = "2. Scan docs/ (mechanics Bible chapters, engine contracts)"


def _new_ticket_scope_text() -> str:
    text = _read()
    open_idx = text.find(_NEW_TICKET_OPEN_ANCHOR)
    close_idx = text.find(_NEW_TICKET_CLOSE_ANCHOR)
    assert open_idx != -1, "new-ticket Scope prompt's opening anchor not found — has it moved or been reworded?"
    assert close_idx != -1, "new-ticket Scope prompt's Step 2 anchor not found — has it moved or been reworded?"
    assert open_idx < close_idx, "opening anchor must precede closing anchor"
    return text[open_idx:close_idx]


def test_new_ticket_scope_step_1_scans_todos_via_the_scanner():
    step_1 = _new_ticket_scope_text()
    assert "tickets/todos/" in step_1, (
        "new-ticket Scope Step 1 no longer mentions tickets/todos/ — "
        "see TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER"
    )
    assert "open_ticket_overlap.py" in step_1, (
        "new-ticket Scope Step 1 no longer calls tools/open_ticket_overlap.py — "
        "see TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER"
    )


def test_new_ticket_scope_step_1_routes_todos_hits_to_related_context_not_conflicts():
    step_1 = _new_ticket_scope_text()
    assert "tickets/todos/ scanner hit always goes to related_context, never conflicts" in step_1


# ---------------------------------------------------------------------------
# Existing-ticket Scope path
# ---------------------------------------------------------------------------

_EXISTING_TICKET_OPEN_ANCHOR = "Load the existing ticket."
_EXISTING_TICKET_CONFLICTS_LINE = 'conflicts=(["ticket file not found for ${ticketId}"] if ticket_path is empty, else []),'
_EXISTING_TICKET_CLOSE_ANCHOR = "related_context=(any non-blocking informational findings noticed while loading the ticket, [] if none),"


def _existing_ticket_scope_text() -> str:
    text = _read()
    open_idx = text.find(_EXISTING_TICKET_OPEN_ANCHOR)
    close_idx = text.find(_EXISTING_TICKET_CLOSE_ANCHOR)
    assert open_idx != -1, "existing-ticket Scope prompt's opening anchor not found — has it moved or been reworded?"
    assert close_idx != -1, "existing-ticket Scope prompt's related_context= line not found byte-identical — has it changed?"
    assert open_idx < close_idx, "opening anchor must precede closing anchor"
    return text[open_idx:close_idx + len(_EXISTING_TICKET_CLOSE_ANCHOR)]


def test_existing_ticket_scope_runs_the_scanner_before_the_related_context_output_field():
    scope_text = _existing_ticket_scope_text()
    scanner_idx = scope_text.find("open_ticket_overlap.py")
    related_context_field_idx = scope_text.find("related_context=(any non-blocking informational findings")
    assert scanner_idx != -1, (
        "existing-ticket Scope prompt no longer calls tools/open_ticket_overlap.py — "
        "see TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER"
    )
    assert related_context_field_idx != -1, "related_context= output field instruction not found — has it moved?"
    assert scanner_idx < related_context_field_idx, (
        "the scanner call must be instructed before the related_context= output field so its "
        "hits can actually be folded in"
    )


def test_existing_ticket_scope_conflicts_field_unchanged_by_the_scanner_wiring():
    assert _EXISTING_TICKET_CONFLICTS_LINE in _read(), (
        "the conflicts= output field line changed — it must stay exactly "
        '\'conflicts=(["ticket file not found for ${ticketId}"] if ticket_path is empty, else []),\' '
        "so scanner hits never flow into it (see TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER)"
    )
