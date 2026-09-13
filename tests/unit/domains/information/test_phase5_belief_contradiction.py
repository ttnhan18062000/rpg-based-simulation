"""
tests/unit/domains/information/test_phase5_belief_contradiction.py

Phase 5 — BeliefContradictionService unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import (
    CombatComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState, RegionState,
)
from src.core.strategic import LeadState, LeadCertainty
from src.domains.information.contradiction import BeliefContradictionService


def _entity(e_id):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    return b.build()


def _state(entities, **kwargs) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    defaults = dict(
        tick=1, seed=1, world_time=100, entities=ent_map,
        groups={}, regions={}, resource_nodes={}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={},
        local_scars={}, global_resources={}, town_tiles=(),
        building_tiles=(), terrain=(), home_storage={},
        town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=(), town_entity_ids=(),
    )
    defaults.update(kwargs)
    return AuthoritativeState(**defaults)


def test_failed_search_contradicts_lead():
    actor = _entity(1)
    
    # Pre-populate lead
    lead = LeadState(
        id="lead_1",
        kind="location",
        subject="moon_resin",
        detail="north_ruin",
        certainty=LeadCertainty.APPROXIMATE,
    )
    
    # Inject lead via build replace
    from src.core.strategic import StrategicComponent
    sc = StrategicComponent(leads={"lead_1": lead})
    
    # Rebuild entity with strategic component
    b = V2EntityBuilder(1)
    b.replace_strategic(sc)
    actor = b.build()
    
    state = _state([actor])
    
    obs = {
        "kind": "claim_failed_search",
        "subject": "moon_resin",
        "location_searched": "north_ruin",
    }
    
    res = BeliefContradictionService.detect(actor, obs, state)

    assert res.contradiction_detected is True
    assert res.lead_id == "lead_1"
    assert res.old_certainty == LeadCertainty.APPROXIMATE
    assert res.new_certainty == LeadCertainty.EXHAUSTED


def test_region_danger_seen_contradicts_lead_via_coordinate_detail():
    """
    TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING: `lead.detail`
    follows the declared "x,y" coordinate contract, resolved to a region id via
    resolve_location_lead_region_id() rather than compared directly against a
    region id string that no real producer ever emits.
    """
    from src.core.strategic import StrategicComponent

    lead = LeadState(
        id="lead_2",
        kind="location",
        subject="safe_road",
        detail="50,50",
        certainty=LeadCertainty.VAGUE,
    )
    sc = StrategicComponent(leads={"lead_2": lead})

    b = V2EntityBuilder(1)
    b.replace_strategic(sc)
    actor = b.build()

    region = RegionState(id="bandit_road", name="Bandit Road", bounds=(0, 0, 100, 100))
    state = _state([actor], regions={"bandit_road": region})

    obs = {
        "kind": "region_danger_seen",
        "subject": "safe_road",
        "region_id": "bandit_road",
    }

    res = BeliefContradictionService.detect(actor, obs, state)

    assert res.contradiction_detected is True
    assert res.lead_id == "lead_2"
    assert res.old_certainty == LeadCertainty.VAGUE
    assert res.new_certainty == LeadCertainty.EXHAUSTED
