# Compliance IDs: WORLD-050, WORLD-051, WORLD-052
from __future__ import annotations

import json
import time
import random
from typing import Optional, Any, Dict, List, Set

from src.core.state import (
    AuthoritativeState,
    RegionState,
    EntityState,
    BuildingState,
    ResourceNodeState,
    InventoryComponent
)
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.replay.fingerprint import StateFingerprinter
from src.worldbuilding.schema import WorldSpec
from src.core.quests import QuestState, QuestStatus, QuestKind, RewardState
from src.core.strategic import ProjectKind


def get_role_enum(role_str: str) -> EntityRole:
    """Map raw role string to EntityRole enum."""
    r = role_str.upper()
    if "HERO" in r:
        return EntityRole.HERO
    elif "SHOP" in r or "STORE" in r:
        return EntityRole.SHOPKEEPER
    elif "MONSTER" in r:
        return EntityRole.MONSTER
    elif "CITIZEN" in r or "CIVILIAN" in r:
        return EntityRole.CITIZEN
    elif "WORKER" in r or "PEASANT" in r:
        return EntityRole.WORKER
    elif "GUARD" in r:
        return EntityRole.GUARD
    return EntityRole.CITIZEN


def get_faction_enum(faction_str: str) -> Faction:
    """Map raw faction string to Faction enum."""
    f = faction_str.upper()
    if "HERO" in f or "GUILD" in f or "VILLAGE" in f:
        return Faction.HERO_GUILD
    elif "MONSTER" in f or "HORDE" in f or "HOSTILE" in f:
        return Faction.MONSTER_HORDE
    elif "COUNCIL" in f or "TOWN" in f:
        return Faction.TOWN_COUNCIL
    return Faction.NEUTRAL


def get_quest_kind(kind_str: str) -> QuestKind:
    """Map raw quest kind string to QuestKind enum."""
    k = kind_str.upper()
    if "HUNT" in k:
        return QuestKind.HUNT
    elif "GATHER" in k:
        return QuestKind.GATHER
    elif "EXPLORE" in k:
        return QuestKind.EXPLORE
    elif "LIBERATE" in k:
        return QuestKind.LIBERATE
    elif "BOUNTY" in k:
        return QuestKind.BOUNTY
    return QuestKind.EXPLORE


class WorldCompiler:
    """
    Deterministic World Compiler that transforms a validated WorldSpec into
    an engine AuthoritativeState.
    """

    @staticmethod
    def compile(
        spec: WorldSpec,
        seed: int,
        output_report_path: Optional[str] = None
    ) -> tuple[AuthoritativeState, dict]:
        """
        Compile the given WorldSpec into a fully populated AuthoritativeState.

        Args:
            spec: The validated WorldSpec object.
            seed: RNG seed for deterministic placement.
            output_report_path: Optional file path to save compile report JSON.

        Returns:
            A tuple of (AuthoritativeState, report_dict)
        """
        start_time = time.perf_counter()

        # 0. Initialize deterministic RNG using standard library random
        rng = random.Random(seed)

        # 1. Compile map topology
        terrain: Dict[tuple[int, int], str] = {}
        for x in range(spec.topology.width):
            for y in range(spec.topology.height):
                terrain[(x, y)] = "PLAIN"

        # 2. Compile regions & terrain painting
        regions: Dict[str, RegionState] = {}
        town_tiles: Set[tuple[int, int]] = set()

        for r_spec in spec.regions:
            min_x, min_y, max_x, max_y = r_spec.bounds
            
            # Default to "GRASS" if terrain not specified on RegionSpec
            r_terrain = getattr(r_spec, "terrain", "GRASS")
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    if 0 <= x < spec.topology.width and 0 <= y < spec.topology.height:
                        terrain[(x, y)] = r_terrain
                        if r_spec.type == "town":
                            town_tiles.add((x, y))

            # Map RegionSpec to RegionState
            regions[r_spec.id] = RegionState(
                id=r_spec.id,
                name=r_spec.id.replace("_", " ").title(),
                bounds=(r_spec.bounds[0], r_spec.bounds[1], r_spec.bounds[2], r_spec.bounds[3]),
                kind=r_spec.type.upper(),
                influence=100.0 if r_spec.type == "town" else 0.0,
                owner_faction_id=Faction.HERO_GUILD if r_spec.type == "town" else None,
                hazard_level=getattr(r_spec, "hazard_level", 0.0)
            )

        # 3. Compile factions (Initialize starting vaults in global_resources)
        global_resources: Dict[str, float] = {}
        for f_spec in spec.factions:
            faction_enum = get_faction_enum(f_spec.id)
            if faction_enum == Faction.HERO_GUILD:
                global_resources["faction_hero_guild_gold"] = 1000.0
            elif faction_enum == Faction.MONSTER_HORDE:
                global_resources["faction_monster_horde_gold"] = 1000.0
            elif faction_enum == Faction.TOWN_COUNCIL:
                global_resources["faction_town_council_gold"] = 1000.0
            else:
                global_resources[f"faction_{f_spec.id.lower()}_gold"] = 1000.0

        # 4. Compile resources
        resource_nodes: Dict[int, ResourceNodeState] = {}
        next_resource_id = 10000
        for res_spec in spec.resources:
            region_id = res_spec.region
            region = regions.get(region_id)
            if region:
                min_x, min_y, max_x, max_y = region.bounds
                x = rng.randint(min_x, max_x)
                y = rng.randint(min_y, max_y)

                resource_nodes[next_resource_id] = ResourceNodeState(
                    id=next_resource_id,
                    kind=res_spec.resource_type,
                    position=(float(x), float(y)),
                    yields_item=res_spec.resource_type,
                    remaining_charges=res_spec.count,
                    max_charges=res_spec.count,
                    required_ticks=10,
                    cooldown_remaining=0
                )
                next_resource_id += 1

        # 5. Compile buildings
        buildings: Dict[int, BuildingState] = {}
        blocked_tiles: Set[tuple[int, int]] = set()
        next_building_id = 20000
        for bld_spec in spec.buildings:
            region_id = bld_spec.region
            region = regions.get(region_id)
            if region:
                min_x, min_y, max_x, max_y = region.bounds
                x = rng.randint(min_x, max_x)
                y = rng.randint(min_y, max_y)

                buildings[next_building_id] = BuildingState(
                    id=next_building_id,
                    kind=bld_spec.type,
                    position=(float(x), float(y)),
                    hp=500,
                    max_hp=500,
                    functional=True
                )
                blocked_tiles.add((x, y))
                next_building_id += 1

        # 6. Compile entities (populations)
        entities: Dict[int, EntityState] = {}
        town_entity_ids: Set[int] = set()
        next_entity_id = 1
        for pop_spec in spec.entities:
            region_id = pop_spec.spawn_region
            region = regions.get(region_id)
            if region:
                min_x, min_y, max_x, max_y = region.bounds
                for _ in range(pop_spec.count):
                    x = rng.randint(min_x, max_x)
                    y = rng.randint(min_y, max_y)

                    builder = (
                        V2EntityBuilder(next_entity_id)
                        .kind(pop_spec.role.lower())
                        .location(float(x), float(y))
                        .identity(
                            role=get_role_enum(pop_spec.role),
                            faction=get_faction_enum(pop_spec.faction),
                            properties={"spawn_region": pop_spec.spawn_region}
                        )
                        .combat(
                            hp=100,
                            max_hp=100,
                            atk=10,
                            attack_range=1,
                            alive=True,
                            readiness=100.0
                        )
                        .lifecycle(active=True)
                    )
                    entities[next_entity_id] = builder.build()
                    if region.kind == "TOWN":
                        town_entity_ids.add(next_entity_id)
                    next_entity_id += 1

        # 7. Compile quests and run post-compile validations
        compiled_quests: List[QuestState] = []
        warnings: List[str] = []

        for quest_idx, q_data in enumerate(spec.quests):
            qid = q_data.get("id", f"quest_{quest_idx}")
            qkind_str = q_data.get("kind", "EXPLORE").upper()
            qkind = get_quest_kind(qkind_str)

            # Quest referential warnings
            target_region = q_data.get("target_region_id")
            if target_region and target_region not in regions:
                warnings.append(f"Quest '{qid}' references unknown target region '{target_region}'")

            target_faction = q_data.get("target_faction")
            if target_faction:
                faction_ids = {f.id for f in spec.factions}
                if target_faction not in faction_ids:
                    warnings.append(f"Quest '{qid}' references unknown target faction '{target_faction}'")

            target_role = q_data.get("target_role")
            if target_role:
                roles = {e.role for e in spec.entities}
                if target_role not in roles:
                    warnings.append(f"Quest '{qid}' references unknown target entity role '{target_role}'")

            target_resource = q_data.get("target_resource_type")
            if target_resource:
                resource_types = {r.resource_type for r in spec.resources}
                if target_resource not in resource_types:
                    warnings.append(f"Quest '{qid}' references unknown resource type '{target_resource}'")

            metadata = q_data.get("metadata", {})
            if "target_position" in q_data:
                metadata["target_position"] = q_data["target_position"]
            if target_region:
                metadata["target_region_id"] = target_region

            reward_data = q_data.get("reward", {})
            reward = RewardState(
                xp=reward_data.get("xp", 0),
                gold=reward_data.get("gold", 0),
                items=reward_data.get("items", [])
            )

            q_state = QuestState(
                id=qid,
                kind=ProjectKind.QUEST,
                quest_kind=qkind,
                quest_status=QuestStatus.ACTIVE,
                goal_value=float(q_data.get("goal_value", 1.0)),
                current_value=0.0,
                reward=reward,
                name=q_data.get("name", qid),
                metadata=metadata
            )
            compiled_quests.append(q_state)

            # Stage 8: Strategic Setup (assign quest projects to matching entities)
            assignee = q_data.get("assignee")
            if assignee:
                for ent in entities.values():
                    match = False
                    if str(ent.id) == str(assignee):
                        match = True
                    elif ent.kind == assignee:
                        match = True
                    elif ent.identity.role.name.lower() == assignee.lower():
                        match = True

                    if match:
                        new_projects = dict(ent.strategic.projects)
                        new_projects[qid] = q_state
                        
                        from dataclasses import replace
                        new_strat = replace(
                            ent.strategic,
                            projects=new_projects,
                            current_project_id=qid
                        )
                        entities[ent.id] = replace(ent, strategic=new_strat)

        # Assemble final AuthoritativeState
        state = AuthoritativeState(
            tick=0,
            seed=seed,
            entities=entities,
            resource_nodes=resource_nodes,
            buildings=buildings,
            regions=regions,
            terrain=terrain,
            global_resources=global_resources,
            blocked_tiles=blocked_tiles,
            town_tiles=town_tiles,
            town_entity_ids=town_entity_ids
        )

        # Calculate fingerprint state hash
        fingerprint = StateFingerprinter.get_fingerprint(state)
        state_hash = fingerprint["state_hash"]

        # Finalize report metrics
        end_time = time.perf_counter()
        compile_duration_ms = (end_time - start_time) * 1000.0

        report = {
            "world_id": spec.world_id,
            "seed": seed,
            "entity_count": len(entities),
            "region_count": len(regions),
            "resource_node_count": len(resource_nodes),
            "building_count": len(buildings),
            "quest_count": len(compiled_quests),
            "warnings": warnings,
            "compile_duration_ms": compile_duration_ms,
            "state_hash": state_hash
        }

        if output_report_path:
            with open(output_report_path, "w") as f:
                json.dump(report, f, indent=2)

        return state, report
