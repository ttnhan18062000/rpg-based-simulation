from __future__ import annotations

from typing import Dict, List

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.models.inventory import ItemStack
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, ResourceNodeState, EntityState
from src.core.strategic import (
    ProjectState, BlockerState, LeadState, ConcernState, CognitionProfile,
    BlockerKind, ProjectKind, ConcernKind
)


def build_idle_state(
    *,
    entity_count: int,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a state with many active entities and no intentional work pressure.

    Purpose:
        Measures base engine overhead.
    """
    entities = {
        entity_id: (
            V2EntityBuilder(entity_id)
            .kind("hero")
            .location(float(entity_id % 100), float(entity_id // 100))
            .identity(
                role=EntityRole.HERO,
                faction=Faction.HERO_GUILD,
            )
            .combat(
                hp=100,
                max_hp=100,
                alive=True,
                readiness=100.0,
            )
            .lifecycle(active=True)
            .build()
        )
        for entity_id in range(1, entity_count + 1)
    }

    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
    )


def build_resource_state(
    *,
    entity_count: int,
    node_count: int,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a resource-heavy state.

    Purpose:
        Measures resource-node scanning, interaction, transfer resolution,
        and inventory handling.
    """
    entities = {
        entity_id: (
            V2EntityBuilder(entity_id)
            .kind("hero")
            .location(float(entity_id % 100), float(entity_id // 100))
            .identity(
                role=EntityRole.HERO,
                faction=Faction.HERO_GUILD,
            )
            .inventory(
                items=[
                    ItemStack(item_id="junk", quantity=1),
                ],
                max_slots=20,
            )
            .combat(
                hp=100,
                max_hp=100,
                alive=True,
                readiness=100.0,
            )
            .lifecycle(active=True)
            .build()
        )
        for entity_id in range(1, entity_count + 1)
    }

    resource_nodes = {
        node_id: ResourceNodeState(
            id=node_id,
            kind="iron_ore_node",
            position=(float(node_id % 100), float(node_id // 100)),
            remaining_charges=10,
            max_charges=10,
            yields_item="iron_ore",
            required_ticks=1,
        )
        for node_id in range(1000, 1000 + node_count)
    }

    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
        resource_nodes=resource_nodes,
    )


def build_movement_state(
    *,
    entity_count: int,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a movement-heavy state.

    Purpose:
        Measure movement/path/occupancy costs.
    """
    # Use a grid layout to ensure no initial occupancy conflicts
    entities = {}
    for i in range(entity_count):
        entity_id = i + 1
        x, y = float(i % 100), float(i // 100)
        # Target is 10 tiles away to ensure sustained movement
        tx, ty = x + 10.0, y + 10.0
        
        entities[entity_id] = (
            V2EntityBuilder(entity_id)
            .kind("hero")
            .location(x, y)
            .navigation(
                target=(tx, ty),
                movement_mode=MovementMode.WANDER # Or another mode that triggers pathing
            )
            .identity(
                role=EntityRole.HERO,
                faction=Faction.HERO_GUILD,
            )
            .combat(
                hp=100,
                max_hp=100,
                alive=True,
                readiness=100.0,
            )
            .lifecycle(active=True)
            .build()
        )

    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
    )


def build_combat_arena_state(
    *,
    team_a_count: int,
    team_b_count: int,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a combat-heavy arena state.

    Purpose:
        Measure action routing, legality, and combat resolution.
    """
    entities = {}
    
    # Team A (Heroes)
    for i in range(team_a_count):
        entity_id = i + 1
        entities[entity_id] = (
            V2EntityBuilder(entity_id)
            .kind("hero")
            .location(0.0, float(i))
            .identity(
                role=EntityRole.HERO,
                faction=Faction.HERO_GUILD,
            )
            .combat(
                hp=100,
                max_hp=100,
                atk=20,
                def_stat=10,
                alive=True,
                readiness=100.0,
            )
            .lifecycle(active=True)
            .build()
        )
        
    # Team B (Monsters)
    for i in range(team_b_count):
        entity_id = team_a_count + i + 1
        entities[entity_id] = (
            V2EntityBuilder(entity_id)
            .kind("monster")
            .location(5.0, float(i)) # Close enough to trigger combat
            .identity(
                role=EntityRole.MONSTER,
                faction=Faction.MONSTER_HORDE,
            )
            .combat(
                hp=100,
                max_hp=100,
                atk=20,
                def_stat=10,
                alive=True,
                readiness=100.0,
            )
            .lifecycle(active=True)
            .build()
        )

    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
    )


def build_strategic_state(
    *,
    entity_count: int,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a strategic-heavy state.

    Purpose:
        Measure blocker inference, detour, project updates, leads/concerns.
    """
    entities = {}
    for i in range(entity_count):
        entity_id = i + 1
        
        # Add some mock strategic data
        blockers = {"B1": BlockerState(id="B1", kind=BlockerKind.MATERIAL, subject="iron_ore", severity=0.5)}
        leads = {"L1": LeadState(id="L1", kind="location", subject="iron_ore_node")}
        concerns = {"C1": ConcernState(id="C1", kind=ConcernKind.HUNGER)}
        projects = {"P1": ProjectState(id="P1", kind=ProjectKind.EXPLORATION)}
        
        entities[entity_id] = (
            V2EntityBuilder(entity_id)
            .kind("hero")
            .location(float(i % 100), float(i // 100))
            .identity(
                role=EntityRole.HERO,
                faction=Faction.HERO_GUILD,
            )
            .strategic(
                blockers=blockers,
                leads=leads,
                concerns=concerns,
                projects=projects,
            )
            .combat(
                hp=100,
                max_hp=100,
                alive=True,
                readiness=100.0,
            )
            .lifecycle(active=True)
            .build()
        )

    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
    )


def build_mixed_state(
    *,
    entity_count: int,
    seed: int = 42,
) -> AuthoritativeState:
    """
    Build a realistic mixed simulation state.
    """
    # Simplified mix: 40% heroes, 30% monsters, 30% nodes
    hero_count = int(entity_count * 0.4)
    monster_count = int(entity_count * 0.3)
    node_count = int(entity_count * 0.3)
    
    state_idle = build_idle_state(entity_count=hero_count, seed=seed)
    state_combat = build_combat_arena_state(team_a_count=0, team_b_count=monster_count, seed=seed + 1)
    state_res = build_resource_state(entity_count=0, node_count=node_count, seed=seed + 2)
    
    entities = {**state_idle.entities}
    # Offset monster IDs to avoid collision
    for eid, monster in state_combat.entities.items():
        new_id = hero_count + eid
        entities[new_id] = V2EntityBuilder(new_id).replace_identity(monster.identity).replace_combat(monster.combat).location(*monster.position).build()
        
    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
        resource_nodes=state_res.resource_nodes,
    )
