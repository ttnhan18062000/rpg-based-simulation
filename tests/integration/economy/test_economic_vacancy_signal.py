"""Integration tests for the economic-vacancy signal (TCK-20260903-ECONOMIC-VACANCY-SIGNAL,
idea 64 "The Empty Chair"). Exercises the real authoritative apply path (src/engine/apply.py) and
the real PP-20 consumer (TownResolutionSystem.resolve), not hand-constructed StateUpdate objects
in isolation.
"""
from dataclasses import replace

from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.engine.apply import ApplyPath
from src.engine.town_resolution import TownResolutionSystem
from src.systems.lifecycle import LifecycleSystem
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory


def _region(region_id="region_01"):
    return RegionState(id=region_id, name="Test Region", bounds=(0, 0, 100, 100))


def _filler_events(count, tick=1):
    return [
        WorldEvent(category=WorldEventCategory.ENTITY_DEATH, tick=tick, region_id="filler_region")
        for _ in range(count)
    ]


def test_vacancy_event_committed_through_authoritative_apply_path():
    """AC1: death of the sole SHOPKEEPER in a region commits a PRODUCTION_ROLE_VACATED WorldEvent
    through the real authoritative apply path (ApplyPath.apply_generation), landing in the
    post-apply AuthoritativeState.recent_world_events -- not merely constructed in isolation."""
    dying = (V2EntityBuilder(1)
             .location(10.0, 10.0)
             .identity(role=EntityRole.SHOPKEEPER)
             .lifecycle(age_ticks=1000, max_age_ticks=1000)
             .build())
    state = AuthoritativeState(tick=100, seed=42, entities={1: dying}, regions={"region_01": _region()})

    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
    next_state = ApplyPath.apply_generation(state, refined, 101, 101)

    vacancy_events = [
        e for e in next_state.recent_world_events
        if e.category == WorldEventCategory.PRODUCTION_ROLE_VACATED
    ]
    assert len(vacancy_events) == 1
    assert vacancy_events[0].region_id == "region_01"
    assert vacancy_events[0].subject == "1"
    assert vacancy_events[0].payload == {"vacated_role": float(int(EntityRole.SHOPKEEPER))}


def test_vacancy_signal_readable_by_consuming_system():
    """AC2: TownResolutionSystem.resolve (PP-20) actually reads state.recent_world_events and
    increments a per-region metric when a PRODUCTION_ROLE_VACATED event is present -- proven by
    reading it back from state, not constructing the consumer call in isolation with a hand-built
    event list disconnected from real state."""
    event = WorldEvent(
        category=WorldEventCategory.PRODUCTION_ROLE_VACATED,
        tick=99,
        region_id="region_01",
        subject="1",
        payload={"vacated_role": float(int(EntityRole.SHOPKEEPER))},
    )
    state = AuthoritativeState(
        tick=100, seed=42, entities={},
        regions={"region_01": _region()},
        recent_world_events=[event],
    )

    result = TownResolutionSystem.resolve(state, StateUpdate())

    assert result.metric_counters["economic_vacancy_detected_region_region_01"] == 1


def test_vacancy_remains_detectable_across_subsequent_tick_if_unfilled():
    """AC3: the vacancy signal is not auto-resolved -- it remains detectable across a subsequent
    tick purely because the underlying WorldEvent has not yet been evicted from
    recent_world_events. Per the architecture review's Review Revision point 1,
    `recent_world_events` is bounded by a global COUNT of WorldEvent objects
    (WORLD_EVENT_WINDOW = 500, src/engine/apply.py:335-338), not by elapsed ticks -- this test
    exercises that real count-based eviction boundary directly via ApplyPath.apply_generation,
    rather than standing in a 501-tick simulation loop as a false proxy for it."""
    vacancy_event = WorldEvent(
        category=WorldEventCategory.PRODUCTION_ROLE_VACATED,
        tick=1,
        region_id="region_01",
        subject="1",
        payload={"vacated_role": float(int(EntityRole.SHOPKEEPER))},
    )

    # Still-in-window case: vacancy event is the newest of exactly 500. Applying a StateUpdate
    # with zero new events must not evict anything already inside the window.
    prior_events_still_in_window = _filler_events(499) + [vacancy_event]
    assert len(prior_events_still_in_window) == 500
    prior_state = AuthoritativeState(
        tick=100, seed=42, entities={},
        regions={"region_01": _region()},
        recent_world_events=prior_events_still_in_window,
    )
    next_state = ApplyPath.apply_generation(prior_state, StateUpdate(), 101, 101)
    assert vacancy_event in next_state.recent_world_events

    # Evicted case: vacancy event is the oldest of exactly 500. Applying a StateUpdate carrying
    # ONE new filler event pushes it out, purely by event count, regardless of tick count.
    prior_events_about_to_evict = [vacancy_event] + _filler_events(499)
    assert len(prior_events_about_to_evict) == 500
    prior_state_2 = AuthoritativeState(
        tick=100, seed=42, entities={},
        regions={"region_01": _region()},
        recent_world_events=prior_events_about_to_evict,
    )
    one_new_event_update = StateUpdate(world_events_add=_filler_events(1, tick=101))
    next_state_2 = ApplyPath.apply_generation(prior_state_2, one_new_event_update, 101, 101)
    assert vacancy_event not in next_state_2.recent_world_events
    assert len(next_state_2.recent_world_events) == 500


def test_single_production_entity_town_regression_vacancy_detection_delta():
    """AC4 (revised, see tickets/inprogress/TCK-20260903-ECONOMIC-VACANCY-SIGNAL.md and
    plan.md's AC4 revision rationale): single-production-entity town, same seed, control vs.
    treatment across N ticks. This measures the vacancy-DETECTION-SIGNAL delta (Step 2 emission
    at PP-33 + Step 3 consumption at PP-20), NOT blacksmith crafting throughput --
    BlacksmithSystem.enforce (src/engine/blacksmith.py) remains entity-agnostic by design in this
    ticket (TOWN-017 stays a P0-protected, unchanged parity entry). This test would correctly
    fail if Step 2 or Step 3's wiring were removed, but makes no claim about crafted-item counts.
    """
    METRIC_KEY = "economic_vacancy_detected_region_region_01"
    N_TICKS = 3

    def _run(kill_at_first_tick: bool) -> int:
        entity = (V2EntityBuilder(1)
                  .location(10.0, 10.0)
                  .identity(role=EntityRole.SHOPKEEPER)
                  .lifecycle(age_ticks=0, max_age_ticks=100000)
                  .build())
        state = AuthoritativeState(tick=100, seed=42, entities={1: entity}, regions={"region_01": _region()})

        cumulative_vacancy_count = 0
        for i in range(N_TICKS):
            update = StateUpdate()
            if kill_at_first_tick and i == 0:
                kill_upd = CombatUpdate(outcome_kind="KILL", is_lethal=True)
                update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=kill_upd)})

            # Mirrors real pipeline phase order: PP-20 town_resolution runs before PP-33
            # lifecycle within the same tick (src/engine/pipeline.py).
            update = TownResolutionSystem.resolve(state, update)
            update = LifecycleSystem.resolve_lifecycle(state, update)

            cumulative_vacancy_count += update.metric_counters.get(METRIC_KEY, 0)

            next_tick = state.tick + 1
            state = ApplyPath.apply_generation(state, update, next_tick, next_tick)

        return cumulative_vacancy_count

    control_total = _run(kill_at_first_tick=False)
    treatment_total = _run(kill_at_first_tick=True)

    assert control_total == 0
    assert treatment_total > 0
