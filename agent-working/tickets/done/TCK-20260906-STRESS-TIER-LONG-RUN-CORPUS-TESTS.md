---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS
phase: done
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS

## Title
Idea 48 stress-tier corpus test (ready); idea 57 corpus test blocked on already-known dormant-wiring gap

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 6 of 8. Both ideas need longer-run/
stress-tier corpus extensions per the original epic doc, but re-verification, 2026-09-06, found their
readiness differs:
- **Idea 48 (Place-Type Transitions)** — confirmed shipped (M2's epic doc,
  `rpg_m2_foundational_systems_epic.md`), and its `region_transformed` event confirmed real and live
  (`src/observability/event_extractor.py`, `event_shapers.py`,
  `src/simulation_quality/scorers/world_dynamics.py`). Ready to test.
- **Idea 57 (Living Legend Feedback Loop)** — `heroism_score` is real (`src/core/models/social.py`),
  but the corpus test's own required mechanism (a Townsperson's Motivation & Doctrine route bias
  shifting after a fame-perception event) is NOT live: zero hits for any Perception/Motivation
  call site consuming `heroism_score`/`LegendFact` output anywhere in `src/systems/
  strategic_systems/` or `src/domains/fame/`. This matches the already-known, already-disclosed gap
  from idea 57's own M5 ticket and M7's own scoping pass (`PerceptionUpdatePhase`/
  `MotivationBiasService` have zero live pipeline call sites for this signal) — not a new finding,
  but confirmed still blocking this specific corpus test.

## Scope
- **Idea 48**: extend `lifecycle_full_coverage_world` (41 entities, 8 regions, stress tier, 7
  factions). Author a `faction_tension_overrides` entry driving sustained conflict against the
  `frontier_village_core` region; since this world's only committed run_key is 200t, a siege reaching
  completion needs a separate, longer manual run via the long-run tooling, outside
  `grade_anchors.json`. Assert `Place.kind` flips CITY->RUIN and `region_transformed` fires. **Real
  risk to carry into the assertion design**: this world's own prior investigation found sustained
  COMBAT pressure starves SOCIAL/GUILD goal-selection for the whole run — tolerate SOCIAL/GUILD
  dropping in this specific test, don't treat it as a false regression.
- **Idea 57**: do NOT author this corpus test yet — it cannot currently produce a real, non-vacuous
  assertion. Document the blocker in the M9 epic doc (already partially done via the dormant-idea
  cross-references elsewhere this session) and leave a forward pointer to whichever future ticket
  builds the Perception/Motivation live wiring.

## Out of Scope
- Building idea 57's missing Perception/Motivation wiring — that is real, separate future work
  (already disclosed by idea 57's own M5 ticket as out of that ticket's scope too).
- Any other item from M9's scope.

## Acceptance Criteria
- [x] Idea 48's corpus test is authored and passing, with the SOCIAL/GUILD-drop caveat explicitly
      documented in the test itself (a comment or assertion tolerance), not silently ignored.
- [x] Idea 57's corpus test is explicitly deferred with a written reason (dormant wiring gap), not
      silently dropped or fabricated against a mechanism that doesn't fire.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (idea 57's own ticket, already disclosed this same gap)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS/`

## Related Code Areas
- `src/simulation_quality/scorers/world_dynamics.py`
- `data/content/world_modules/` (`lifecycle_full_coverage_world`)
- `src/world/transformation.py`, `src/engine/world_dynamics.py`, `src/observability/event_shapers.py`

## Assumptions / Open Questions
- None — the idea-48 correction below is evidence-based, not a judgment call left open.

## Implementation Notes

**Idea 48 — MAJOR CORRECTION, confirmed and applied.** This ticket's own original scope text
("Assert `Place.kind` flips CITY->RUIN" driven by `faction_tension_overrides` against
`frontier_village_core`) has no basis in real code. The real mechanism
(`src/world/transformation.py::TransformationService`) transforms `RegionState.kind` (a terrain
type: FOREST/PLAINS/DESERT/WASTELAND/MOUNTAIN/VOLCANIC/FROZEN_PEAKS/BURNT_FOREST) driven by
`trauma_score`/`calamity_intensity`/`stability`/`active_modifiers` — it has nothing to do with
`PlaceKind` (CITY/CAMP/NEST/LAIR/RUIN/DUNGEON/LANDMARK, idea 66's separate settlement-classification
system, already found to be a distinct concept by this same M9 batch's ticket 5). No module
composing `lifecycle_full_coverage_world` overrides `RegionState.kind` away from its real default,
`"FOREST"` — a genuinely transformable kind. `frontier_village_core`'s own `Place(kind="city")` is
unrelated.

The real, already-shipped pure `TransformationService.apply_transformation()` function was already
well unit-tested (`tests/unit/world/test_transformations.py`) at the real threshold values. This
ticket's corrected value-add proves the REAL per-tick pipeline wiring instead: `WorldDynamicsSystem`'s
death-triggered trauma accumulation (`src/engine/world_dynamics.py:44-51`, any combat death in a
region adds +1.0 trauma) feeding its own "Regional Transformations" step, and the real
`region_transformed` event actually firing — using the same hand-seeded-combat-death construction
pattern already established by `tests/integration/world/test_regional_sovereignty.py`.

Two further real behaviors found empirically while building the test (disclosed in the test's own
module docstring, not silently discovered and dropped):
1. **One-tick lag** — the Regional Transformations step reads `trauma_score` off the START-of-tick
   state, so a death crossing a threshold only transforms the region on the NEXT tick's dynamics
   pass, once the delta is actually committed. The test exercises this real 2-tick boundary rather
   than an artificially collapsed single tick.
2. **Real event-delivery path** — `region_transformed` is NOT observable via
   `EventExtractor.extract()` under default flags (that block is unconditionally skipped once
   `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` defaults `"ON"`); the real, always-live path is
   `WorldDynamicsShaper` (`event_shapers.py`'s Phase-1 `SHAPER_REGISTRY`), invoked via
   `run_shadow_shapers()`.

**SOCIAL/GUILD-drop caveat — does not apply to the corrected design, disclosed rather than silently
dropped.** That caveat was written against the original scope's assumption of a long, emergent
multi-hundred/thousand-tick siege run. The corrected test is a single-scenario, deterministic,
2-tick, hand-seeded proof (matching this whole M9 batch's established precedent for mechanisms
impractical to reach via full emergent/corpus play) — it does not run long enough for a goal-selection
starvation effect to occur or need tolerating. This reasoning is stated directly in the test file's
own docstring so a future ticket attempting a genuine long emergent siege run against this world
knows to expect and tolerate that drop.

No new corpus world, registered run_key, or long-run manual invocation via
`simq_long_run_observation.py` was needed — the real pipeline integration point is provable
deterministically in two ticks.

**Idea 57** — re-confirmed still blocked (zero hits for `heroism_score`/`LegendFact` consumption
anywhere in `src/systems/strategic_systems/`). No test authored; the gap and its forward pointer are
documented in the new test file's own module docstring rather than fabricating a vacuous assertion.

No production code changed (`behavior_changed=false`); no parity-ledger entry needed.

## Test Summary
- New: `tests/simulation_quality/test_region_transformation_pipeline_corpus.py` — 2 tests
  (positive: FOREST->BURNT_FOREST transformation + `region_transformed` event fires through the
  real 2-tick pipeline; negative: trauma below threshold produces neither).
- Regression: `tests/simulation_quality/`, `tests/unit/world/`, `tests/unit/observability/` — 1906
  passed, 86 skipped, 0 failed (1 pre-existing, unrelated warning).
- `tests/unit/world/test_transformations.py` and `tests/integration/world/test_regional_sovereignty.py`
  (this ticket's own structural precedents) — confirmed still green, unmodified.

## Files Changed
- `tests/simulation_quality/test_region_transformation_pipeline_corpus.py` (new)

## Completion Summary
Idea 48's corpus test authored and passing after a major, evidence-based correction to the ticket's
own original scope (CITY->RUIN via `PlaceKind` has no basis in real code; the real mechanism is
`RegionState.kind` terrain transformation via trauma/calamity). Proves the real per-tick pipeline
integration end-to-end (trauma accumulation -> transformation -> event emission) rather than
re-testing the already-covered pure function, and discloses two further real pipeline behaviors
(one-tick transformation lag, the real Phase-1-shaper event-delivery path) found empirically during
implementation. Idea 57 correctly left untested with its dormant-wiring gap re-confirmed and
documented. No production code changed.
