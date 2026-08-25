---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE
phase: done
date: 2026-08-25
tags: [engine, bug, websocket]
---

# TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE

## Title
`force_full_scan`'s "Phase 17 Law" (`AuthoritativeApplyPipeline._refresh_dirty_set`) is dead code -- no live path can produce an all-entities WS delta

## Status
DONE

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
- [x] `AuthoritativeApplyPipeline._refresh_dirty_set`'s dead/orphaned status is resolved one way or
      the other (wired in correctly, or removed with its "Phase 17 Law" comment and any now-stale
      references), not left in its current half-documented, uncalled state
- [x] A `force_full_scan=True`-booted `Kernel`/`V2EngineManager` genuinely produces (or is
      documented as intentionally NOT producing, if investigation concludes removal is correct) a WS
      delta whose `changed` list contains every live entity, proven by a real, passing test
- [x] `V2EngineManager._update_latest_state`'s `getattr(self._kernel.status, "force_full_scan", False)`
      read is fixed to actually reflect the Kernel's boot-time `force_full_scan` flag, or is removed if
      the overall mechanism is deprecated instead
- [x] `docs/parity_ledger/infrastructure.yaml`'s `INFRA-388` (or a new entry) reflects the true,
      post-fix end state

## Related Tickets
- TCK-20260821-LIVE-MAP-PERF-VALIDATION (origin of this finding -- AC4 Finding 1)
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST (introduced `compute_tick_delta`/`INFRA-388`)
- TCK-20260825-OPT-INV-001-STALE-TEST-CITATION (filed at Verify to carry forward a real, unrelated
  stale-doc-citation gap found while reading `optimization_invariants.md` for this ticket's own
  OPT-INV-002 edit -- `optimization_invariants.md:55` cites a test file that doesn't exist)

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

Implemented exactly per the APPROVED, twice-corrected `staging_artifacts/TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE/plan.md` (6 steps). No deviations from the plan.

- **Step 1** (`src/engine/pipeline.py`): after the existing "Final dirty set for result application" block (`dirty_builder.mark_from_update(state, update)` / `update = update.replace(dirty_set=dirty_builder.build())`), added `if update.force_full_scan: ... update = update.replace(dirty_set=replace(update.dirty_set, movement_entities=all_ids, combat_entities=all_ids, inventory_entities=all_ids, strategic_entities=all_ids, social_entities=all_ids, lifecycle_entities=all_ids, town_entities=state.town_entity_ids, biological_entities=all_ids, attribute_entities=all_ids))`. Used the module-level `dataclasses.replace` (already imported at `pipeline.py:7`, already used bare elsewhere in the file) on `update.dirty_set` itself, per plan's Correction 2 — not a bare `DirtySet(...)` construction — so the eight non-entity fields (`group_ids`, `region_ids`, `resource_node_ids`, `building_ids`, `chest_ids`, `ground_item_ids`, `corpse_ids`, `camp_ids`) that `dirty_builder.build()` had just correctly computed are preserved verbatim. No new import was needed (plan's Correction 2 made Correction 1's `DirtySet` import moot).
- **Step 2**: deleted `_refresh_dirty_set` entirely (the whole `@staticmethod`, its docstring, and the "Phase 17 Law" inline comment) — no stub left, no call added. `grep -rn "_refresh_dirty_set" --include="*.py" .` from repo root now returns zero hits except the two historical, out-of-scope comment lines in `tools/perf/live_map_ws_payload_measure.py` (left untouched, per Out of Scope).
- **Step 3** (`src/engine/runtime_status.py`): added `force_full_scan: bool = False` immediately after `max_mode_reached`.
- **Step 4** (`src/engine/kernel.py`): added `self._status.force_full_scan = self._force_full_scan` immediately after `self._status = status or DefaultStatus()` (line 109).
- **Step 5**: updated `docs/core/dirty_state_and_dependency.md` (rewrote the `force_full_scan` fallback subsection to describe both post-fix halves — routing bypass unchanged, downstream dirty-set forcing new — and added a new row to the Regression tests table), `docs/performance/optimization_invariants.md` (added Invariant Rule 4 under OPT-INV-002 and cited the new test in Enforcement & Verification), and `docs/parity_ledger/infrastructure.yaml`'s `INFRA-388` (appended a `force_full_scan` clause to `text` and appended the four new test IDs to `test_path`; left `status: verified` and `priority: P1` unchanged, per plan). Left the pre-existing stale `test_static_dirtyset_guard.py` citation in `optimization_invariants.md` line 55 untouched, per plan's explicit "flag, don't fix" instruction — flagging it here for the orchestrator/user as a separate, small follow-up (the file does not exist anywhere in this worktree; not this ticket's Scope).
- **Step 6**: added `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py` (tests 1, 2, 4, with test 5 folded into test 1 as a second, lightweight assertion comparing against an equivalent `force_full_scan=False` run) and `tests/unit/engine/test_runtime_status.py` (test 3, split across three small test functions covering the default-construction case and both boot-flag cases separately, matching test_plan.md's three stated assertions). Test 4 pins observability mode explicitly via `ObservabilityConfig.clear_all_overrides()` + `ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)` in a try/finally, matching `tests/unit/config/test_phase19_observability_feature_flags.py`'s convention.

Verified all Build Gate commands pass (see Test Summary). Confirmed via YAML round-trip (`yaml.safe_load`) that the `infrastructure.yaml` edit remains valid YAML after fixing one colon-in-plain-scalar issue found while drafting the `text` addition (rewrote `end-to-end: AuthoritativeApplyPipeline...` to `end-to-end -- AuthoritativeApplyPipeline...`, since a mid-line `": "` inside an unquoted YAML block scalar is parsed as a new mapping key). Ran `tools/validate_frontmatter.py` against the ticket and all three staging artifacts — all OK, no violations.

## Test Summary

All 6 Build Gate commands from `plan.md`'s "Build Gate — Scoped Pytest Commands" section, run under `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (this worktree's bare `.venv/bin/python3` relative path does not exist — a known, pre-existing worktree quirk, not fixed here):

1. `tests/perf/test_dirty_set_integrity.py tests/unit/domains/optimization/` — **103 passed**
2. `tests/unit/api/test_read_model_cache.py` — **12 passed**
3. `tests/integration/optimization/` (includes the 3 new tests in `test_force_full_scan_dirty_set_completeness.py`) — **18 passed**
4. `tests/integration/kernel/test_minimal_kernel.py tests/unit/engine/` (includes the 3 new tests in `test_runtime_status.py`) — **180 passed, 1 skipped** (pre-existing, unrelated skip: `TestScenarioRuntimeServiceEventRecorder::test_scenario_objective_progressed_gap`)
5. `tests/perf/test_dirty_parity.py::test_dirty_set_vs_full_scan_parity -m "perf and slow"` — **1 passed** (confirms the fix does not affect the state-hash-fingerprint parity between an optimized and a `force_full_scan=True` reference kernel over 100 ticks)
6. `tests/integration/pipeline/test_authoritative_apply.py tests/integration/kernel/test_determinism_suite.py` — **8 passed**

**Total: 322 passed, 1 skipped, 0 failed.** No pre-existing test was modified; all new coverage is additive (2 new files).

## Files Changed
- `src/engine/pipeline.py` — wired the full-scan branch into `refine()`'s final dirty-set block (Step 1); deleted `_refresh_dirty_set` entirely (Step 2)
- `src/engine/runtime_status.py` — added declared `force_full_scan: bool = False` field to `RuntimeStatus` (Step 3)
- `src/engine/kernel.py` — populate `self._status.force_full_scan` once at `Kernel.__init__` (Step 4)
- `docs/core/dirty_state_and_dependency.md` — updated the `force_full_scan` fallback subsection and Regression tests table (Step 5a)
- `docs/performance/optimization_invariants.md` — added Invariant Rule 4 under OPT-INV-002 and updated Enforcement & Verification (Step 5b)
- `docs/parity_ledger/infrastructure.yaml` — updated `INFRA-388`'s `text` and `test_path` (Step 5c)
- `tests/integration/optimization/test_force_full_scan_dirty_set_completeness.py` — new file, tests 1/2/4/5 (Step 6)
- `tests/unit/engine/test_runtime_status.py` — new file, test 3 (Step 6)
- `tickets/inprogress/TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE.md` — this ticket file (Implementation Notes, Test Summary, Files Changed, Acceptance Criteria checkboxes)
- `staging_artifacts/TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE/plan.md` — carries the round-2 architecture-review corrections (Correction 1/2 to Step 1's code, the "Round-2 architecture review update" summary paragraph) applied during this ticket's own pre-Implement Plan/review phase, before this Implement run began; not edited by this Implement run itself, but confirmed via `git diff` against HEAD to be part of this run's real changeset per repo hygiene rules, so listed here rather than silently omitted.

No further changes to `plan.md` were made during this Implement run itself — it was read as the already-approved, already-twice-corrected final spec and followed exactly with zero deviations, so no additional "Deviations" section was added. `investigation.md` and `test_plan.md` show no diff against HEAD (both already reflected the final, current state when this Implement run began).

## Completion Summary

Fixed `AuthoritativeApplyPipeline._refresh_dirty_set`'s dead-code status by relocating only its genuinely-needed `if update.force_full_scan:` branch into `refine()`'s tail (gated explicitly, using `dataclasses.replace()` on the already-correct `update.dirty_set` rather than a bare `DirtySet(...)` reconstruction, to avoid discarding the eight non-entity domain fields) and deleting the dead method outright. Closed the companion `RuntimeStatus`/`Kernel.status` surfacing gap by adding a declared `force_full_scan` field populated once at boot, so `V2EngineManager._update_latest_state` now correctly threads a real `force_full_scan=True` value into `ReadModelCache.compute_tick_delta`/`.update()` for every observability mode, including `OFF`. Added 6 new regression tests across 2 new files (all passing) and updated the 3 named docs plus `INFRA-388`. All 6 Build Gate commands pass (322 passed, 1 pre-existing unrelated skip, 0 failed), including the slow state-hash parity test confirming no determinism regression. All 4 acceptance criteria are genuinely satisfied with no environment blockers. A real, unrelated doc-accuracy gap (`optimization_invariants.md:55`'s OPT-INV-001 test citation pointing at a nonexistent file) was discovered while editing this same doc for OPT-INV-002 -- filed as a concrete follow-up ticket, `tickets/todos/TCK-20260825-OPT-INV-001-STALE-TEST-CITATION.md`, rather than silently fixed outside this ticket's own scope or silently dropped.
