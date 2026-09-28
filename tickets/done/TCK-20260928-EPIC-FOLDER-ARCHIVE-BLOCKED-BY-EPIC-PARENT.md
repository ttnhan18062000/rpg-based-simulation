---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT
phase: done
date: 2026-09-28
tags: [process-improvement]
---

# TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT

## Title

Both folder-archive steps (implement-ticket.js Finalize step 3, implement-epic.js folder-cleanup)
require every `TCK-*.md` in a `tickets/todos/<folder>/` to be done, but the folder's own epic parent
never is, so neither step can archive an epic folder.

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P3

## Request Summary

Found while scoping `TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS`. The resurrection itself
was not caused by this, but the same folders expose it.

- `.claude/workflows/implement-ticket.js` Finalize step 3 (~line 1738, text at `origin/main`
  `9bcae32c5`) says: "If no TCK-*.md files remain (folder is empty or has only SEQUENCE.md /
  non-ticket files): mv <parent-dir>/ tickets/done/<FOLDER>/ … If other TCK-*.md files still exist
  in the folder: skip". An epic folder always still holds its epic-tier parent
  (`TCK-*-EPIC-*.md`, `## Status` `EPIC_SCOPED`), which no child close removes. The step therefore
  always skips for an epic folder.
- `.claude/workflows/implement-epic.js` folder-cleanup block (~line 409) says: "If any TCK-*.md
  file is NOT in tickets/done/ … print 'SKIPPED: unfinished tickets still in folder'". This is the
  same check with the same blocker: the epic parent is in the folder and not in `done/`. The
  `epic_id`-mode close step (`TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING`) closes an epic
  ticket, but only in `epic_id` mode. Folder mode's `epic_ticket_path` is always "".

The consequence is that every finished epic folder is archived by hand. Known cases:
`TCK-20260820-EPIC-WORLD-RENDERING-CORE` (manual close-out) and `mechanism-registry` (archived by
hand in #209 `8ab22a916`). Until someone notices, the epic-staleness hook nags a finished epic.

**Constraint any fix must respect:** moving a folder puts its epic parent under `tickets/done/`.
`check_ticket_location_consistency` (and its corpus test) then requires `status: historical`,
`phase: done` and a real close. So the epic parent must be **closed** (status, frontmatter,
working_log row, monitoring) before or as part of the move. It must never simply be moved while open.

## Scope

1. First, verify the implement-epic folder-mode claim above against `tests/tools/test_implement_epic_close_step.py`
   and the workflow text on the branch. If folder mode already handles the epic parent somewhere
   this ticket missed, record that and limit the fix to implement-ticket.js.
2. **implement-epic.js folder mode:** in the folder-cleanup check, exclude the folder's epic-tier
   parent from the "all TCK-*.md must be in done/" requirement. When every non-epic ticket is done,
   close that epic parent by reusing the existing `epic_id`-mode epic-close step's instructions
   (same helper or the same prompt block, not a second hand-written close), then move the folder.
3. **implement-ticket.js Finalize step 3:** when the only `TCK-*.md` left in the folder is the epic
   parent, do **not** close the epic from inside a child ticket's Finalize, which would be a
   different ticket's lifecycle. Print an explicit advisory instead:
   "All children of <folder> are done; epic parent <EPIC-ID> remains — close it via implement-epic
   (epic_id mode) or by hand." That turns today's silent skip into a visible next step.
4. Identify the epic parent structurally: `## Tier` `epic` (or `## Status` `EPIC_SCOPED`), read
   through `tools/ticket_field_values.py`'s parsing, not a filename match on `-EPIC-`.
5. **Retro cadence:** this changes workflow prompts. Regenerate the W39 retro before the prompt
   commit, as done for `TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS`.

## Out of Scope

- Closing `tickets/todos/progression-starvation-chain/`. That epic is genuinely open.
- Back-filling a close for any past epic that was archived by hand.

## Acceptance Criteria

- AC1: Given a synthetic folder with an `EPIC_SCOPED` parent, `SEQUENCE.md` and N children that
  are all in `done/`, implement-epic folder mode's cleanup closes the parent and moves the folder.
  Afterwards the location-consistency check passes for the moved parent.
- AC2: Given the same folder with one child not yet done, the cleanup still skips.
- AC3: implement-ticket Finalize step 3's text emits the advisory in the epic-parent-only case, and
  still moves a non-epic folder when no TCK files remain.
- AC4: The retro is regenerated before the prompt commit; bare `pytest tests/tools/` passes.

## Related Tickets

- `TCK-20260911-IMPLEMENT-EPIC-CLOSE-STEP-MISSING`: the epic_id-mode close step to reuse.
- `TCK-20260820-EPIC-WORLD-RENDERING-CORE`: a prior manual close-out of this class.
- `TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS`: where this was found; a different cause.

## Related Docs

- `CLAUDE.md` "After Work" folder-move bullet. It states the rule ("when **all** tickets in the
  folder are done") and needs no change: the epic parent is closed as part of that.

## Related Stored Artifacts

None.

## Related Code Areas

- `.claude/workflows/implement-ticket.js` (Finalize step 3)
- `.claude/workflows/implement-epic.js` (folder-cleanup block, epic-close block)
- `tests/tools/test_implement_epic_close_step.py`
- `tools/ticket_field_values.py`

## Assumptions / Open Questions

- Assumes the epic-close step's instructions can be shared between the two implement-epic modes
  without behaviour change for `epic_id` mode. If they can't, stop and report rather than fork a
  second close path.

## Implementation Notes

- **Scope item 1 verification**: confirmed the claim directly against
  `tests/tools/test_implement_epic_close_step.py::test_epic_close_step_is_guarded_on_epic_id_mode`,
  which already asserted the epic-close block is guarded on `epicId`, not `folder` — folder mode
  had zero mechanism to close an epic parent. Not limited to `implement-ticket.js` — both files
  needed the fix as scoped.
- **implement-epic.js**: extracted a shared `buildEpicCloseInstructions(epicIdValue,
  epicTicketPath, childCount, moveDestination)` function, called by both the pre-existing
  `epic_id`-mode close block (unchanged guard/behavior) and folder mode's own new epic-parent
  handling inside the folder-cleanup block — one template, not a second hand-written close.
  Folder mode identifies the epic parent structurally via `generate_registry.parse_body_section`
  on `## Tier`, never by filename match on `-EPIC-` (Scope item 4).
- **Real bug caught by agent-working-design's review before this shipped**: the first version of
  `buildEpicCloseInstructions` always did an individual `mv <path> tickets/done/<id>.md`. For
  folder mode that would have stranded the epic parent flat under `tickets/done/`, outside the
  folder the very next step archives — contradicting both real precedents
  (`tickets/done/mechanism-registry/TCK-20260915-EPIC-MECHANISM-REGISTRY.md`,
  `tickets/done/world-rendering-core/TCK-20260820-EPIC-WORLD-RENDERING-CORE.md`) and CLAUDE.md's
  "move the entire folder" rule. Fixed by adding a `moveDestination` parameter: `epic_id` mode
  passes a real `tickets/done/${epicId}.md` destination (unchanged from before); folder mode
  passes `null`, which selects the function's "close in place, no individual mv" branch — the
  epic parent's frontmatter/body update lands on the file at its existing path inside the folder,
  and the folder-level `mv` (a separate, later step) carries it into `tickets/done/<folder>/` in
  one operation, exactly matching the precedents.
- **implement-ticket.js Finalize step 3**: when exactly one `TCK-*.md` remains in the folder,
  checks whether it is the epic-tier parent (same structural `## Tier` check, never filename).
  If so: prints the advisory `"All children of <FOLDER> are done; epic parent <EPIC-ID> remains —
  close it via implement-epic (epic_id mode) or by hand."` and does not touch the folder — closing
  a different ticket's own lifecycle from inside this ticket's Finalize would be exactly the kind
  of cross-ticket mutation the project's Durable State Rule warns against. A folder with no epic
  parent (the pre-existing, unrelated case) behaves exactly as before.
- **Test-pin fallout from the shared-function extraction, resolved with agent-working-design**:
  extracting `buildEpicCloseInstructions` necessarily changed the exact literal `mv` command text
  a pre-existing test pinned (a function body's own template literal uses its own parameter names,
  not a caller's expression text — there is no way to keep the old literal string AND have one
  real shared function). Re-pinned `test_epic_close_step_moves_file_to_tickets_done` to the shared
  function's own parameter names after explicit confirmation this is a mechanical consequence of
  the requested refactor, not an independent test-logic call — added two new tests
  (`test_epic_id_mode_call_site_passes_a_real_move_destination`,
  `test_folder_mode_call_site_passes_no_move_destination`) proving each call site still feeds the
  shared function the right arguments, closing the gap the rename alone would have left.
- Also corrected, per explicit pre-authorization (assertion itself left byte-identical):
  `test_epic_close_step_is_guarded_on_epic_id_mode`'s failure MESSAGE claimed folder mode "has no
  epic ticket file at all" — false as a premise (`tickets/todos/mechanism-registry/` held
  `TCK-20260915-EPIC-MECHANISM-REGISTRY.md` until #209 archived it by hand); the true reason is
  that folder mode never looked for it, now fixed by this ticket.
- Two more tests added for the flat-mv fix specifically:
  `test_folder_cleanup_closes_epic_parent_before_moving_the_whole_folder` (textual ordering proof
  — same disclosed static-text-pin limitation this whole file already carries, no JS runtime
  exists here to execute the actual logic) and
  `test_folder_mode_epic_parent_target_values_satisfy_the_real_location_validator` (a real
  fixture-level proof: writes a synthetic epic parent inside a synthetic `tickets/todos/<folder>/`,
  applies the close-in-place transformation, renames the whole folder the way Step 4 does, and
  confirms `check_ticket_location_consistency()` passes for the resulting nested
  `tickets/done/<folder>/<EPIC>.md` path — satisfies AC1's own explicit requirement).
- Both `.claude/workflows/*.js` files pass `node --check` (syntax only — no JS test runner exists
  in this repo to execute their actual runtime logic, an existing, honestly-disclosed limitation
  of every test in this family).
- **Retro cadence (Scope item 5)**: regenerated `agent-monitoring/retro/RETRO-2026-W39.md` before
  this commit, matching the precedent set by `TCK-20260927-PHASE-PROMPTS-OMIT-GATE-PRECONDITIONS`.
  Regenerated with `--week 2026-W39` explicitly — the calendar rolled into ISO week 40 partway
  through this same session (2026-09-28 is a Monday), so the no-argument "current week" default
  would have produced W40 instead of the week this batch's own work actually happened in.

- **Second gate collision, also resolved with agent-working-design**: the first version of both
  workflow prompts identified the epic parent via an inline `python3 -c "...parse_body_section..."`
  one-liner. This tripped
  `test_finalize_working_log_uses_helper_pin.py::test_finalize_prompt_never_reintroduces_inline_python_source_embedding`
  — a blanket "no `python3 -c` anywhere in the Finalize agent's own prompt" guard
  (TCK-20260912-WORKING-LOG-APPEND-HELPER's own precedent). Rather than rescope that test (wrong
  direction to narrow a gate on the commit that trips it) or dodge it with a heredoc (the exact
  substring-matching technicality it exists to prevent), extracted a real committed helper instead
  — `tools/epic_folder_status.py`, with a pure `get_epic_folder_status()` function and a real
  argparse `main()` CLI, following the same "Finalize calls a committed helper, never inline
  Python" pattern the origin ticket itself established. Both workflows now call
  `python3 tools/epic_folder_status.py <folder>` and branch on its JSON output
  (`epic_parent`/`epic_parent_ticket_id`/`open_children`/`all_children_done`) — no `python3 -c` in
  either prompt. The pin test passes unchanged, byte-identical assertion.
- Re-anchored several of this ticket's own new text-pin tests (in
  `test_implement_epic_close_step.py` and `test_finalize_epic_parent_advisory_pin.py`) to the
  reworded, helper-based step text — same class of mechanical fallout as the `moveDestination`
  rename above, not a logic change.

## Test Summary

- `pytest tests/tools/test_implement_epic_close_step.py -v` — 14 passed.
- `pytest tests/tools/test_finalize_epic_parent_advisory_pin.py -v` — 5 passed (new file).
- `pytest tests/tools/test_epic_folder_status.py -v` — 8 passed (new file): epic-parent-only (all
  children done), one open child, non-epic folder with no parent, epic identified via `## Tier`
  even without `-EPIC-` in its filename, a non-epic ticket NOT misclassified despite `-EPIC-`
  appearing in ITS filename, CLI in-process + a real subprocess invocation (matching how the
  workflow prompts actually call it), and the default `--done-dir` resolution.
- `node --check .claude/workflows/implement-epic.js` and `node --check
  .claude/workflows/implement-ticket.js` — both exit 0.
- Addendum (`stale_child_copies` fix): `pytest tests/tools/test_implement_epic_close_step.py
  tests/tools/test_finalize_epic_parent_advisory_pin.py tests/tools/test_epic_folder_status.py`
  — 29 passed (1 new helper test, 1 new prompt-pin test, plus 2 pre-existing tests corrected to
  stop accidentally modeling the stale-copy anomaly as a happy path). `node --check` on both
  workflow files re-run, both exit 0.
- Bare `pytest tests/tools/ -m "not slow and not extra_slow"`, run from the worktree, **after the
  `stale_child_copies` addendum** (the number that matters — supersedes the pre-addendum run
  below): **3173 passed, 25 skipped, 28 deselected, 1 xfailed, 0 failed** (352.57s).
  `tests/tools/test_validate_frontmatter.py` specifically re-run and confirmed clean (the exact
  test the peer flagged as at risk): 106 passed.
- Bare `pytest tests/tools/`, pre-addendum (kept for the record; the post-addendum run above is
  authoritative): 3171 passed, 0 failed (359.30s). `epic_folder_status.py` maps to `tests/tools/`
  under `expected_test_dirs_for()` (confirmed directly), so both runs cover it.

## Files Changed

- `tools/epic_folder_status.py` — new shared helper: `get_epic_folder_status()` (pure function)
  plus a real CLI `main()`, used by both workflows below.
- `.claude/workflows/implement-epic.js` — shared `buildEpicCloseInstructions()` helper with a
  `moveDestination` parameter; folder-cleanup block now calls `epic_folder_status.py` to detect
  its own epic-tier parent and closes it before the folder move; epic_id-mode block unchanged in
  behavior, refactored to call the shared helper.
- `.claude/workflows/implement-ticket.js` — Finalize step 3 calls `epic_folder_status.py` and
  prints an advisory instead of silently skipping when the only remaining `TCK-*.md` in a folder
  is its epic-tier parent.
- `tests/tools/test_implement_epic_close_step.py` — 1 re-pinned assertion, 1 corrected message, 4
  new tests, re-anchored to the helper-based step text.
- `tests/tools/test_finalize_epic_parent_advisory_pin.py` — new file, 5 tests.
- `tests/tools/test_epic_folder_status.py` — new file, 8 tests.
- `agent-monitoring/retro/RETRO-2026-W39.md` — regenerated per Scope item 5 (three times — before
  the `epic_folder_status.py` extraction, after it, and again after the `stale_child_copies`
  addendum, to capture the final state each time).
- `docs/REGISTRY.yaml` — regenerated (`make docs-registry`); no manual edits.
- **Addendum**: `tools/epic_folder_status.py` — new `stale_child_copies` field.
  `.claude/workflows/implement-epic.js` and `.claude/workflows/implement-ticket.js` — both move
  branches now also require `stale_child_copies` to be empty, printing an advisory otherwise.
  `tests/tools/test_epic_folder_status.py` — 1 new test, 2 existing tests corrected to stop
  modeling the anomaly as a happy path. `tests/tools/test_finalize_epic_parent_advisory_pin.py` —
  1 new test, existing anchors widened/updated for the reworded step text.

**Addendum, same session (agent-working-design review of the closed ticket, third pass): a real
regression, fixed.** `get_epic_folder_status()` treated a non-epic child as "done" purely because
`<done_dir>/<ticket_id>.md` existed, even when that child's `TCK-*.md` was ALSO still physically
present in the todos folder (a resurrected pre-close copy — exactly the shape
`TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS` guards against, and exactly what #241
re-added to `tickets/todos/mechanism-registry/`). The old implement-ticket.js rule ("move only if
no `TCK-*.md` files remain") would have skipped such a folder; the new `all_children_done`-driven
rule moved it, carrying the stale copy into `tickets/done/<folder>/` and duplicating the basename
against the authoritative flat `tickets/done/<id>.md`. Caught before this reached `origin/main` —
this ticket was still local, unpushed, part of the same review cycle, so fixed in place rather
than filed as a separate follow-up ticket.

Fix: added a `stale_child_copies` field to `get_epic_folder_status()` — non-epic children present
in the folder AND already closed in `done_dir` — kept structurally separate from `open_children`
(an `open_children` entry means "not done, don't move"; a `stale_child_copies` entry means
"already done elsewhere, delete this copy first" — different remediations, so they must not be
conflated). `all_children_done`'s own meaning is unchanged (still `open_children` only). Both
workflows' move branches now additionally require `stale_child_copies` to be empty, printing an
advisory to delete the stale copies (the `tickets/done/` versions are authoritative) and re-run
otherwise. Caught in the same pass: my own original happy-path test
(`test_epic_parent_only_case_reports_all_children_done_and_no_open_children`) had accidentally
modeled this exact anomaly (a child file left in the folder AND already in `done_dir`) rather than
the real "child closed, file removed" convention — fixed to match the real convention, and the
anomalous shape now has its own dedicated test instead.

## Completion Summary

All 4 acceptance criteria met. Folder mode's own epic-tier parent is now detected structurally
(via a real committed helper shared with implement-ticket.js's Finalize, not an inline `python3
-c` or a filename match), closed in place (frontmatter/body, no individual mv), and archived
correctly inside its folder by the existing folder-level move — matching both real precedents.
implement-ticket.js's Finalize never closes a different ticket's lifecycle from inside its own
Finalize; it advises instead. Three real issues were caught in review before this reached
`origin/main`, all fixed rather than papered over: a flat-mv destination that would have stranded
the epic parent outside its folder, an inline `python3 -c` that collided with an existing gate,
and a stale-pre-close-copy gap that would have let a resurrected child copy ride into
`tickets/done/<folder>/` alongside a genuinely-done flat copy of the same ticket. Final bare
`pytest tests/tools/` run (after this addendum): 3173 passed, 25 skipped, 28 deselected, 1
xfailed, 0 failed. No known material gap left unstated.
