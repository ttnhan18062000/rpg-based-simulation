"""
E5 Pipeline Hardening Tests.
- RPG-1222, RPG-1224, RPG-1225: authoritative_pipeline
- RPG-1230, RPG-1231, RPG-1232, RPG-1233: rejection_logic
"""
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, ResourceNodeState, ItemStack, StrategicComponent, InventoryComponent
from src.core.enums import EntityRole, ReasonCode, Faction
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, ResourceTransferIntent, NavigationUpdate
from src.engine.pipeline_phases.actor_validity import ActorValidityPhase
from src.engine.pipeline_phases.occupancy import OccupancyPhase

from src.core.builder import V2EntityBuilder

def create_mock_entity(id, faction=Faction.HERO_GUILD, role=EntityRole.HERO, pos=(0,0), hp=100, readiness=100.0):
    return (V2EntityBuilder(id)
            .kind("ACTOR")
            .location(*pos)
            .combat(hp=hp, attack_range=1, readiness=readiness)
            .identity(faction=faction, role=role)
            .build())

# --- E5.1: Negative Case Hardening ---

def test_negative_case_stunned_actor_rejection():
    # RPG-1689: actor_validity_enforcement
    # RPG-0001: action_proposals_as_intents
    # RPG-0003: coerced_reason_models
    # RPG-0005: partial_rejection_support
    # RPG-0006: tick_outcome_preservation
    """
    Law:
        A stunned actor may not submit movement/navigation proposals.

    Scope:
        This test targets ActorValidityPhase directly.

    Why direct phase test:
        The full AuthoritativeApplyPipeline starts with TrustBoundaryPhase.
        TrustBoundaryPhase may strip direct raw movement before actor validity
        can inspect it. Therefore this test should not use the full pipeline
        when the law under test is specifically actor validity.

    Scenario:
        Entity 1 is stunned.
        It proposes a navigation target.

    Expected:
        ActorValidityPhase clears the navigation intent and records
        ATTACKER_STATUS_BLOCKED.
    """
    entity_id = 1

    e1 = create_mock_entity(entity_id, hp=100)

    e1 = replace(
        e1,
        identity=replace(
            e1.identity,
            properties={
                **dict(e1.identity.properties),
                "status_stunned": True,
            },
        ),
    )

    state = AuthoritativeState(
        tick=1,
        seed=1,
        entities={
            entity_id: e1,
        },
    )

    update = StateUpdate(
        entity_updates={
            entity_id: EntityUpdate(
                entity_id=entity_id,
                navigation=NavigationUpdate(
                    target_set=(1.0, 1.0),
                ),
            )
        }
    )

    refined = ActorValidityPhase.resolve(
        state,
        update,
    )

    refined_entity_update = refined.entity_updates[entity_id]

    assert refined_entity_update.new_position is None
    assert refined_entity_update.navigation is not None
    assert refined_entity_update.navigation.failure_reason == ReasonCode.ATTACKER_STATUS_BLOCKED
    assert refined_entity_update.navigation.clear_target is True
    assert refined_entity_update.navigation.clear_path is True

    assert refined.rejections_delta.get(
        ReasonCode.ATTACKER_STATUS_BLOCKED,
        0,
    ) == 1

    assert any(
        event.actor_id == entity_id
        and event.reason == ReasonCode.ATTACKER_STATUS_BLOCKED
        for event in refined.rejection_events
    )

def test_negative_case_depleted_node():
    # RPG-1690: negative_case_depleted_node
    e1 = create_mock_entity(1, pos=(1,1))
    node = ResourceNodeState(id=10, kind="iron_ore", position=(1,1), remaining_charges=0, max_charges=1, yields_item="iron_ore", required_ticks=1)
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1}, resource_nodes={10: node})
    intent = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)])
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent])})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    assert any(res.accepted is False and res.reason == "SOURCE_DEPLETED" for res in refined.entity_updates[1].intent_results)

# --- E5.2: Race Conditions ---

def test_race_condition_occupancy():
    # RPG-1691: race_condition_occupancy
    # RPG-0010: cardinal_occupancy_legality
    # RPG-0011: collision_rejection
    """
    Law:
        If multiple authoritative movement results claim the same destination
        tile in the same tick, the lowest entity id wins and all other claimants
        are rejected with OCCUPANCY_CONFLICT.

    Scope:
        This test targets OccupancyPhase directly.

    Why direct phase test:
        Full AuthoritativeApplyPipeline starts with TrustBoundaryPhase.
        Raw direct new_position proposals may be stripped before OccupancyPhase.
        This test intentionally provides already-authoritative final movement
        results to OccupancyPhase.

    Scenario:
        Entity 1 and entity 2 both claim tile (1, 1).
        Entity 1 has the lower id.

    Expected:
        Entity 1 keeps the position.
        Entity 2 is rejected with OCCUPANCY_CONFLICT.
    """
    e1 = create_mock_entity(1, pos=(0, 0))
    e2 = create_mock_entity(2, pos=(2, 2))

    state = AuthoritativeState(
        tick=1,
        seed=1,
        entities={
            1: e1,
            2: e2,
        },
    )

    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                new_position=(1, 1),
                moved_this_tick=True,
            ),
            2: EntityUpdate(
                entity_id=2,
                new_position=(1, 1),
                moved_this_tick=True,
            ),
        }
    )

    refined = OccupancyPhase.resolve(
        state,
        update,
    )

    assert refined.entity_updates[1].new_position == (1, 1)
    assert refined.entity_updates[1].moved_this_tick is True

    assert refined.entity_updates[2].new_position is None
    assert refined.entity_updates[2].moved_this_tick is False
    assert refined.entity_updates[2].navigation is not None
    assert refined.entity_updates[2].navigation.failure_reason == "OCCUPANCY_CONFLICT"

    assert refined.rejections_delta.get("OCCUPANCY_CONFLICT", 0) == 1

    assert any(
        event.actor_id == 2
        and event.action_kind == "MOVE"
        and event.reason == "OCCUPANCY_CONFLICT"
        for event in refined.rejection_events
    )

def test_race_condition_resource_access():
    # RPG-1692: race_condition_resource_access
    e1 = create_mock_entity(1, pos=(1,1))
    e2 = create_mock_entity(2, pos=(1,1))
    node = ResourceNodeState(id=10, kind="iron_ore", position=(1,1), remaining_charges=1, max_charges=1, yields_item="iron_ore", required_ticks=1)
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1, 2: e2}, resource_nodes={10: node})
    intent1 = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)])
    intent2 = ResourceTransferIntent(source_id=10, source_kind="NODE", items_add=[ItemStack("iron_ore", 1)])
    
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, resource_transfers=[intent1]),
        2: EntityUpdate(entity_id=2, resource_transfers=[intent2])
    })
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    assert refined.entity_updates[1].inventory.items_add[0].item_id == "iron_ore"
    assert any(res.accepted is False and res.reason == "SOURCE_DEPLETED" for res in refined.entity_updates[2].intent_results)

# --- E5.3: Idempotency ---

def test_cross_tick_idempotency():
    # RPG-1693: cross_tick_idempotency
    # RPG-0016: readiness_cadence_decoupling
    # RPG-0018: authoritative_move_cost
    # RPG-0020: movement_intent_vs_result
    e1 = create_mock_entity(1)
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1})
    
    intent = ResourceTransferIntent(source_id="Q1", source_kind="QUEST", items_add=[ItemStack("gold_coin", 10)], transaction_id="TX_123")
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent])})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    next_state = ApplyPath.apply_generation(state, refined, next_tick=2)
    
    # Retry in next tick
    refined2 = AuthoritativeApplyPipeline.refine(next_state, update)
    assert any(res.accepted is False and res.reason == ReasonCode.IDEMPOTENCY_VIOLATION for res in refined2.entity_updates[1].intent_results)

def test_in_tick_idempotency():
    e1 = create_mock_entity(1)
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1})
    intent = ResourceTransferIntent(source_id="Q1", source_kind="QUEST", items_add=[ItemStack("gold_coin", 10)], transaction_id="TX_123")
    
    # Duplicate intent in same update
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, resource_transfers=[intent, intent])})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    results = refined.entity_updates[1].intent_results
    assert len([r for r in results if r.accepted]) == 1
    assert len([r for r in results if not r.accepted and r.reason == ReasonCode.IDEMPOTENCY_VIOLATION]) == 1
