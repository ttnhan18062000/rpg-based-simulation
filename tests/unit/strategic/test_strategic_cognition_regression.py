import pytest
from dataclasses import replace
from src.core.enums import Faction, ReasonCode
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    CombatComponent, InventoryComponent, StrategicComponent, 
    BiologicalComponent, SocialComponent, NavigationComponent,
    LifecycleComponent, EntityRole
)
from src.core.strategic import (
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    BlockerState, LeadState, LeadCertainty, CognitionProfile
)
from src.engine.domain_logic import SimulationDomainLogic
from src.systems.strategic import StrategicIntelligenceSystem

def create_mock_entity(e_id, pos, faction=1, role=EntityRole.HERO):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(e_id)
        .kind("actor")
        .location(pos[0], pos[1])
        .identity(role=role)
        .identity(faction=faction)
        .combat(hp=100, max_hp=100)
        .combat(alive=True)
        .combat(readiness=100.0)
        .cognition(interruption_resistance=0.5, detour_breadth=3)
        .build())

def test_failed_attack_reports_out_of_range():
    """
    Verify that an out-of-range ATTACK is rejected by combat/action legality.

    Important:
        Latest src does not have AuthoritativeApplyPipeline._route_combat_intent().
        Combat actions are routed through _route_action_intent(), which calls
        SimulationDomainLogic.execute_action(...).

    This test only proves the combat failure is surfaced. It does not expect
    StrategicIntelligenceSystem to infer a blocker from ATTACK OUT_OF_RANGE,
    because latest infer_blockers() only handles navigation failures and
    transaction-style failures.
    """
    from src.engine.legality import LegalityServiceV2

    hero = create_mock_entity(
        1,
        (1.0, 1.0),
        faction=Faction.HERO_GUILD,
        role=EntityRole.HERO,
    )

    monster = create_mock_entity(
        2,
        (10.0, 10.0),
        faction=Faction.MONSTER_HORDE,
        role=EntityRole.MONSTER,
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: hero,
            2: monster,
        },
    )

    legal, reason = LegalityServiceV2.verify_attack_legality(
        hero,
        monster,
        state,
    )

    assert legal is False
    assert reason == ReasonCode.OUT_OF_RANGE or reason == "OUT_OF_RANGE"
    
def test_access_blocker_inference_on_navigation_failure():
    """
    Verify that a navigation failure generates an access blocker.

    Current latest-src behavior:
        StrategicIntelligenceSystem.infer_blockers(...) creates access blockers
        for navigation failures:

            PATH_NOT_FOUND
            STUCK
            OSCILLATING

    Fraud this catches:
        - failed movement does not become strategic blocker information
        - access blocker id/subject is not tied to failed target_position
        - detour system cannot later reason about blocked access
    """
    hero = create_mock_entity(
        1,
        (1.0, 1.0),
        faction=Faction.HERO_GUILD,
        role=EntityRole.HERO,
    )

    payload = {
        "action": "MOVE",
        "target_position": (10.0, 10.0),
    }

    strat_upd = StrategicIntelligenceSystem.infer_blockers(
        entity=hero,
        last_task="ENTITY_ACT",
        last_payload=payload,
        navigation_failure="PATH_NOT_FOUND",
        current_project=None,
    )

    assert strat_upd is not None
    assert any(
        blocker.kind == "access"
        for blocker in strat_upd.blockers_add_or_update
    )
    assert any(
        "blocker_access_10_10" == blocker.id
        for blocker in strat_upd.blockers_add_or_update
    )

def test_detour_suggestion_logic():
    """Verify that a blocker + lead triggers a detour project."""
    hero = create_mock_entity(1, (1.0, 1.0))
    # Add a material blocker
    blocker = BlockerState(id="blocker_mat_iron", kind="material", subject="iron", severity=1.0)
    # Add a location lead for iron
    lead = LeadState(id="lead_mine", kind="location", subject="iron", detail="mine_at_10_10", certainty=LeadCertainty.PRECISE)
    
    hero = replace(hero, strategic=replace(hero.strategic, 
        blockers={"blocker_mat_iron": blocker},
        leads={"lead_mine": lead},
        # Current project is crafting
        projects={"proj_craft": ProjectState(id="proj_craft", kind="crafting", status=ProjectStatus.ACTIVE, score=40.0)},
        current_project_id="proj_craft"
    ))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero})
    
    strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)
    
    assert strat_up.current_project_id_set.startswith("proj_detour")
    assert strat_up.current_objective_id_set.startswith("detour_blocker_mat_iron")
    
    # Check that crafting is suspended
    suspended = next(p for p in strat_up.projects_add_or_update if p.id == "proj_craft")
    assert suspended.status == ProjectStatus.SUSPENDED


def test_blocker_resolution_on_pickup():
    """
    Verify that acquiring a registered material resolves the matching material blocker.

    Important:
        The latest InventoryService only applies registered item ids.
        Use `iron_ore`, not plain `iron`, because `iron` is not in ItemRegistry.
    """
    hero = create_mock_entity(1, (1.0, 1.0))

    blocker = BlockerState(
        id="blocker_mat_iron_ore",
        kind="material",
        subject="iron_ore",
        severity=1.0,
        target_quantity=1,
    )

    hero = replace(
        hero,
        strategic=replace(
            hero.strategic,
            blockers={
                blocker.id: blocker,
            },
        ),
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: hero,
        },
    )

    from src.core.state import ItemStack
    from src.core.updates import InventoryUpdate, StateUpdate, EntityUpdate

    inv_up = InventoryUpdate(
        items_add=[
            ItemStack(item_id="iron_ore", quantity=1),
        ],
    )

    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                inventory=inv_up,
            )
        }
    )

    resolved_update = StrategicIntelligenceSystem.resolve_blockers(
        state,
        update,
    )

    hero_upd = resolved_update.entity_updates[1]

    assert hero_upd.strategic is not None
    assert "blocker_mat_iron_ore" in hero_upd.strategic.blockers_remove