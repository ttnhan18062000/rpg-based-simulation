---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
phase: done
date: 2026-09-02
tags: [content, determinism]
---

# TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT

## Title
Stage A pilot: migrate unit_information_source to Region/Place

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 3/5 of `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`, depends on
`TCK-20260902-WORLDCOMPILER-PLACE-WIRING`. Smallest correctness check per the plan doc: migrate
`unit_information_source` (16 entities, 1 region — `frontier_village_core` + `hero_adventurers`) so it
compiles as one `Region` containing exactly one `Place(kind=CITY)`. Nothing else should change.

## Scope
- Migrate `unit_information_source`'s content to Place-shaped form.
- Compile it under the new schema and verify the migration's actual effect using
  `CanonicalStateHasher` (the real, full-coverage hash), not `StateFingerprinter`'s `state_hash` alone
  — see Implementation Notes for why the latter can't do this job.
- Confirm the diff is isolated to exactly the new Place data, nothing else.

## Out of Scope
- Any other world (Stage B and the remaining-19-world rollout are separate tickets).
- `grade_anchors.json` re-runs (not applicable to this world's isolation-test scope).
- Fixing the repo-wide committed-baseline staleness found during this ticket (filed as
  `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`, genuinely out of scope for idea 66).

## Acceptance Criteria
- [x] `unit_information_source` compiles as 1 Region containing exactly 1 `Place(kind=CITY)`.
- [x] Migration verified via `CanonicalStateHasher`, not the committed `state_hash` (found to be both
      stale for unrelated reasons and structurally blind to Place data — see Implementation Notes).
      Confirmed the *only* difference in the full canonical dict, before vs. after, is `regions`/
      `places` — no entity, building, or resource state changed.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (parent epic)
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING (dependency)
- TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT (depends on this)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` item 2

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT/`)

## Related Code Areas
- `data/content/world_modules/frontier_village_core.yaml` — the real content location (confirmed
  directly: `unit_information_source` has no standalone content of its own, it's a
  `worldcomposition.v1` world composing `frontier_village_core` + `hero_adventurers`; every one of the
  21 worlds uses the shared-module Composition path, none uses the Direct path with inline `regions:`).
- `src/worldbuilding/compiler.py` — added `canonical_state_hash`/`place_count` to the compile report.
- `data/worlds/unit_information_source/world_compile_report.json`, `resolved/world.resolved.yaml` —
  regenerated.

## Assumptions / Open Questions
- ~~None beyond what the parent epic already tracks.~~ **Real finding during implementation**: the plan
  doc's "isolated single-world pilot" framing assumed a content architecture that doesn't exist — there
  is no per-world region-override mechanism, and no standalone (non-composition) world exists in the
  real 21-world corpus. Editing `frontier_village_core` to add the pilot's Place therefore affects all
  17 worlds that compose it, not just this one — see the epic's own ticket for how this reshapes Stage
  B's scope.

## Implementation Notes
Three real findings during implementation, none anticipated at scoping time:

1. **No isolated pilot target exists.** All 21 worlds use `worldcomposition.v1` (the shared-module
   Composition path); zero use the Direct path with inline regions. `WorldCompositionSpec` has no
   per-world region-override mechanism. Adding a Place to `unit_information_source` therefore requires
   editing the shared `frontier_village_core` module, which cascades to all 17 worlds that compose it.
   Decided (user-confirmed) to do this directly rather than build new isolation machinery just to
   preserve a false premise — see the epic's own tracking for the Stage B scope implication.
2. **`state_hash` can't verify this migration at all.** `world_compile_report.json`'s `state_hash` comes
   from `StateFingerprinter` (confirmed by its 32-char MD5 format), which has zero reference to `places`
   anywhere in `src/replay/fingerprint.py`. Verified directly: compiling the same world with and without
   the new Place produces an *identical* `state_hash` — not because the migration was a no-op, but
   because this specific check is structurally blind to Place data. Fixed by adding
   `canonical_state_hash` (`CanonicalStateHasher`, the real full-coverage hash used by
   `src/engine/kernel.py`'s own per-tick/final-run determinism checks) and `place_count` to the compile
   report (`src/worldbuilding/compiler.py`) — this is now the real verification mechanism, both for this
   ticket and for Recalibration going forward.
3. **All 21 committed baselines are stale, unrelated to idea 66.** Confirmed via `git log`: every one of
   the 21 worlds' `world_compile_report.json` files was last committed in the same single commit
   (`29d78798`, 2026-08-14), 83 commits ago. Spot-checked 3 worlds unrelated to my changes
   (`dungeon_crawl`, `wilderness_survival`, `urban_political`) — none reproduce their committed
   `state_hash` on a clean recompile. Root-caused: not a determinism bug (compiler reproduces identical
   output given identical input, verified directly) — a fixture-maintenance gap, currently unenforced by
   any test. Filed as `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`. Worked around for this
   ticket by comparing against a *freshly regenerated* baseline (recompile unchanged content once, use
   that as the reference point) rather than the stale committed one.

Migration itself: added one `places:` entry to `frontier_village_core.yaml`'s `hometown` region —
`{id: hometown_city, kind: city, position: [25, 25]}` (centroid of the region's `grid_bounds`).
`owner_faction_id`/`footprint`/`scale` left unset — Place inherits the Region's existing sovereignty by
default, and no calibrated value exists yet for `scale` (same caution this session applied to other new
numeric territory).

## Test Summary
- Confirmed via a direct comparison script (`CanonicalStateHasher.to_canonical_data()` before/after):
  the *only* top-level canonical-dict keys that differ are `regions` and `places` — no entity, building,
  or resource state changed. Entity/building/resource counts identical (16/5/2).
- 2 new tests in `tests/unit/worldbuilding/test_world_compiler.py`:
  `test_compile_report_includes_canonical_state_hash_and_place_count`,
  `test_compile_report_state_hash_blind_to_places_canonical_hash_is_not` (the exact regression this
  ticket found, now locked in as a regression guard).
- Updated `tests/certification/test_world_compile_determinism.py::test_compile_report_contents`'s exact
  key-set assertion for the 2 new report fields.
- Full regression sweep: `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/
  tests/unit/worldmodules/ tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/
  -m "not slow"` → 895 passed, 2 skipped (pre-existing, unrelated), 0 failed.
- Real-world verification: regenerated `unit_information_source`'s actual committed
  `world_compile_report.json`/`resolved/` assets — `place_count: 1`, `entity_count: 16` (matches the
  plan doc's own description), `canonical_state_hash` populated.

## Files Changed
- `data/content/world_modules/frontier_village_core.yaml` — added the pilot's `places:` declaration
  (affects all 17 composing worlds — see Stage B).
- `src/worldbuilding/compiler.py` — added `canonical_state_hash`/`place_count` to the compile report.
- `data/worlds/unit_information_source/world_compile_report.json`, `resolved/*` — regenerated.
- `tests/unit/worldbuilding/test_world_compiler.py` — 2 new tests.
- `tests/certification/test_world_compile_determinism.py` — updated exact-key-set assertion.
- `tickets/todos/TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS.md` — new follow-up ticket (not
  implemented).
- `tickets/inprogress/TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT.md` → moved to `tickets/done/`.

## Completion Summary
Migrated `unit_information_source` to Place-shaped content — 1 Region containing exactly 1
`Place(kind=CITY)`, matching the plan doc's own description exactly. Along the way, found and worked
around two real gaps neither ticket anticipated: the corpus has no isolated single-world content target
(all 21 worlds share modules), and `state_hash` can't verify Place migrations at all (fixed by adding
`canonical_state_hash` to the compile report). Also found and filed a third, genuinely out-of-scope
finding: all 21 committed baselines are stale for reasons unrelated to idea 66. Verified the migration
itself is fully isolated — the only canonical-dict difference is the new Place data, confirmed directly,
not assumed. Next: Stage B, which inherits this same shared-module reality — the `frontier_village_core`
edit already lands for 17 of the 21 worlds; Stage B's own scope is to verify `hero_guild_routing`'s
non-uniform region kinds and handle the remaining 4 worlds that don't compose `frontier_village_core`.
