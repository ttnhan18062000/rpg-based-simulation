"""SimQ corpus-tier proof that idea 48 (Place-Type Transitions) fires end-to-end through the real
per-tick pipeline (TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS, M9 ticket 6 of 8).

**Correction, found during Investigate**: this ticket's own original scope text asserted "Place.kind
flips CITY->RUIN" driven by `faction_tension_overrides` against the `frontier_village_core` region.
That has no basis in real code. The real mechanism (`src/world/transformation.py::
TransformationService`) transforms `RegionState.kind` (a terrain type: FOREST/PLAINS/DESERT/
WASTELAND/MOUNTAIN/VOLCANIC/FROZEN_PEAKS/BURNT_FOREST) driven by `trauma_score`/
`calamity_intensity`/`stability`/`active_modifiers` -- it has nothing to do with `PlaceKind`
(CITY/CAMP/NEST/LAIR/RUIN/DUNGEON/LANDMARK, idea 66's separate settlement-classification system).
`frontier_village_core`'s own region declares `Place(kind="city")` -- a `PlaceKind` value entirely
unrelated to `RegionState.kind`, which every module composing `lifecycle_full_coverage_world` leaves
at its real default, `"FOREST"` (confirmed via grep, no module overrides it).

The already-shipped pure `TransformationService.apply_transformation()` function is already well
unit-tested (`tests/unit/world/test_transformations.py`) at the real threshold values. This test's
own value-add is proving the REAL per-tick pipeline wiring -- `WorldDynamicsSystem`'s
death-triggered trauma accumulation (`src/engine/world_dynamics.py:44-51`, any combat death in a
region adds +1.0 trauma) feeding into its own "Regional Transformations" step
(`world_dynamics.py:234-241`), and the real `region_transformed` observability event actually
firing -- not re-proving the pure function in isolation. Uses the same hand-seeded-combat-death
pattern already established by `tests/integration/world/test_regional_sovereignty.py`.

**Two further real behaviors found empirically while building this test, not assumed:**
1. **One-tick lag.** The "Regional Transformations" step reads `region.trauma_score` off the
   START-of-tick state -- it does not see this same tick's own `trauma_delta` before checking
   thresholds. A death that crosses a threshold therefore only transforms the region on the NEXT
   tick's own dynamics pass, once `ApplyPath.apply_generation()` has actually committed that delta.
   This test exercises that real 2-tick boundary rather than an artificially collapsed single tick.
2. **Real event-delivery path.** `region_transformed` is NOT observable via
   `EventExtractor.extract()` under default flags -- that function's own equivalent block is
   unconditionally skipped once `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` defaults `"ON"`. The real,
   always-live-by-default path is `WorldDynamicsShaper` in `event_shapers.py`'s Phase-1
   `SHAPER_REGISTRY`, invoked via `run_shadow_shapers()`. Confirmed via direct empirical
   verification, not inherited from the ticket's own citation.

**SOCIAL/GUILD-drop caveat -- does not apply here, disclosed rather than silently dropped.** The
ticket's own text warned that sustained COMBAT pressure over a long emergent run starves SOCIAL/
GUILD goal-selection. This test is a single-tick, deterministic, hand-seeded proof (this whole M9
batch's established precedent for mechanisms impractical to reach via full emergent/corpus play) --
it does not run long enough for that starvation effect to occur. A future ticket attempting a real
long emergent siege run against this same world should expect and tolerate that drop; this test does
not need to.

**Idea 57 (Living Legend Feedback Loop) is deliberately NOT tested here.** Re-confirmed still real:
zero hits for `heroism_score`/`LegendFact` consumption anywhere in `src/systems/strategic_systems/`
-- no live Perception/Motivation call site exists for this signal (the same already-disclosed gap
from idea 57's own M5 ticket, TCK-20260905-FAME-DERIVER-LEGEND-FACT, and M7's own scoping pass).
Fabricating a test against a mechanism that cannot fire would produce a vacuous or fabricated
assertion -- deferred instead, per this ticket's own explicit instruction.
"""
from __future__ import annotations

from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.core.builder import V2EntityBuilder
from src.engine.apply import ApplyPath
from src.engine.world_dynamics import WorldDynamicsSystem
from src.observability.event_shapers import run_shadow_shapers
from src.systems.world_systems.generator import EntityGenerator


def _build_state(trauma_score: float) -> AuthoritativeState:
    region = RegionState(
        id="whispering_wood",
        name="Whispering Wood",
        bounds=(0, 0, 50, 50),
        kind="FOREST",
        trauma_score=trauma_score,
    )
    victim = (
        V2EntityBuilder(1)
        .kind("citizen")
        .location(10.0, 10.0)
        .identity(role=EntityRole.CITIZEN, faction=Faction.TOWN_COUNCIL)
        .combat(hp=1, alive=True)
        .build()
    )
    return AuthoritativeState(
        tick=1, seed=42, entities={1: victim}, regions={"whispering_wood": region}
    )


def _kill_entity_1_update() -> StateUpdate:
    # Same real construction pattern as tests/integration/world/test_regional_sovereignty.py:
    # a hand-seeded combat-death EntityUpdate, routed through the real authoritative pipeline
    # rather than a full emergent multi-tick combat resolution.
    return StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, combat=CombatUpdate(outcome_kind="KILL", hp_delta=-20, alive_set=False)),
    })


def test_forest_region_transforms_to_burnt_forest_through_real_pipeline_after_a_combat_death():
    # Real, one-tick-lag pipeline behavior, discovered empirically and disclosed here rather than
    # assumed: WorldDynamicsSystem.resolve_dynamics()'s "4. Regional Transformations" step reads
    # region.trauma_score off the START-of-tick state (world_dynamics.py:236-241) -- it does NOT
    # see this SAME tick's own trauma_delta before checking thresholds. A death that pushes trauma
    # score across a threshold therefore only transforms the region on the NEXT tick's own dynamics
    # pass, once that trauma_delta has actually been committed via ApplyPath.apply_generation().
    # This test proves both real steps genuinely wired together across that real 2-tick boundary,
    # not a single artificially-collapsed tick.
    # Seeded at 49.5, not exactly 49.0: a small passive per-tick trauma decay elsewhere in the
    # pipeline (src/world/consequences.py, -0.0005/tick) would otherwise shave the post-death total
    # to 49.9995, just under the real 50.0 threshold -- confirmed empirically, not assumed. 49.5 +
    # 1.0 - 0.0005 clears the threshold with real margin.
    state = _build_state(trauma_score=49.5)
    update = _kill_entity_1_update()
    generator = EntityGenerator(seed=42)

    # Tick 1: the combat death commits trauma_score across the 50.0 threshold (no transformation
    # yet -- the threshold check this same tick still sees the pre-death, pre-decay value).
    refined_1 = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    state_after_death = ApplyPath.apply_generation(state, refined_1, next_tick=2)
    assert state_after_death.regions["whispering_wood"].kind == "FOREST"
    assert state_after_death.regions["whispering_wood"].trauma_score >= 50.0

    # Tick 2: no new deaths -- resolve_dynamics() now sees the already-committed 50.0 trauma_score
    # and the real transformation fires.
    refined_2 = WorldDynamicsSystem.resolve_dynamics(state_after_death, StateUpdate(), generator)
    next_state = ApplyPath.apply_generation(state_after_death, refined_2, next_tick=3)

    assert next_state.regions["whispering_wood"].kind == "BURNT_FOREST", (
        "trauma_score standing at exactly the real 50.0 threshold must cross "
        "FOREST->BURNT_FOREST on the next real dynamics pass"
    )

    # region_transformed's real live path is WorldDynamicsShaper (event_shapers.py), a Phase-1
    # push shaper delivered whenever ENABLE_PUSH_EVENT_SHAPERS is not OFF (the real, always-on-by-
    # default path) -- NOT EventExtractor.extract(), whose own equivalent block is unconditionally
    # skipped once ENABLE_PUSH_EVENT_SHAPERS_PHASE2 defaults "ON" (confirmed empirically). Call the
    # real live entry point, run_shadow_shapers(), rather than the flag-gated rollback path.
    events = run_shadow_shapers(state_after_death, refined_2, tick=3)
    transform_events = [e for e in events if e.event_type == "region_transformed"]
    assert transform_events, (
        "a real region_transformed observability event must fire alongside the real "
        "state transition -- the pipeline integration point this test exists to prove"
    )
    assert transform_events[0].payload["new_kind"] == "BURNT_FOREST"
    assert transform_events[0].payload["region_id"] == "whispering_wood"


def test_no_transformation_below_the_real_threshold_through_the_same_real_pipeline():
    state = _build_state(trauma_score=30.0)  # well under the 50.0 threshold even after +1.0
    update = _kill_entity_1_update()

    generator = EntityGenerator(seed=42)
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    next_state = ApplyPath.apply_generation(state, refined, next_tick=2)

    assert next_state.regions["whispering_wood"].kind == "FOREST", (
        "trauma_score staying under the real 50.0 threshold must NOT transform the region -- "
        "a real regression-catching floor, not a tautology"
    )

    events = run_shadow_shapers(state, refined, tick=2)
    assert not [e for e in events if e.event_type == "region_transformed"], (
        "no region_transformed event should fire when no real transformation occurred"
    )
