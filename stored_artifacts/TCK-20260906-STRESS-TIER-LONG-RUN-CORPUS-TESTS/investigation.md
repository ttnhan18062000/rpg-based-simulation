---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS
date: 2026-09-06
---

# Investigation: TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS

## Idea 57 — gap re-confirmed still real
Zero hits for `heroism_score`/`LegendFact` anywhere in `src/systems/strategic_systems/` (confirmed
via direct grep, matching the ticket's own citation). `src/domains/fame/` only contains the
Deriver/Exporter/model/legend files that PRODUCE the signal at episode boundaries — no consumer.
No corpus test authored for idea 57, per the ticket's own explicit instruction.

## Idea 48 — MAJOR CORRECTION: the ticket's own scope has no basis in real code

**The real mechanism (`src/world/transformation.py::TransformationService`) transforms REGION
terrain kinds (`RegionState.kind`, default `"FOREST"`, values FOREST/PLAINS/DESERT/WASTELAND/
MOUNTAIN/VOLCANIC/FROZEN_PEAKS/BURNT_FOREST), driven by `trauma_score`/`calamity_intensity`/
`stability`/`active_modifiers` — it has NOTHING to do with `PlaceKind` (CITY/CAMP/NEST/LAIR/
RUIN/DUNGEON/LANDMARK, idea 66's system) at all.** `TransformationService.TRANSFORMATION_THRESHOLDS`
has no CITY key and no RUIN target anywhere. The ticket's own scope text — "Author a
`faction_tension_overrides` entry driving sustained conflict against the `frontier_village_core`
region... Assert `Place.kind` flips CITY->RUIN" — conflates `RegionState.kind` (idea 48's real
terrain-type system) with `PlaceState.kind`/`PlaceKind` (idea 66's settlement-classification system,
already confirmed a separate concept by this same M9 batch's ticket 5 investigation for idea 44).

**Confirmed via direct read of `frontier_village_core`'s own compiled composition
(`data/content/world_modules/frontier_village_core.yaml:22`): its `hometown` region's `Place` is
declared `kind: "city"` — a `PlaceKind` value, entirely separate from `RegionState.kind`.** No
module composing `lifecycle_full_coverage_world` declares an explicit `RegionState.kind` override
anywhere (confirmed via grep across all 8 module YAMLs) — every region in this world defaults to
`RegionState.kind = "FOREST"` (the dataclass default, `src/core/state.py:271`), which IS a real,
transformable kind (FOREST->BURNT_FOREST at `trauma_score>=50`, FOREST->WASTELAND at
`trauma_score>=100` and `calamity_intensity>=0.5`).

**The real, already-shipped pure-function mechanism is already well-unit-tested**
(`tests/unit/world/test_transformations.py`: `test_forest_to_burnt_forest`,
`test_forest_to_wasteland`, `test_no_transformation_under_threshold`,
`test_mountain_to_frozen_peaks` — all real, all passing, direct `TransformationService.
apply_transformation()` calls). This ticket's own value-add, matching every other M9 sibling
ticket's own "SimQ-corpus-framed, real-pipeline-integration" angle, is proving the REAL per-tick
pipeline wiring works end-to-end — `WorldDynamicsSystem`'s "4. Regional Transformations" step
(`src/engine/world_dynamics.py:234-241`) actually applying a transformation and the real
`region_transformed` observability event actually firing — not re-proving the already-tested pure
function in isolation.

**Real trauma-raising mechanism identified**: `src/engine/world_dynamics.py:44-51`, "2.1
Death-triggered Trauma" — any entity combat death (`EntityUpdate.combat.alive_set is False`) in a
region adds `+1.0` to that region's `trauma_delta` for the tick. A real, established precedent for
constructing exactly this kind of hand-seeded combat-death update exists at
`tests/integration/world/test_regional_sovereignty.py:44-52` (`EntityUpdate(entity_id=1,
combat=CombatUpdate(outcome_kind="KILL", hp_delta=-20, alive_set=False))`, run through
`AuthoritativeApplyPipeline.refine()`/`LifecycleSystem.resolve_lifecycle()` +
`ApplyPath.apply_generation()`).

**Corrected test design**: hand-seed a region at `kind="FOREST"`, `trauma_score=49.0` (1 tick under
the real 50.0 `BURNT_FOREST` threshold), with one entity whose combat death is forced via the same
real construction pattern as `test_regional_sovereignty.py`. Run through the real
`AuthoritativeApplyPipeline.refine()` (which includes `WorldDynamicsSystem`'s trauma-then-
transformation steps) and `ApplyPath.apply_generation()`. Assert `region.kind == "BURNT_FOREST"`
post-apply, and that `EventExtractor.extract()` (or the real live shaper path, whichever is
default-active) reports a `region_transformed` event with `payload["new_kind"] == "BURNT_FOREST"`.

**SOCIAL/GUILD-drop caveat — does not apply to this corrected design, disclosed rather than
silently dropped.** The ticket's own caveat ("sustained COMBAT pressure starves SOCIAL/GUILD
goal-selection for the whole run") was written against the ORIGINAL scope's assumption of a long,
emergent multi-hundred/thousand-tick siege run. The corrected design is a single-tick, deterministic,
hand-seeded proof (matching this whole M9 batch's established precedent for hard-to-reach-via-
emergent-play mechanisms) — it does not run long enough for a goal-selection starvation effect to
occur or need tolerating. This is noted directly in the new test file's own docstring, not silently
omitted, so a future ticket that DOES attempt a genuine long emergent siege run against this same
world knows to expect and tolerate that drop.

## No new corpus world or new committed run_key needed
The corrected test needs no new registered world, no new `grade_anchors.json` run_key, and no
long-run manual invocation via `simq_long_run_observation.py` — the real pipeline integration point
(trauma accumulation -> transformation -> event emission) is provable deterministically in a single
tick, matching the same "impractical full run, real deterministic proof instead" reasoning this
whole M9 batch has used repeatedly (M9 tickets 1, 2, 4, 5).

## Docs Requiring Update
None — no behavior change, test-only ticket. The M9 epic doc's own idea-57 cross-reference already
exists from this session's earlier M7/M9 scoping work; confirmed still accurate, no edit needed.

## Parity Ledger Overlap
None — no `src/` production code change, `behavior_changed=false`.

## Prior Work
- `tests/unit/world/test_transformations.py` — the real, already-passing pure-function precedent this
  ticket's own new test does NOT duplicate (different angle: real pipeline integration, not the pure
  function in isolation).
- `tests/integration/world/test_regional_sovereignty.py` — the real hand-seeded-combat-death-through-
  `AuthoritativeApplyPipeline.refine()` precedent this ticket's own test structurally follows.

## Risks and Open Questions
None outstanding — the idea-48 correction is evidence-based (a field/system conflation, the same
class already resolved solo by every M9 sibling ticket so far), not a judgment call requiring
escalation.

## Anti-Drift Hazards
- Do not assert on `PlaceKind`/`Place.kind` for idea 48 — that is idea 66's separate system.
- Do not target `frontier_village_core`'s own region — its `Place.kind="city"` composition has no
  bearing on `RegionState.kind`, and no module in this world overrides `RegionState.kind` away from
  the FOREST default.
- Do not attempt a genuine long multi-thousand-tick emergent siege run — confirmed unnecessary; the
  real pipeline integration is provable deterministically in one tick.
- Do not duplicate `test_transformations.py`'s own pure-function coverage.
