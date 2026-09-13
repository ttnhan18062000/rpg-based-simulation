"""Pin for `implement-epic.js`'s epic-ticket close step
(TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING).

Before this ticket, `epic_id` mode had no equivalent of the folder-mode cleanup block: an epic
ticket's own frontmatter/body status/location were never touched by any workflow, so every epic
ticket reached `tickets/done/` by hand or in a batch commit (confirmed in this ticket's own
investigation.md, citing TCK-20260907-DONE-TICKET-FRONTMATTER-PHASE-STATUS-DRIFT's 91.7% drift
finding for `implement-epic`-run epics). The first 7 tests are raw-source-text-parsing pins,
following tests/tools/test_finalize_phase_status_instruction_pin.py's established pattern for this
non-Python workflow file (no JS test runner exists in this repo for `.claude/workflows/*.js`) --
they pin the agent PROMPT's wording, not the dispatched agent's runtime behavior (honestly
disclosed as a limitation in this ticket's own Test Summary). One additional fixture-level test
(`test_epic_close_step_target_values_satisfy_the_real_location_validator`) closes part of that gap
by applying the prompt's own specified end-state transformation to a synthetic ticket and checking
it against the real `check_ticket_location_consistency()` validator -- it still does not prove the
dispatched agent performs the transformation correctly at runtime.
"""
import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_EPIC_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-epic.js"
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


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


# ---------------------------------------------------------------------------
# Fixture-level transformation check (added post-review, agent-working-design). The 7 tests
# above are string pins over the agent PROMPT -- they never execute the close step or prove a
# real epic ticket ends up correctly transformed; they'd pass even if the dispatched agent
# ignored the prompt entirely. This test closes that gap for the one part of the transformation
# that IS pure, factorable logic: given the exact target values the prompt specifies (`phase:
# done`, `status: historical`, body `## Status: DONE`, moved to tickets/done/), does the result
# actually satisfy this repo's own real validator? It does NOT prove the dispatched agent
# performs this transformation correctly at runtime -- that remains unverified, disclosed
# honestly in the ticket's own Test Summary. TCK-20260907's `check_ticket_location_consistency()`
# corpus test remains the actual CI-enforced backstop for the frontmatter half of this; body
# `## Status` has no automated enforcement at all, pinned here only against the prompt's own
# stated target, not against runtime behavior.
# ---------------------------------------------------------------------------

_SYNTHETIC_EPIC_TEMPLATE = """---
status: {fm_status}
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260101-SYNTHETIC-EPIC
phase: {fm_phase}
date: 2026-01-01
tags: []
---

# TCK-20260101-SYNTHETIC-EPIC

## Title
Synthetic epic for fixture-level close-step verification

## Status
{body_status}

## Tier
epic
"""


@pytest.mark.parametrize("body_status", ["EPIC_SCOPED", "OPEN", "DONE"])
def test_epic_close_step_target_values_satisfy_the_real_location_validator(tmp_path, body_status):
    """Simulates the exact end state the close-step prompt specifies (Step 2/Step 3 of the
    epic-close block) against a synthetic epic ticket starting from each observed real-corpus
    drift shape (EPIC_SCOPED, OPEN, and already-DONE as a no-op control), then asserts the
    result satisfies validate_frontmatter.py's real check_ticket_location_consistency() -- the
    same function TCK-20260907's own corpus test runs over all of tickets/done/ at CI.
    """
    from validate_frontmatter import check_ticket_location_consistency

    inprogress_dir = tmp_path / "tickets" / "inprogress"
    done_dir = tmp_path / "tickets" / "done"
    inprogress_dir.mkdir(parents=True)
    done_dir.mkdir(parents=True)

    source = inprogress_dir / "TCK-20260101-SYNTHETIC-EPIC.md"
    source.write_text(
        _SYNTHETIC_EPIC_TEMPLATE.format(fm_status="active", fm_phase="open", body_status=body_status)
    )

    # Apply exactly what Step 2/Step 3 of the close-step prompt specifies: frontmatter ->
    # historical/done, body ## Status -> DONE (unconditionally), then move to tickets/done/.
    text = source.read_text()
    text = re.sub(r"^status:.*$", "status: historical", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^phase:.*$", "phase: done", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^## Status\n\S+$", "## Status\nDONE", text, count=1, flags=re.MULTILINE)
    dest = done_dir / "TCK-20260101-SYNTHETIC-EPIC.md"
    dest.write_text(text)
    source.unlink()

    fm = {"status": "historical", "phase": "done"}
    errors = check_ticket_location_consistency(str(dest), fm)
    assert errors == [], f"target frontmatter values must satisfy the real validator, got: {errors}"

    body_match = re.search(r"^## Status\n(\S+)$", dest.read_text(), re.MULTILINE)
    assert body_match is not None and body_match.group(1) == "DONE", (
        "body ## Status must read DONE after the transformation, regardless of the starting value"
    )
