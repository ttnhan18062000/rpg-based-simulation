---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK
phase: done
date: 2026-07-11
tags: []
---

# TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK

## Title
Add dedupe logic to epic_staleness_check.py to prevent double-discovery of epics present in both todos and inprogress

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Investigation of the epic-tier Scope-phase orphan defect (this concern's root cause, tracked in TCK-20260711-EPIC-SCOPE-ORPHAN-FIX) surfaced a second-order gap in tools/agent-monitoring/epic_staleness_check.py: discover_candidate_epics() scans tickets/inprogress/*.md (epic_id-mode) and tickets/todos/{folder}/ (folder-mode) as two independent loops with no dedupe logic across them. When the same epic ticket exists in both locations simultaneously, it is double-discovered and double-nudged by staleness checks, and this scenario has zero existing test coverage across the current 11 tests in test_epic_staleness_check.py.

## Scope
- Add dedupe logic to discover_candidate_epics() (lines 119-163) in tools/agent-monitoring/epic_staleness_check.py so an epic ticket present in both tickets/inprogress/ (epic_id-mode) and tickets/todos/{folder}/ (folder-mode) scan loops is discovered/reported exactly once, not twice.
- Add regression test(s) to tests/tools/test_epic_staleness_check.py covering the dual-presence-in-both-locations scenario, alongside the existing 11 tests.

## Out of Scope
- Fixing the root-cause orphan-creation bug in implement-ticket.js's Scope phase (Step 1c copy-not-move) -- tracked in TCK-20260711-EPIC-SCOPE-ORPHAN-FIX; this ticket only hardens epic_staleness_check.py's discovery logic against the dual-presence state regardless of whether it originates from that bug, a pre-fix orphan, or any other transient window.
- Any change to done_checker_static.py or a new orphan-detection static check -- tracked in TCK-20260711-EPIC-SCOPE-ORPHAN-FIX.

## Acceptance Criteria
- [ ] epic_staleness_check.py's discover_candidate_epics(), given a fixture epic present in both tickets/inprogress/ and tickets/todos/{folder}/ simultaneously, is confirmed via a new test to dedupe and report the epic exactly once.
- [ ] Existing test_epic_staleness_check.py coverage (test_identifies_epic_tickets_vs_regular_tickets, test_handles_hybrid_folder_shape, and the other 9 tests) continues to pass unmodified.

## Related Tickets
- TCK-20260710-EPIC-STALENESS-CHECK
- TCK-20260711-EPIC-SCOPE-ORPHAN-FIX (sibling, root cause, created in parallel)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/epic_staleness_check.py
- tests/tools/test_epic_staleness_check.py

## Assumptions / Open Questions
- Assumes this dedupe hardening is valuable independent of whether TCK-20260711-EPIC-SCOPE-ORPHAN-FIX lands first: once that fix lands the dual-presence state cannot occur post-fix in the epic-tier Scope path specifically, but epic_staleness_check.py should still defensively dedupe since other transient windows (e.g. mid-Finalize reconciliation timing for hotfix/standard, or manual ticket copies) could theoretically produce the same dual-presence shape.
- Priority set to P3 (below the P2 hint given for the parent concern) because this is an untested latent gap with no confirmed live double-discovery incident, unlike the root-cause orphan which is confirmed live.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK/plan.md`'s 4 steps, no deviations:

1. Added `_dedupe_candidates_by_epic_id(candidates: list) -> list` to
   `tools/agent-monitoring/epic_staleness_check.py`, placed immediately after
   `_dedupe_preserve_order()` and before `_frontmatter_block()`, as specified. It is
   first-occurrence-wins, keyed strictly on `EpicCandidate.epic_id`. `_dedupe_preserve_order()`
   itself is untouched (still used only by `_child_ids_from_text()` and the folder-mode
   sibling-files fallback).
2. Changed `discover_candidate_epics()`'s final `return candidates` to
   `return _dedupe_candidates_by_epic_id(candidates)`. The epic_id-mode loop
   (`tickets/inprogress/*.md`) remains textually before the folder-mode loop
   (`tickets/todos/{folder}/`) — confirmed by direct re-read of the file before editing (no
   reordering was made), so first-occurrence-wins dedupe naturally makes the
   `tickets/inprogress/` candidate win any tie, per the plan's tie-break decision.
3. Added three new tests to `tests/tools/test_epic_staleness_check.py` (after the existing 11,
   none renumbered/modified), all using a shared `_write_dual_presence_fixture()` helper built on
   top of the existing `_write_ticket()` helper (unmodified signature):
   - `test_discover_candidate_epics_dedupes_dual_presence` — discovery-level, asserts
     `len(candidates) == 1`.
   - `test_dual_presence_not_double_reported_in_stale_list` — full
     discovery→classify→report pipeline, asserts `find_stale_epics()` returns the shared
     `epic_id` exactly once and `compute_stale_epics_report()`'s "Stale epics:" section contains
     exactly one matching line.
   - `test_dual_presence_prefers_inprogress_candidate` — locks in the tie-break: asserts
     `mode == "epic_id"` and `source_path.parent == inprogress_dir`.
4. Updated `docs/guides/agent_monitoring.md`'s "Epic Staleness Check" section with a short
   paragraph describing the new dedupe-by-`epic_id` behavior and its tie-break, since that doc
   previously described discovery without mentioning cross-mode duplication handling.

No parity ledger entry was added, per the plan's and investigation's shared position (pure
`layer: ai` agent-orchestration tooling, following the precedent set by
TCK-20260710-EPIC-STALENESS-CHECK, which also added no parity entry for this same file).

## Test Summary
`pytest tests/tools/test_epic_staleness_check.py -v` — 14 passed (11 pre-existing + 3 new),
no modifications to any pre-existing test.

`pytest tests/tools/test_epic_staleness_check.py tests/tools/test_scope_orphan_fix.py tests/tools/test_epic_scope_orphan_check.py -v`
— 27 passed (full regression bundle per test_plan.md's scoped command), confirming no breakage
in sibling modules that import from `epic_staleness_check.py`.

## Files Changed
- `tools/agent-monitoring/epic_staleness_check.py`
- `tests/tools/test_epic_staleness_check.py`
- `docs/guides/agent_monitoring.md`
- `docs/ai/ticket-lifecycle.md` (modified — Epic staleness check paragraph updated for dedupe/tie-break behavior, per DoD Verify finding)

## Completion Summary
Added a first-occurrence-wins, `epic_id`-keyed dedupe pass to
`discover_candidate_epics()` so an epic ticket present in both `tickets/inprogress/`
(epic_id-mode) and `tickets/todos/{folder}/` (folder-mode) is discovered and reported exactly
once, with the `tickets/inprogress/` candidate winning any tie. Covered by 3 new tests
(discovery-level, full-pipeline, and tie-break lock-in); all 11 pre-existing tests and both
sibling-module test files remain green unmodified. Pure in-memory list filter — no new write
path, no change to `EpicCandidate`'s shape or classification/reporting semantics.

Mid-Verify doc fix: Verify caught that `docs/ai/ticket-lifecycle.md`'s Epic staleness check
paragraph still described discovery without mentioning the new cross-mode dedupe/tie-break
behavior. Updated it in the same session before Finalize, mirroring the sibling ticket's
(TCK-20260711-EPIC-SCOPE-ORPHAN-FIX) own doc-gap finding during its Verify phase. All 4 files
below were touched; tests were re-run after the doc fix and remained green (doc-only change,
no code path affected).

All Files Changed below were touched. Tests were run and pass (14/14 in the direct test file,
27/27 across the scoped regression bundle). Ticket moved to `tickets/done/`, staging artifacts
migrated to `stored_artifacts/`, working log appended, and the parent `tickets/todos/` folder
verified empty of remaining tickets before archival.
