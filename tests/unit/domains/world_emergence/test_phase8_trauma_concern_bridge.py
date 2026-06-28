"""
E52F — TraumaRegionConcernBridge: regional trauma_score → DANGER ConcernState injection.

Ticket: TCK-20260628-E52F-TRAUMA-MOTIVATION
"""
from __future__ import annotations

import pytest
from dataclasses import replace

from src.core.state import AuthoritativeState, RegionState
from src.core.strategic import ConcernKind
from src.domains.world_emergence.services import TraumaRegionConcernBridge
from src.core.builder import V2EntityBuilder


THRESHOLD = TraumaRegionConcernBridge.TRAUMA_CONCERN_THRESHOLD   # 0.5
SCALE = TraumaRegionConcernBridge.URGENCY_SCALE                  # 50.0


def _region(rid: str, trauma: float = 0.0) -> RegionState:
    return RegionState(id=rid, name=rid, bounds=(0, 0, 100, 100), trauma_score=trauma)


def _entity_in_region(eid: int, region_id: str, alive: bool = True):
    e = V2EntityBuilder(eid).kind("worker").location(10.0, 10.0).combat(hp=80, max_hp=80).build()
    from dataclasses import replace as dc_replace
    nav = dc_replace(e.navigation, region_id=region_id)
    if not alive:
        from src.core.state import CombatComponent
        combat = dc_replace(e.combat, alive=False, hp=0)
        e = dc_replace(e, navigation=nav, combat=combat)
    else:
        e = dc_replace(e, navigation=nav)
    return e


def _state(tick: int, regions: dict, entities: dict) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=42, regions=regions, entities=entities)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_updates_when_no_regions():
    state = _state(tick=1, regions={}, entities={})
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=1)
    assert result == {}


def test_no_update_when_trauma_below_threshold():
    region = _region("forest", trauma=THRESHOLD)  # exactly at threshold → NOT above
    entity = _entity_in_region(1, "forest")
    state = _state(tick=1, regions={"forest": region}, entities={1: entity})
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=1)
    assert 1 not in result


def test_concern_injected_when_trauma_above_threshold():
    region = _region("forest", trauma=THRESHOLD + 0.1)
    entity = _entity_in_region(1, "forest")
    state = _state(tick=5, regions={"forest": region}, entities={1: entity})
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=5)

    assert 1 in result
    strat_upd = result[1]
    assert len(strat_upd.concerns_add_or_update) == 1
    concern = strat_upd.concerns_add_or_update[0]
    assert concern.id == "regional_trauma_forest"
    assert concern.kind == ConcernKind.DANGER
    assert concern.created_tick == 5


def test_urgency_scales_with_trauma():
    region = _region("badlands", trauma=25.0)  # 25 / 50 = 0.5
    entity = _entity_in_region(1, "badlands")
    state = _state(tick=1, regions={"badlands": region}, entities={1: entity})
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=1)

    concern = result[1].concerns_add_or_update[0]
    assert concern.urgency == pytest.approx(0.5)


def test_urgency_capped_at_one():
    region = _region("hellzone", trauma=200.0)  # 200 / 50 = 4.0 → capped at 1.0
    entity = _entity_in_region(1, "hellzone")
    state = _state(tick=1, regions={"hellzone": region}, entities={1: entity})
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=1)

    concern = result[1].concerns_add_or_update[0]
    assert concern.urgency == pytest.approx(1.0)


def test_dead_entity_excluded():
    region = _region("forest", trauma=10.0)
    entity = _entity_in_region(1, "forest", alive=False)
    state = _state(tick=1, regions={"forest": region}, entities={1: entity})
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=1)
    assert 1 not in result


def test_entity_without_region_id_excluded():
    region = _region("forest", trauma=10.0)
    entity = _entity_in_region(1, "forest")
    # Clear region_id
    from dataclasses import replace as dc_replace
    entity = dc_replace(entity, navigation=dc_replace(entity.navigation, region_id=None))
    state = _state(tick=1, regions={"forest": region}, entities={1: entity})
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=1)
    assert 1 not in result


def test_entity_in_safe_region_unaffected():
    safe = _region("meadow", trauma=0.1)
    unsafe = _region("warzone", trauma=20.0)
    entity_safe = _entity_in_region(1, "meadow")
    entity_unsafe = _entity_in_region(2, "warzone")
    state = _state(
        tick=1,
        regions={"meadow": safe, "warzone": unsafe},
        entities={1: entity_safe, 2: entity_unsafe},
    )
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=1)
    assert 1 not in result
    assert 2 in result


def test_concern_appears_within_one_tick_of_threshold_crossing():
    """Key E52F requirement: concern is injected on the same tick trauma crosses threshold."""
    region = _region("forest", trauma=1.0)  # 1 death = 1.0 trauma > 0.5
    entity = _entity_in_region(1, "forest")
    state = _state(tick=100, regions={"forest": region}, entities={1: entity})
    result = TraumaRegionConcernBridge.inject_concerns(state, current_tick=100)
    # Concern must be present: 1.0 > THRESHOLD (0.5), urgency = 1.0/50.0 = 0.02
    assert 1 in result
    concern = result[1].concerns_add_or_update[0]
    assert concern.created_tick == 100
    assert concern.urgency == pytest.approx(1.0 / SCALE)
