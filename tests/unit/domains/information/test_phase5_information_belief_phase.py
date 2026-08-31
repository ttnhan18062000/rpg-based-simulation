"""
tests/unit/domains/information/test_phase5_information_belief_phase.py

TCK-20260824-LEAD-CONTRADICTION-WIRING — production call-site tests for
InformationBeliefPhase.apply()'s new observation-synthesis branch (Steps 6/7 of
the plan). Confirms BeliefContradictionService.detect() is reachable from a real
per-tick phase, not just from a hand-constructed observation dict (AC2).
"""

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import (
    AuthoritativeState,
    CombatComponent,
    BiologicalComponent,
    PersonalityComponent,
    NavigationComponent,
    RegionState,
    LocalScarState,
)
from src.core.strategic import (
    LeadState,
    LeadCertainty,
    StrategicComponent,
    ProjectState,
    ProjectKind,
    ProjectStatus,
    ObjectiveState,
    ObjectiveKind,
    ObjectiveStatus,
)
from src.domains.information.phase import InformationBeliefPhase


def _base_builder(e_id):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    return b


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


def test_claim_failed_search_observation_triggers_belief_contradiction_via_production_path():
    """
    AC2: a claim_failed_search observation, synthesized from
    NavigationComponent.last_failure_reason + the actor's active ASK_INFORMATION-
    style objective whose target matches the lead's subject, reaches
    BeliefContradictionService.detect() via InformationBeliefPhase.apply() and is
    applied as a typed StrategicUpdate visible in the returned StateUpdate.
    """
    lead = LeadState(
        id="lead_1", kind="location", subject="moon_resin", detail="north_ruin",
        certainty=LeadCertainty.APPROXIMATE,
    )
    objective = ObjectiveState(
        id="obj_1", kind=ObjectiveKind.REACH_LOCATION, target="moon_resin",
        status=ObjectiveStatus.ACTIVE,
    )
    project = ProjectState(
        id="proj_1", kind=ProjectKind.INFORMATION_SEEKING, status=ProjectStatus.ACTIVE,
        objectives=[objective], active_objective_id="obj_1",
    )
    sc = StrategicComponent(
        leads={"lead_1": lead},
        projects={"proj_1": project},
        current_project_id="proj_1",
        current_objective_id="obj_1",
    )

    b = _base_builder(1)
    b.replace_strategic(sc)
    b.replace_navigation(NavigationComponent(last_failure_reason="target_unreachable"))
    actor = b.build()

    state = _state([actor])

    update = InformationBeliefPhase.apply(state, profiles=[])

    assert 1 in update.entity_updates
    ent_upd = update.entity_updates[1]
    assert ent_upd.strategic is not None
    leads_upd = ent_upd.strategic.leads_add_or_update
    assert len(leads_upd) == 1
    failed_lead = leads_upd[0]
    assert failed_lead.id == "lead_1"
    assert failed_lead.certainty == LeadCertainty.EXHAUSTED
    assert failed_lead.test_outcome == "FAILURE"
    assert failed_lead.tested is True


def test_region_danger_seen_observation_triggers_belief_contradiction_via_production_path():
    """
    AC2's second observation kind: a region_danger_seen observation, synthesized
    from NavigationComponent.region_id plus an active local scar inside the
    region's bounds, reaches BeliefContradictionService.detect() via
    InformationBeliefPhase.apply() for a VAGUE/APPROXIMATE-certainty location lead.
    """
    lead = LeadState(
        id="lead_2", kind="location", subject="safe_road", detail="bandit_road",
        certainty=LeadCertainty.VAGUE,
    )
    sc = StrategicComponent(leads={"lead_2": lead})

    b = _base_builder(1)
    b.replace_strategic(sc)
    b.replace_navigation(NavigationComponent(region_id="bandit_road"))
    actor = b.build()

    region = RegionState(id="bandit_road", name="Bandit Road", bounds=(0, 0, 100, 100))
    scar = LocalScarState(id=1, position=(50.0, 50.0), kind="RAID_DAMAGE")

    state = _state([actor], regions={"bandit_road": region}, local_scars={1: scar})

    update = InformationBeliefPhase.apply(state, profiles=[])

    assert 1 in update.entity_updates
    ent_upd = update.entity_updates[1]
    assert ent_upd.strategic is not None
    failed_lead = ent_upd.strategic.leads_add_or_update[0]
    assert failed_lead.id == "lead_2"
    assert failed_lead.certainty == LeadCertainty.EXHAUSTED
    assert failed_lead.test_outcome == "FAILURE"


def test_region_danger_seen_not_fired_for_precise_certainty_lead():
    """Negative case: a PRECISE-certainty lead is never degraded by region_danger_seen
    (matches BeliefContradictionService.detect()'s own VAGUE/APPROXIMATE-only guard)."""
    lead = LeadState(
        id="lead_3", kind="location", subject="safe_road", detail="bandit_road",
        certainty=LeadCertainty.PRECISE,
    )
    sc = StrategicComponent(leads={"lead_3": lead})

    b = _base_builder(1)
    b.replace_strategic(sc)
    b.replace_navigation(NavigationComponent(region_id="bandit_road"))
    actor = b.build()

    region = RegionState(id="bandit_road", name="Bandit Road", bounds=(0, 0, 100, 100))
    scar = LocalScarState(id=1, position=(50.0, 50.0), kind="RAID_DAMAGE")

    state = _state([actor], regions={"bandit_road": region}, local_scars={1: scar})

    update = InformationBeliefPhase.apply(state, profiles=[])

    ent_upd = update.entity_updates.get(1)
    assert ent_upd is None or ent_upd.strategic is None or not ent_upd.strategic.leads_add_or_update
