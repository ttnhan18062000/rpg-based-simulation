---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260711-EPIC-SCOPE-ORPHAN-FIX
artifact_type: test_plan
tags: [epic, scope, orphan, workflow]
---

# Test Plan — TCK-20260711-EPIC-SCOPE-ORPHAN-FIX

## Regression Surface

**Unit — implement-ticket.js source-text assertions (highest risk for this change):**
- `tests/tools/test_step0_ts_orchestrator.py` — specifically
  `test_ts_capture_bash_precedes_each_covered_agent_call`, whose
  `_IMPLEMENT_TICKET_ADJACENCY[0]` asserts the exact literal string
  `"const scopeTs = await captureTs()\nconst ticketInfo = await agent("` with zero intervening
  lines. This is the single test most likely to break if the new cp/rm `bash()` call is placed in
  the wrong spot (see investigation.md Risk #2).
- `tests/tools/test_current_run_sidecar_orchestrator.py` — specifically
  `test_scope_phase_call_site_has_no_preceding_sidecar_write` (asserts no `writeSidecar(` call
  between `const ticketInfo = await agent(` and `{ label: 'scope',`) and
  `test_writeMonitoring_call_has_no_preceding_sidecar_write`.
- `tests/tools/test_tag_skill_mapping_check.py` — same-file source-text-parsing sibling; guards
  against accidental collateral edits to unrelated `implement-ticket.js` prompt regions (tag→skill
  mapping table, mistag-warning logic) that sit adjacent to the Step 1-3 text being edited.

**Unit — gate_checks / agent-monitoring:**
- `tests/tools/test_done_checker_static.py` (full file) — every existing
  `check_ticket_location` / `check_ticket_finalized` / `run_static_precheck` /
  `run_finalize_selfcheck` test must remain green unmodified; the new orphan check must be
  additive, never a signature/shape change to any of these.
- `tests/tools/test_workflow_meta_conformance.py` (full file) — unrelated behavior, but same
  `gate_checks` package; guards against an import-side-effect regression if the new module is
  added to that package.
- `tests/tools/test_epic_staleness_check.py` (full file, 11 tests) — confirms
  `discover_candidate_epics()`'s epic_id-mode discovery still finds tier=epic tickets at
  `tickets/inprogress/{id}.md` unchanged after the move fix. The sibling dedupe ticket
  (`TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK`) is explicitly out of scope here, but this file's
  existing behavior is the tripwire if the fix accidentally changes final ticket placement.

**Integration / arena-combat:** none applicable. No JS test runner exists in this repo for
`.claude/workflows/*.js` (confirmed via `test_step0_ts_orchestrator.py`'s own docstring); all
verification of the `.js` behavior change is via static source-text assertions, consistent with
every sibling ticket in this family. This ticket does not touch simulation/combat code.

## New Tests Required

1. **`test_step1c_orphan_bash_precedes_capturets`** — unit / architecture guard — verifies
   `implement-ticket.js`'s new orchestrator-side cp/rm `bash()` construct for the todos→inprogress
   transfer is placed *before* `const scopeTs = await captureTs()`, not between it and
   `const ticketInfo = await agent(` — directly guards the collision identified in investigation.md
   Risk #2. Lives in new file `tests/tools/test_scope_orphan_fix.py` (new file per this ticket
   family's one-file-per-ticket convention).

2. **`test_epic_tier_move_deletes_todos_original`** — unit — given a synthetic
   `tickets/todos/{folder}/TCK-*.md` fixture with `## Tier` = `epic`, confirms the new move logic
   (whether implemented as an extracted, directly-callable helper or exercised via a shelled-out
   equivalent of the orchestrator's one-liner) results in exactly one on-disk copy in
   `tickets/inprogress/` and the todos original removed. Verifies AC #1. Lives in
   `tests/tools/test_scope_orphan_fix.py`.

3. **`test_standard_hotfix_tier_still_copy_only`** — unit — same fixture shape but `## Tier` =
   `standard` or `hotfix`, confirms cp-only behavior is preserved (todos original still present,
   matching the existing Finalize-reconciliation expectation). Verifies AC #2. Lives in
   `tests/tools/test_scope_orphan_fix.py`.

4. **`test_ticket_scoper_prompt_no_longer_unconditionally_copies`** — unit — confirms the Step 1c
   prompt text's current unconditional `Copy it to tickets/inprogress/${ticketId}.md` instruction
   is either removed from agent-prompt text or now conditioned on a pre-computed, orchestrator-known
   fact rather than left as a tier-blind agent-executed copy. Lives in
   `tests/tools/test_scope_orphan_fix.py`.

5. **`test_new_orphan_check_flags_dual_presence`** — unit — new check module (recommended:
   `tools/gate_checks/epic_scope_orphan_check.py`, pending the placement decision flagged in
   investigation.md Risk #4), given a synthetic fixture with the same `ticket_id` present in both
   `tickets/inprogress/*.md` (`## Tier` = `epic`) and `tickets/todos/**/*.md`, returns a
   FAIL/flagged result naming both paths as evidence. Verifies AC #3. Lives in new file
   `tests/tools/test_epic_scope_orphan_check.py` (mirrors `test_workflow_meta_conformance.py`'s
   tmp_path fixture-builder style).

6. **`test_new_orphan_check_passes_when_todos_original_absent`** — unit — same fixture but the
   todos original removed (or never present); confirms PASS / not-flagged. Lives in
   `tests/tools/test_epic_scope_orphan_check.py`.

7. **`test_new_orphan_check_does_not_flag_legitimate_epic_resting_in_inprogress`** — unit /
   architecture guard — an epic-tier ticket in `tickets/inprogress/` with **no** todos-folder
   original (the normal, documented `epic_id`-mode resting state per
   `docs/ai/ticket-lifecycle.md:440`) must **not** be flagged. Directly verifies the ticket's own
   AC #3 distinction ("actual orphan signature — dual presence, not merely 'epic ticket resting in
   inprogress/'"). Lives in `tests/tools/test_epic_scope_orphan_check.py`.

8. **`test_new_orphan_check_ignores_non_epic_dual_presence`** — unit / architecture guard — a
   standard/hotfix-tier ticket present in both `tickets/inprogress/` and `tickets/todos/`
   simultaneously (the normal, expected mid-flight state pending Finalize — confirmed live for 2
   real tickets in the repo today) must **not** be flagged. Only epic-tier dual presence is the
   orphan signature. This is the highest-value false-positive guard given the confirmed live state.
   Lives in `tests/tools/test_epic_scope_orphan_check.py`.

9. **`test_live_repo_orphan_check_returns_zero_findings`** — integration — runs the new check
   against the actual live `tickets/inprogress/` and `tickets/todos/` directories (no fixture,
   real repo state) and asserts zero flagged orphans. Directly verifies AC #4 literally ("running
   this new check against the live repo post-fix returns zero orphans") — synthetic-fixture tests
   alone (#5-8) do not satisfy this AC. Lives in `tests/tools/test_epic_scope_orphan_check.py`,
   clearly commented as a live-repo (non-isolated) assertion, consistent with this codebase's
   existing convention for the few tests that intentionally scan real repo state rather than a
   tmp_path fixture.

10. **`test_check_ticket_location_and_finalized_signatures_unchanged`** — unit / architecture guard
    — explicit signature/shape check that `check_ticket_location(ticket_id, inprogress_dir=...) ->
    tuple[str, str]` and `check_ticket_finalized(ticket_id) -> tuple[str, str]` are unmodified
    (import and call with existing test fixtures, assert return shape) — the ticket asks to
    "mirror," not modify, these; this test makes that explicit rather than relying solely on
    `test_done_checker_static.py` passing unmodified. Lives in
    `tests/tools/test_epic_scope_orphan_check.py`.

## Scoped Pytest Commands

Pre-implementation baseline (run now, before any code change, to confirm no pre-existing failures
in the regression surface):
```
pytest tests/tools/test_step0_ts_orchestrator.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_done_checker_static.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_epic_staleness_check.py tests/tools/test_tag_skill_mapping_check.py -v
```

Post-implementation full scoped run (once the new test files exist):
```
pytest tests/tools/test_step0_ts_orchestrator.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_done_checker_static.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_epic_staleness_check.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_scope_orphan_fix.py tests/tools/test_epic_scope_orphan_check.py -v
```

Never: `pytest tests/` (unscoped) — per CLAUDE.md Testing Rule.

## Anti-Drift Test Guards

- `test_step1c_orphan_bash_precedes_capturets` (#1) and re-running
  `test_step0_ts_orchestrator.py::test_ts_capture_bash_precedes_each_covered_agent_call` /
  `test_current_run_sidecar_orchestrator.py::test_scope_phase_call_site_has_no_preceding_sidecar_write`
  unmodified are the direct tripwires for the highest-identified risk in this ticket: an
  incorrectly-placed orchestrator `bash()` call silently breaking two pre-existing, unrelated-looking
  regression tests.
- `test_new_orphan_check_ignores_non_epic_dual_presence` (#8) guards against the most likely
  scope-creep/false-positive failure mode: a check that flags the CURRENT, legitimate, expected
  dual-presence state of standard/hotfix tickets mid-workflow (confirmed live for 2 tickets in the
  repo right now — `TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME` and this ticket itself) as if it were
  the epic-only orphan bug.
- `test_new_orphan_check_does_not_flag_legitimate_epic_resting_in_inprogress` (#7) guards the
  ticket's own explicitly-named distinction (Scope bullet 3, AC #3) between "epic ticket resting in
  inprogress/" (legitimate, documented) and "dual presence" (the actual bug) — get this wrong and
  every future legitimately-scoped epic ticket gets falsely flagged forever.
- Re-running `test_epic_staleness_check.py`'s 11 existing tests unmodified guards against the fix
  accidentally changing where epic tickets land (still `tickets/inprogress/{id}.md`) or how they're
  discovered — any change to final placement is the tripwire this suite exists to catch.
- `test_check_ticket_location_and_finalized_signatures_unchanged` (#10) guards against silently
  drifting `done_checker_static.py`'s existing checked-in contracts while building something that
  merely "mirrors" their shape, per the ticket's own explicit "mirroring... (status, evidence) tuple
  shape" wording (mirror, not modify).
- Confirm the sibling ticket's scope boundary is respected: no new test in this ticket's suite
  should assert anything about `epic_staleness_check.py::discover_candidate_epics()`'s
  double-discovery/dedupe behavior across its two scan loops — that is
  `TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK`'s regression surface, not this ticket's.
