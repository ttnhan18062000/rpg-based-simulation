---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE
phase: open
date: 2026-08-25
tags: [engine, bug, websocket]
---

# TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE

## Title
`force_full_scan`'s "Phase 17 Law" (`AuthoritativeApplyPipeline._refresh_dirty_set`) is dead code -- no live path can produce an all-entities WS delta

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`src/engine/pipeline.py::AuthoritativeApplyPipeline._refresh_dirty_set` is a static method whose
docstring/comment calls it a "Hardening Phase" implementing "Phase 17 Law: If force_full_scan is
True, the dirty set must include ALL entities" -- but it is never called anywhere in the codebase.
Discovered during `TCK-20260821-LIVE-MAP-PERF-VALIDATION`'s Implement phase (see
`stored_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/report.md`'s AC4 Finding 1, and that
ticket's `plan.md` Deviations section), independently re-verified 3 additional times during that
ticket's own pipeline (doc-updater, architecture-reviewer during Architecture-Verify, and the
orchestrator, each via a fresh full-repo `grep -rn "_refresh_dirty_set" --include="*.py" .`
returning zero call sites beyond the method's own definition at `pipeline.py:363`).

Net effect: today, no live mechanism -- not `tick % 20 == 0`, not a `Kernel(flags={"force_full_scan":
True})` boot, nothing -- can make `AuthoritativeApplyPipeline.refine()`'s resulting `DirtySet` (the
one that reaches `ReadModelInvalidationPolicy.get_dirty_entity_ids` / `ReadModelCache.compute_tick_delta`
/ the `/api/v1/ws` broadcast) actually contain every entity. `force_full_scan=True` DOES still work
correctly for its OTHER, already-tested purpose -- widening `CandidateSelector`/`MovementCandidateSelector`
phase-routing to iterate all entities within `refine()`'s own execution (`src/core/dirty.py`'s
`get_relevant_entity_ids`, `src/engine/candidate_selector.py:113`; both covered by real passing tests,
`tests/integration/optimization/test_force_full_scan_phase_compliance.py`,
`tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity`) -- only the DOWNSTREAM
DirtySet that's supposed to reflect that full scan for consumers outside the pipeline (the read-model
cache, the WS broadcast) never gets rebuilt, because `_refresh_dirty_set` -- the only method that
contains that rebuild logic -- is orphaned.

There is a second, compounding gap discovered by the same investigation: `V2EngineManager._update_latest_state`
(`src/api/engine_manager.py:156`) reads `getattr(self._kernel.status, "force_full_scan", False)` to
decide whether to pass `force_full_scan=True` into `ReadModelCache.compute_tick_delta`/`.update()` --
but `Kernel.status` (`src/engine/kernel.py`) returns a `RuntimeStatus` dataclass
(`src/engine/runtime_status.py`) that has no `force_full_scan` field at all, so this `getattr` always
returns its `False` default regardless of how the `Kernel` was booted. Even if `_refresh_dirty_set`
were wired back in, this second gap would still need fixing for the read-model/API layer to ever see
a full scan.

## Scope
- Root-cause and fix (or formally deprecate/remove, if investigation concludes it should not be
  wired back in) `AuthoritativeApplyPipeline._refresh_dirty_set`'s orphaned status in
  `src/engine/pipeline.py` -- either call it at the correct point in `refine()`'s phase sequence
  (immediately before the "Final dirty set for result application" block, mirroring where
  `DirtySetBuilder.mark_from_update` is already called per `pipeline.py` lines 261/296/314/329/352),
  or determine via investigation that its logic was genuinely superseded by
  `DirtySetBuilder.mark_from_update` and the dead method + its "Phase 17 Law" comment should be
  removed instead.
- Fix the second gap: wire `Kernel.status`/`RuntimeStatus` (or `V2EngineManager._update_latest_state`'s
  read of it) so a `force_full_scan=True`-booted `Kernel` actually surfaces that fact to
  `ReadModelCache.compute_tick_delta`/`.update()`, if the first fix concludes the mechanism should
  work end-to-end.
- Add or restore a regression test proving a `force_full_scan=True` boot produces a WS delta message
  whose `changed` list contains every live entity (the exact gap `TCK-20260821-LIVE-MAP-PERF-VALIDATION`'s
  own harness worked around with a synthetic in-process estimate instead of a live capture, because
  no live capture was possible).
- Update `docs/parity_ledger/infrastructure.yaml`'s `INFRA-388` entry (or add a new entry) reflecting
  whichever end state investigation concludes is correct (wired-and-working vs. formally removed).

## Out of Scope
- Any change to `TCK-20260821-LIVE-MAP-PERF-VALIDATION`'s own deliverables (`tools/perf/live_map_ws_payload_measure.py`,
  `frontend/perf/live_map_render_timing.mjs`, its `staging_artifacts`/`stored_artifacts`) -- that
  ticket is closed; this is a fresh, independent fix.
- Any change to the frontend (`frontend/src/hooks/useSimulation.ts` and friends) -- this is purely a
  backend engine/read-model correctness gap.
- Building a new full-scan-cadence feature (e.g. an automatic periodic full re-sync) beyond making
  the existing, already-documented `force_full_scan` mechanism work correctly end-to-end as designed.

## Acceptance Criteria
- [ ] `AuthoritativeApplyPipeline._refresh_dirty_set`'s dead/orphaned status is resolved one way or
      the other (wired in correctly, or removed with its "Phase 17 Law" comment and any now-stale
      references), not left in its current half-documented, uncalled state
- [ ] A `force_full_scan=True`-booted `Kernel`/`V2EngineManager` genuinely produces (or is
      documented as intentionally NOT producing, if investigation concludes removal is correct) a WS
      delta whose `changed` list contains every live entity, proven by a real, passing test
- [ ] `V2EngineManager._update_latest_state`'s `getattr(self._kernel.status, "force_full_scan", False)`
      read is fixed to actually reflect the Kernel's boot-time `force_full_scan` flag, or is removed if
      the overall mechanism is deprecated instead
- [ ] `docs/parity_ledger/infrastructure.yaml`'s `INFRA-388` (or a new entry) reflects the true,
      post-fix end state

## Related Tickets
- TCK-20260821-LIVE-MAP-PERF-VALIDATION (origin of this finding -- AC4 Finding 1)
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST (introduced `compute_tick_delta`/`INFRA-388`)

## Related Docs
- docs/core/dirty_state_and_dependency.md
- docs/core/update_intents.md
- docs/engine/candidate_selection.md
- docs/performance/optimization_invariants.md
- docs/parity_ledger/infrastructure.yaml (INFRA-388)

## Related Stored Artifacts
- stored_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION (report.md's AC4 Finding 1 has the full
  root-cause trace: file:line citations for `_refresh_dirty_set`'s zero call sites,
  `DirtySetBuilder.mark_from_update`'s call sites, and the `Kernel.status`/`RuntimeStatus` gap)

## Related Code Areas
- src/engine/pipeline.py (`AuthoritativeApplyPipeline.refine()`, `._refresh_dirty_set`)
- src/engine/kernel.py (`Kernel.status`, `_force_full_scan`)
- src/engine/runtime_status.py (`RuntimeStatus`)
- src/api/engine_manager.py (`V2EngineManager._update_latest_state`)
- src/api/read_model_cache.py (`ReadModelCache.compute_tick_delta`, `ReadModelInvalidationPolicy`)
- src/core/dirty.py (`DirtySetBuilder`, for contrast with the orphaned method)

## Assumptions / Open Questions
- Whether `_refresh_dirty_set`'s full-scan logic should be wired back in exactly where it appears to
  have been intended (immediately before the final dirty-set-rebuild block in `refine()`), or whether
  its logic is genuinely redundant with `DirtySetBuilder.mark_from_update`'s incremental marking and
  should instead be removed as dead code -- this needs real investigation, not an assumption, since
  wiring in a full-entity-marking pass at the wrong point in the 17-phase sequence could have
  performance or correctness side effects on a live 2500-entity world.
- Whether any other consumer besides the WS broadcast (e.g. `ReadModelCache.get_entities_paged`, or a
  future consumer) currently relies on or would be affected by `force_full_scan` actually starting to
  work end-to-end -- worth a repo-wide check during investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
