---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP
artifact_type: investigation
tags: [determinism]
---

# Investigation — TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP

Re-verified `NavigationComponent` (`src/core/state.py:452-478`) against current code: 16 real fields
total (13 at original scoping time, +1 `place_id` added by `TCK-20260902-PLACE-SCHEMA-MIGRATION`, +2 the
original finding undercounted — `position` and `place_id` were already covered).

**`position` resolved first, per the ticket's own flagged priority**: it IS covered — as a top-level
`to_canonical_dict()` key (`"position": self.navigation.position`, line 846), not inside the
`"navigation"` sub-dict. Not the severe gap the original finding worried it might be.

Covered before this fix: `position` (top-level), `target`, `path`, `moved_recently`, `place_id` (5).
Uncovered: `movement_mode`, `last_failure_reason`, `wait_count`, `oscillation_count`, `last_position`,
`home_position`, `leash_radius`, `region_id`, `chase_ticks`, `max_chase_ticks`, `returning_home` (11).

**Field-by-field liveness check** (per the ticket's own instruction not to default-include): grepped
every real consumer site for each of the 11 fields before adding any of them.
- `region_id`: cached back-reference, gates `src/domains/memory/phase.py`, `src/domains/information/phase.py`,
  `src/engine/semantic_entity_index.py`, `src/engine/pipeline_phases/actions.py` (combat target region
  resolution), `src/observability/live/entity_inspector.py`.
- `movement_mode`: gates `src/engine/movement.py`, `src/engine/apply.py`, `src/engine/candidate_selector.py`,
  `src/engine/pipeline_phases/movement.py`, `src/systems/social_systems/appraisal.py`.
- `wait_count`/`oscillation_count`: gate congestion-recovery replanning in `src/engine/movement.py`
  (`wait_count >= 2`/`>= 5` triggers, `oscillation_count >= 3`), consumed in
  `src/systems/strategic_systems/work_queue.py`, `src/systems/strategic_systems/intelligence.py`,
  `src/observability/live/entity_inspector.py`, and exported via `src/api/presenters/state_presenter.py`.
- `last_position`: directly compared against the current target in `src/engine/movement.py`'s
  oscillation-detection logic.
- `home_position`/`leash_radius`/`chase_ticks`/`max_chase_ticks`/`returning_home`: gate mob-leash chase
  logic in `src/engine/rpg_depth.py` (`should_chase`/`should_return_home`-shaped checks); all four also
  explicitly copied by `ApplyPath._fast_replace_navigation` (`src/engine/apply.py:556-574`).
- `last_failure_reason`: feeds `StrategicIntelligenceSystem.infer_blockers()`
  (`src/systems/strategic_systems/intelligence.py:446`), which produces real `StrategicComponent.blockers`
  updates — an already-covered downstream field, confirming this one is a genuine independent input, not
  a redundant debug string.

None of the 11 are derived/reconstructable the way `StrategicComponent.profile` was in the parallel
Knowledge-gap fix — no field was excluded here.

**`ApplyPath._fast_replace_navigation` checked** (the exact class of bug the ticket flagged, hit once
before while adding `place_id`): already copies all 16 real fields correctly, including all 11 fields
this ticket adds hash coverage for. No fix needed there — confirmed, not assumed.

**Fixture-staleness impact assessed**: this fix changes `CanonicalStateHasher`'s output for any state
containing non-default `NavigationComponent` values, which changes `canonical_state_hash` in every
world's `world_compile_report.json` (added by idea 66's Stage A). Checked whether any test asserts an
exact `canonical_state_hash` literal against a committed baseline — none do; every consumer
(`test_world_compile_determinism.py`, `test_world_compiler.py`) recomputes the hash at test time and
compares against a fresh value, never a hardcoded string. No fixture regeneration needed, consistent with
the already-documented fixture-staleness pattern tracked separately in
`TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`.
