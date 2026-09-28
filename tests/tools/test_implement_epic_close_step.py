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
    # TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT: this pin moved from the literal
    # 'mv "${discovery.epic_ticket_path}" "tickets/done/${epicId}.md"' (the caller-side variable
    # names) to the shared buildEpicCloseInstructions() function's OWN parameter names, now that
    # both the epic_id-mode block and folder mode's own epic-parent handling call one shared
    # function instead of each hand-writing this mv. A function body's own template literal
    # necessarily uses its own parameter names, not a caller's expression text, so this rename is
    # a mechanical, unavoidable consequence of that extraction — not a change to what the check
    # proves (a `mv` into a `tickets/done/...` destination still literally exists in the source).
    # The two tests below independently confirm each call site still feeds the shared function the
    # right values, closing the gap this rename alone would otherwise leave.
    text = _read()
    assert 'mv "${epicTicketPath}" "${moveDestination}"' in text, (
        "epic-close step must physically move the epic ticket file into its moveDestination"
    )


def test_epic_id_mode_call_site_passes_a_real_move_destination():
    # Unlike folder mode (see test_folder_mode_call_site_passes_no_move_destination below),
    # epic_id mode's epic ticket has no surrounding folder of its own — this call site is the
    # only thing that ever archives it, so it must pass a real tickets/done/<epicId>.md
    # destination, not the falsy value folder mode uses to skip an individual mv.
    text = _read()
    assert (
        "buildEpicCloseInstructions(epicId, discovery.epic_ticket_path, ticketIds.length, "
        "`tickets/done/${epicId}.md`)"
    ) in text, "epic_id-mode call site must pass a real tickets/done/<epicId>.md moveDestination"


def test_folder_mode_call_site_passes_no_move_destination():
    # TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT (agent-working-design review): if
    # folder mode passed a real destination here the way epic_id mode does, the epic parent would
    # land FLAT under tickets/done/ instead of staying inside the folder the very next step
    # archives — stranding it outside both existing precedents
    # (tickets/done/mechanism-registry/TCK-20260915-EPIC-MECHANISM-REGISTRY.md,
    # tickets/done/world-rendering-core/TCK-20260820-EPIC-WORLD-RENDERING-CORE.md) and CLAUDE.md's
    # own "move the entire folder" rule. Passing a falsy 4th argument is what makes
    # buildEpicCloseInstructions emit its "do NOT move this file by itself" branch instead.
    text = _read()
    idx = text.find('Step 3 — if "epic_parent" is not null')
    assert idx != -1
    call_region = text[idx:idx + 700]
    assert "buildEpicCloseInstructions(" in call_region
    call_start = call_region.find("buildEpicCloseInstructions(")
    call_close_idx = call_region.find(")}", call_start)
    assert call_close_idx != -1, "could not find the end of the folder-mode buildEpicCloseInstructions(...) call"
    call_text = call_region[call_start:call_close_idx]
    assert re.search(r",\s*null\s*$", call_text), (
        "folder mode's call site must pass a falsy (null) moveDestination as its last argument — "
        f"no flat mv of the parent, got call text: {call_text!r}"
    )


def test_folder_cleanup_closes_epic_parent_before_moving_the_whole_folder():
    # Ordering proof (best-effort, static-text level — see this file's own module docstring on
    # the disclosed limit of these pins): the epic-parent close instructions must be textually
    # positioned, and thus dispatched, before the folder-level mv, since the parent's frontmatter
    # (phase: done/status: historical) must already be correct by the time the surrounding mv
    # carries it into tickets/done/<folder>/ — a real agent executing "Step 3... Step 4..." in
    # order satisfies this; this test cannot itself execute the .js file (no JS runtime here).
    text = _read()
    close_call_idx = text.find('Step 3 — if "epic_parent" is not null')
    folder_mv_idx = text.find('"tickets/done/${folderName}"')
    assert close_call_idx != -1
    assert folder_mv_idx != -1
    assert close_call_idx < folder_mv_idx, (
        "the epic-parent close step must be textually ordered before the folder-level mv"
    )


def test_epic_close_step_is_guarded_on_epic_id_mode():
    text = _read()
    idx = text.find("Epic ticket close (epic_id mode, all children done)")
    assert idx != -1
    guard_region = text[idx:idx + 1000]
    assert "batchStatus === 'DONE' && epicId" in guard_region, (
        "the epic-close step must be guarded on epicId, not folder -- folder mode's own "
        "epic_ticket_path is always '' because folder mode never looked for its epic parent, not "
        "because the folder can't contain one (TCK-20260915-EPIC-MECHANISM-REGISTRY.md sat inside "
        "tickets/todos/mechanism-registry/ until #209 archived it by hand). Folder mode now closes "
        "its own epic parent via the folder-cleanup block below instead "
        "(TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT) -- this guard staying on "
        "epicId only means epic_id mode's file-known-ahead-of-time close path is a separate one"
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
# The frontmatter dict passed to the validator is parsed back OUT of the written file via
# extract_frontmatter() (not hand-built) -- a first draft built the dict by hand, which meant a
# broken re.sub above (wrong anchor, unexpected spacing, count=1 hitting the wrong line) would
# have sailed through undetected, confirmed satisfying only a value the test itself asserted was
# correct (agent-working-design review). Confirmed the fix actually catches a broken rewrite
# before shipping it.
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
    from validate_frontmatter import check_ticket_location_consistency, extract_frontmatter

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

    # Parse the frontmatter back OUT of the written file -- not hand-built -- so a broken re.sub
    # (wrong anchor, unexpected spacing, count=1 hitting the wrong line) fails this assertion
    # instead of a literal-by-construction dict silently sailing through.
    written_text = dest.read_text()
    fm = extract_frontmatter(written_text)
    assert fm is not None, "expected the synthetic ticket to still have parseable frontmatter"
    assert fm.get("status") == "historical" and fm.get("phase") == "done", (
        f"the rewrite must actually produce status: historical / phase: done, got: {fm}"
    )
    errors = check_ticket_location_consistency(str(dest), fm)
    assert errors == [], f"target frontmatter values must satisfy the real validator, got: {errors}"

    body_match = re.search(r"^## Status\n(\S+)$", dest.read_text(), re.MULTILINE)
    assert body_match is not None and body_match.group(1) == "DONE", (
        "body ## Status must read DONE after the transformation, regardless of the starting value"
    )


def test_folder_mode_epic_parent_target_values_satisfy_the_real_location_validator(tmp_path):
    """AC1 (TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT): folder mode's own variant
    of the fixture-level check above -- the epic parent starts INSIDE a tickets/todos/<folder>/,
    gets closed in place (frontmatter/body only, no individual mv -- Step 3's "do NOT move this
    file by itself" branch when moveDestination is falsy), then the surrounding folder move
    (a real `mv <folder> tickets/done/<folder>/`, simulated here) carries it to
    tickets/done/<folder>/<EPIC-ID>.md. Confirms check_ticket_location_consistency() still passes
    for that NESTED done/ path, not just the flat tickets/done/<EPIC-ID>.md path the other test
    above covers -- `_ticket_directory()` only looks at the path segment immediately below
    `tickets/`, so nesting one level deeper inside an archived folder must not matter, but this is
    the one test that actually proves it rather than assuming it.
    """
    from validate_frontmatter import check_ticket_location_consistency, extract_frontmatter

    todos_folder = tmp_path / "tickets" / "todos" / "synthetic-epic-folder"
    done_folder = tmp_path / "tickets" / "done" / "synthetic-epic-folder"
    todos_folder.mkdir(parents=True)

    epic_path = todos_folder / "TCK-20260101-SYNTHETIC-EPIC.md"
    epic_path.write_text(
        _SYNTHETIC_EPIC_TEMPLATE.format(fm_status="active", fm_phase="open", body_status="EPIC_SCOPED")
    )

    # Step 2 of buildEpicCloseInstructions, applied in place (no mv -- moveDestination is falsy
    # for folder mode's call site, per test_folder_mode_call_site_passes_no_move_destination).
    text = epic_path.read_text()
    text = re.sub(r"^status:.*$", "status: historical", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^phase:.*$", "phase: done", text, count=1, flags=re.MULTILINE)
    text = re.sub(r"^## Status\n\S+$", "## Status\nDONE", text, count=1, flags=re.MULTILINE)
    epic_path.write_text(text)

    # Step 4 of the folder-cleanup prompt: move the WHOLE folder (the epic parent rides along),
    # not the epic parent individually.
    done_folder.parent.mkdir(parents=True, exist_ok=True)
    todos_folder.rename(done_folder)
    dest = done_folder / "TCK-20260101-SYNTHETIC-EPIC.md"
    assert dest.exists(), "the epic parent must have moved along with the rest of the folder"

    fm = extract_frontmatter(dest.read_text())
    assert fm is not None
    assert fm.get("status") == "historical" and fm.get("phase") == "done"
    errors = check_ticket_location_consistency(str(dest), fm)
    assert errors == [], (
        f"a nested tickets/done/<folder>/<EPIC>.md path must satisfy the real validator just like "
        f"the flat tickets/done/<EPIC>.md path does, got: {errors}"
    )
