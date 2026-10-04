# Compliance IDs: PERF-011
from __future__ import annotations

from typing import Dict, List

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.models.inventory import ItemStack
from src.core.movement_modes import MovementMode
from src.core.state import (
    AuthoritativeState, BuildingState, EntityState, RegionState, ResourceNodeState,
)
from src.core.strategic import (
    ProjectState, BlockerState, LeadState, ConcernState, CognitionProfile,
    BlockerKind, ProjectKind, ConcernKind
)

# Entity grid per 100x100 metropolis region: 5-tile pitch from offset 5 (5..95) in each axis.
_REGION_GRID_SIDE = 19


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
                role=EntityRole.WORKER,
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
        entities[new_id] = (
            V2EntityBuilder(new_id)
            .replace_identity(monster.identity)
            .replace_combat(monster.combat)
            .location(*monster.navigation.position)
            .build()
        )
        
    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
        resource_nodes=state_res.resource_nodes,
    )


def _region_free_slots(region: RegionState, occupied: set[tuple[int, int]]) -> List[tuple[float, float]]:
    """Grid tiles of one region not already held by a building or resource node, in row-major order."""
    x0, y0 = region.bounds[:2]
    slots = []
    for row in range(_REGION_GRID_SIDE):
        for col in range(_REGION_GRID_SIDE):
            pos = (x0 + 5.0 + col * 5, y0 + 5.0 + row * 5)
            if (int(pos[0]), int(pos[1])) not in occupied:
                slots.append(pos)
    return slots


def _spread_entities_into_regions(
    entities: Dict[int, EntityState],
    regions: Dict[str, RegionState],
    buildings: Dict[int, BuildingState],
    resource_nodes: Dict[int, ResourceNodeState],
    entity_count: int,
) -> None:
    """Move entity i to region i % region_count, onto that region's free slot i // region_count.

    build_mixed_state positioned entities near 0,0; spreading them out makes a better test. Building and
    resource-node tiles are skipped so no two objects share a tile. Mutates *entities* in place.
    """
    region_count = len(regions)
    occupied = {(int(b.position[0]), int(b.position[1])) for b in buildings.values()}
    occupied |= {(int(n.position[0]), int(n.position[1])) for n in resource_nodes.values()}
    free_slots = {r_idx: _region_free_slots(regions[f"region_{r_idx}"], occupied) for r_idx in range(region_count)}
    for i, entity in enumerate(list(entities.values())):
        r_idx, slot = i % region_count, i // region_count
        if slot >= len(free_slots[r_idx]):
            raise ValueError(
                f"build_metropolis_state: region_{r_idx} has {len(free_slots[r_idx])} free tiles but "
                f"entity_count={entity_count} needs more; raise region_count"
            )
        entities[entity.id] = (
            V2EntityBuilder(entity.id)
            .replace_navigation(entity.navigation)
            .replace_identity(entity.identity)
            .replace_combat(entity.combat)
            .replace_inventory(entity.inventory)
            .replace_lifecycle(entity.lifecycle)
            .location(*free_slots[r_idx][slot])
            .build()
        )


def build_metropolis_state(
    *,
    entity_count: int = 1000,
    region_count: int = 50,
    buildings_per_region: int = 20,
    seed: int = 42
) -> AuthoritativeState:
    """
    Build a massive metropolis state with governance, buildings, and mixed work.
    """
    # 1. Base Mixed State
    state = build_mixed_state(entity_count=entity_count, seed=seed)
    entities = dict(state.entities) # Ensure mutable copy
    
    # 2. Add Regions
    regions = {}
    for i in range(region_count):
        r_id = f"region_{i}"
        x = (i % 10) * 100
        y = (i // 10) * 100
        regions[r_id] = RegionState(
            id=r_id,
            name=f"District {i}",
            bounds=(float(x), float(y), float(x + 100), float(y + 100)),
            owner_faction_id=Faction.HERO_GUILD if i % 2 == 0 else Faction.MONSTER_HORDE,
            hazard_level=0.1 if i % 5 == 0 else 0.0
        )
        
    # 3. Add Buildings
    buildings = {}
    b_id_counter = 1
    for r_id, region in regions.items():
        for b in range(buildings_per_region):
            bx = region.bounds[0] + (b % 5) * 10 + 5
            by = region.bounds[1] + (b // 5) * 10 + 5
            buildings[b_id_counter] = BuildingState(
                id=b_id_counter,
                kind="inn" if b % 2 == 0 else "tavern",
                position=(bx, by),
                functional=True
            )
            b_id_counter += 1
            
    # 4. Global Resources
    global_resources = {
        "faction_hero_guild_gold": 1000000.0,
        "faction_monster_horde_gold": 1000000.0
    }
    
    # 5. Distribute entities into regions
    _spread_entities_into_regions(entities, regions, buildings, state.resource_nodes, entity_count)

    # 6. Mark town tiles
    town_tiles = set()
    building_tiles = {}
    for b in buildings.values():
        bx, by = int(b.position[0]), int(b.position[1])
        town_tiles.add((bx, by))
        building_tiles[(bx, by)] = b.kind

    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
        regions=regions,
        buildings=buildings,
        global_resources=global_resources,
        town_tiles=town_tiles,
        building_tiles=building_tiles
    )


SCENARIO_BUILDERS = {
    "idle": build_idle_state,
    "movement": build_movement_state,
    "resource": build_resource_state,
    "combat": build_combat_arena_state,
    "strategic": build_strategic_state,
    "mixed": build_mixed_state,
    "metropolis": build_metropolis_state,
}
