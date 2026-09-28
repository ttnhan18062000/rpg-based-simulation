"""Pin for `implement-ticket.js`'s Finalize step 3 epic-parent advisory
(TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT).

Before this ticket, step 3's folder-cleanup check ("if other TCK-*.md files still exist in the
folder: skip") could never distinguish a genuinely unfinished sibling ticket from the folder's own
epic-tier parent -- which never closes on its own, since implement-ticket.js only ever closes the
ticket it was invoked for, never a different ticket's lifecycle. This left every finished epic
folder silently un-archived forever (see that ticket's Request Summary for two real cases:
TCK-20260820-EPIC-WORLD-RENDERING-CORE, mechanism-registry). The fix is a visible advisory, not a
silent close from inside a child ticket's own Finalize -- implement-epic.js's own folder-cleanup
block (see tests/tools/test_implement_epic_close_step.py) is the sanctioned place that actually
closes an epic parent.

Raw-source-text-parsing pin, following test_finalize_phase_status_instruction_pin.py's established
pattern for this non-Python workflow file (no JS test runner exists in this repo for
.claude/workflows/*.js) -- pins the agent PROMPT's wording, not the dispatched agent's runtime
behavior.

Step 3 calls the shared `tools/epic_folder_status.py` helper (also used by
`implement-epic.js`'s own folder-cleanup block -- see test_implement_epic_close_step.py) rather
than an inline `python3 -c` script, per `test_finalize_working_log_uses_helper_pin.py`'s own
blanket "no inline Python source in the Finalize prompt" guard, which an earlier draft of this
ticket's fix tripped.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"


def _read() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def test_finalize_step3_detects_epic_parent_structurally_not_by_filename():
    text = _read()
    idx = text.find("Remove the todos source file")
    assert idx != -1
    step3 = text[idx:idx + 1500]
    assert "epic_folder_status.py" in step3, (
        "step 3 must call the shared tools/epic_folder_status.py helper, not an inline python3 -c "
        "script (test_finalize_working_log_uses_helper_pin.py's own blanket guard rejects that) "
        "or a filename-based check"
    )
    assert "never by filename match on" in step3 and "-EPIC-" in step3, (
        "the epic-parent check must identify the remaining ticket via its own ## Tier/## Status "
        "body fields, not a filename convention -- a filename check would miss a real epic ticket "
        "named without '-EPIC-' in its ID and false-positive on a non-epic ticket that happens to "
        "contain it"
    )


def test_finalize_step3_never_closes_the_epic_parent_itself():
    text = _read()
    idx = text.find("Remove the todos source file")
    assert idx != -1
    step3 = text[idx:idx + 1500]
    assert "do NOT close or move" in step3, (
        "implement-ticket.js's own Finalize must never close a different ticket's (the epic "
        "parent's) lifecycle from inside this ticket's own Finalize step -- that is "
        "implement-epic.js's job (epic_id mode, or its own folder-cleanup block)"
    )


def test_finalize_step3_prints_the_advisory_message():
    text = _read()
    assert "All children of <FOLDER> are done; epic parent <EPIC-ID> remains" in text
    assert "close it via" in text
    assert "implement-epic (epic_id mode) or by hand." in text, (
        "the advisory must name both a concrete next step (implement-epic epic_id mode) and the "
        "manual fallback"
    )


def test_finalize_step3_advisory_is_inside_finalize_phase():
    text = _read()
    finalize_start = text.find("phase('Finalize')")
    advisory_idx = text.find("epic parent <EPIC-ID> remains")
    assert finalize_start != -1
    assert advisory_idx != -1
    assert finalize_start < advisory_idx, "the advisory must be inside the Finalize phase's own prompt text"


def test_finalize_step3_still_moves_a_non_epic_folder_when_no_tck_files_remain():
    # AC3's other half: the pre-existing, unrelated behavior (a folder whose last child just
    # closed, with no epic parent at all) must be unchanged in outcome, even though the mechanism
    # (an ls-based check) was replaced by the shared epic_folder_status.py helper's JSON output.
    text = _read()
    idx = text.find("Remove the todos source file")
    assert idx != -1
    step3 = text[idx:idx + 1500]
    assert '"all_children_done" is true and "epic_parent" is null' in step3, (
        "a folder with no epic-tier ticket must still move once every child is done -- the same "
        "outcome the old ls-based check produced, now driven by epic_folder_status.py's JSON"
    )
    assert "Run: mv <parent-dir>/ tickets/done/<FOLDER>/" in step3
    assert '"all_children_done" is false' in step3, (
        "an unfinished (non-epic) folder must still skip, same as before"
    )
