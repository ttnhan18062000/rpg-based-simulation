"""Pin for `implement-epic.js`'s epic-ticket close step
(TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING).

Before this ticket, `epic_id` mode had no equivalent of the folder-mode cleanup block: an epic
ticket's own frontmatter/body status/location were never touched by any workflow, so every epic
ticket reached `tickets/done/` by hand or in a batch commit (confirmed in this ticket's own
investigation.md, citing TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT's 91.7% drift
finding for `implement-epic`-run epics). This is a raw-source-text-parsing pin, following
tests/tools/test_finalize_phase_status_instruction_pin.py's established pattern for this
non-Python workflow file (no JS test runner exists in this repo for `.claude/workflows/*.js`).
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_EPIC_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-epic.js"


def _read() -> str:
    return _IMPLEMENT_EPIC_PATH.read_text(encoding="utf-8")


def test_epic_close_step_sets_phase_done_and_status_historical():
    text = _read()
    # The source file escapes backticks inside its own outer template literal
    # (`\`phase: done\`` on disk), so the raw text search must match that literal escaping.
    assert r"set \`phase: done\` and \`status: historical\`" in text, (
        "the epic-close step must set the same canonical frontmatter values "
        "check_ticket_location_consistency() requires for tickets/done/"
    )


def test_epic_close_step_sets_body_status_done_not_epic_scoped():
    text = _read()
    idx = text.find("Set the body ## Status section to DONE")
    assert idx != -1, "epic-close step must instruct writing body ## Status: DONE"
    # EPIC_SCOPED is allowed to appear nearby only as explanatory contrast for why DONE (not
    # EPIC_SCOPED) is the value actually written -- confirm the instructed value itself is DONE.
    surrounding = text[idx:idx + 400]
    assert "EPIC_SCOPED" in surrounding, (
        "the instruction should explain why DONE was chosen over EPIC_SCOPED, per "
        "investigation.md §4 -- if this explanatory contrast disappears, a future edit may have "
        "silently reverted to the wrong canonical value"
    )
    assert "Set the body ## Status section to DONE" in surrounding


def test_epic_close_step_moves_file_to_tickets_done():
    text = _read()
    assert 'mv "${discovery.epic_ticket_path}" "tickets/done/${epicId}.md"' in text, (
        "epic-close step must physically move the epic ticket file into tickets/done/"
    )


def test_epic_close_step_is_guarded_on_epic_id_mode():
    text = _read()
    idx = text.find("Epic ticket close (epic_id mode, all children done)")
    assert idx != -1
    guard_region = text[idx:idx + 1000]
    assert "batchStatus === 'DONE' && epicId" in guard_region, (
        "the epic-close step must be guarded on epicId, not folder -- folder mode has no epic "
        "ticket file at all (its own epic_ticket_path is always '')"
    )


def test_epic_close_step_runs_after_folder_cleanup_and_before_report_phase():
    text = _read()
    folder_cleanup_guard_idx = text.find("if (batchStatus === 'DONE' && folder)")
    epic_close_guard_idx = text.find("if (batchStatus === 'DONE' && epicId)")
    report_phase_idx = text.find("phase('Report')")
    assert folder_cleanup_guard_idx != -1
    assert epic_close_guard_idx != -1
    assert report_phase_idx != -1
    assert folder_cleanup_guard_idx < epic_close_guard_idx < report_phase_idx, (
        "epic-close must run after the existing folder-cleanup step and before Report, matching "
        "where the batch's own 'all children done' state (batchStatus) is already known"
    )


def test_epic_close_step_is_a_bookkeeping_step_that_never_fails_the_workflow():
    text = _read()
    idx = text.find("Epic ticket close (epic_id mode, all children done)")
    assert idx != -1
    block = text[idx:idx + 2000]
    assert "This is bookkeeping" in block and "do NOT fail the workflow" in block, (
        "epic-close must follow the same bookkeeping convention as the existing folder-cleanup "
        "and batch-monitoring-write steps -- a failure here must never block the batch result"
    )


def test_epic_close_step_uses_a_fresh_negative_sidecar_seq():
    text = _read()
    # Every existing negative writeSidecar seq in this file, confirmed by direct grep before
    # picking -5 for the new step (see plan.md Step 1) -- pin that no collision was introduced.
    assert "writeSidecar(-1, 'Discover', 'discover')" in text
    assert "writeSidecar(-2, 'Implement', 'batch-monitoring-write')" in text
    assert "writeSidecar(-3, 'Implement', 'folder-cleanup')" in text
    assert "writeSidecar(-4, 'Report', 'tracking-doc-update')" in text
    assert "writeSidecar(-5, 'Implement', 'epic-close')" in text
