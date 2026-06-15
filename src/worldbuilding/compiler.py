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


def get_role_enum(role_str: str, catalog_repo: Optional[Any] = None, context: Optional[Any] = None) -> EntityRole:
    """Map raw role string to EntityRole enum."""
    if context is not None and hasattr(context, "legacy_roles") and role_str in context.legacy_roles:
        return context.legacy_roles[role_str]

    if catalog_repo is not None:
        from src.content_semantics.role import RoleSemanticsService
        return RoleSemanticsService(catalog_repo).get_legacy_entity_role(role_str)

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


def get_faction_enum(faction_str: str, catalog_repo: Optional[Any] = None, context: Optional[Any] = None) -> Faction:
    """Map raw faction string to Faction enum."""
    if context is not None and hasattr(context, "legacy_factions") and faction_str in context.legacy_factions:
        return context.legacy_factions[faction_str]

    if catalog_repo is not None:
        from src.content_semantics.faction import FactionSemanticsService
        return FactionSemanticsService(catalog_repo).get_legacy_faction_bucket(faction_str)

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
        output_report_path: Optional[str] = None,
        context: Optional[Any] = None
    ) -> tuple[AuthoritativeState, dict]:
        """
        Compile the given WorldSpec into a fully populated AuthoritativeState.

        Args:
            spec: The validated WorldSpec object.
            seed: RNG seed for deterministic placement.
            output_report_path: Optional file path to save compile report JSON.
            context: Optional CompileContext resolving catalog profiles.

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
            owner_faction = Faction.HERO_GUILD if r_spec.type == "town" else None
            if context is not None and hasattr(context, "region_ownership") and r_spec.id in context.region_ownership:
                owner_faction = context.region_ownership[r_spec.id]

            regions[r_spec.id] = RegionState(
                id=r_spec.id,
                name=r_spec.id.replace("_", " ").title(),
                bounds=(r_spec.bounds[0], r_spec.bounds[1], r_spec.bounds[2], r_spec.bounds[3]),
                kind=r_spec.type.upper(),
                influence=100.0 if r_spec.type == "town" else 0.0,
                owner_faction_id=owner_faction,
                hazard_level=getattr(r_spec, "hazard_level", 0.0)
            )

        # 3. Compile factions (Initialize starting vaults in global_resources)
        global_resources: Dict[str, float] = {}
        for f_spec in spec.factions:
            faction_enum = get_faction_enum(f_spec.id, context=context)
            starting_gold = 1000.0
            
            # Context-backed Faction starting gold override
            if context is not None and f_spec.id in context.factions:
                starting_gold = context.factions[f_spec.id].starting_gold

            if faction_enum == Faction.HERO_GUILD:
                global_resources["faction_hero_guild_gold"] = starting_gold
            elif faction_enum == Faction.MONSTER_HORDE:
                global_resources["faction_monster_horde_gold"] = starting_gold
            elif faction_enum == Faction.TOWN_COUNCIL:
                global_resources["faction_town_council_gold"] = starting_gold
            else:
                global_resources[f"faction_{f_spec.id.lower()}_gold"] = starting_gold

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

                required_ticks = 10
                if context is not None and res_spec.id in context.resources:
                    required_ticks = context.resources[res_spec.id].required_ticks

                resource_nodes[next_resource_id] = ResourceNodeState(
                    id=next_resource_id,
                    kind=res_spec.resource_type,
                    position=(float(x), float(y)),
                    yields_item=res_spec.resource_type,
                    remaining_charges=res_spec.count,
                    max_charges=res_spec.count,
                    required_ticks=required_ticks,
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

                hp = 500
                max_hp = 500
                if context is not None and bld_spec.id in context.buildings:
                    hp = context.buildings[bld_spec.id].hp
                    max_hp = context.buildings[bld_spec.id].max_hp

                buildings[next_building_id] = BuildingState(
                    id=next_building_id,
                    kind=bld_spec.type,
                    position=(float(x), float(y)),
                    hp=hp,
                    max_hp=max_hp,
                    functional=True
                )
                blocked_tiles.add((x, y))
                next_building_id += 1

        # 6. Compile entities (populations)
        entities: Dict[int, EntityState] = {}
        town_entity_ids: Set[int] = set()
        next_entity_id = 1
        for pop_idx, pop_spec in enumerate(spec.entities):
            region_id = pop_spec.spawn_region
            region = regions.get(region_id)
            if region:
                min_x, min_y, max_x, max_y = region.bounds
                for _ in range(pop_spec.count):
                    x = rng.randint(min_x, max_x)
                    y = rng.randint(min_y, max_y)

                    # Initialize core stats with legacy default parameters
                    hp = 100
                    max_hp = 100
                    atk = 10
                    def_stat = 0
                    attack_range = 1
                    readiness = 100.0
                    
                    role_enum = get_role_enum(pop_spec.role, context=context)
                    faction_enum = get_faction_enum(pop_spec.faction, context=context)

                    # Context profile values override
                    pop_key = getattr(pop_spec, "id", f"pop_{pop_idx}")
                    if context is not None and pop_key in context.entities:
                        resolved = context.entities[pop_key]
                        hp = resolved.hp
                        max_hp = resolved.max_hp
                        atk = resolved.atk
                        def_stat = getattr(resolved, "def_stat", 0)
                        attack_range = resolved.attack_range
                        readiness = resolved.readiness
                        
                        if hasattr(resolved, "legacy_role") and resolved.legacy_role is not None:
                            role_enum = EntityRole(resolved.legacy_role)
                        if hasattr(resolved, "legacy_faction") and resolved.legacy_faction is not None:
                            faction_enum = Faction(resolved.legacy_faction)

                    # Populate properties
                    ent_properties = {
                        "spawn_region": pop_spec.spawn_region,
                        "population_id": pop_key,
                        "faction_id": pop_spec.faction,
                    }
                    if context is not None and pop_key in context.entities:
                        resolved = context.entities[pop_key]
                        if hasattr(resolved, "faction_id") and resolved.faction_id:
                            ent_properties["faction_id"] = resolved.faction_id
                        if hasattr(resolved, "race_id") and resolved.race_id:
                            ent_properties["race_id"] = resolved.race_id

                    builder = (
                        V2EntityBuilder(next_entity_id)
                        .kind(pop_spec.role.lower())
                        .location(float(x), float(y))
                        .identity(
                            role=role_enum,
                            faction=faction_enum,
                            properties=ent_properties
                        )
                        .combat(
                            hp=hp,
                            max_hp=max_hp,
                            atk=atk,
                            def_stat=def_stat,
                            attack_range=attack_range,
                            alive=True,
                            readiness=readiness
                        )
                        .lifecycle(active=True)
                    )
                    entities[next_entity_id] = builder.build()
                    if region.kind == "TOWN":
                        town_entity_ids.add(next_entity_id)
                    next_entity_id += 1


        # 7. Compile quest_definitions (authoring blueprints) into seeded QuestState records
        compiled_quests: List[QuestState] = []
        warnings: List[str] = []

        for quest_idx, q_def in enumerate(spec.quest_definitions):
            qid = q_def.id
            # Map QuestDefinition.type (authoring) → QuestKind (runtime enum)
            qkind = get_quest_kind(q_def.type)

            # Validate required_location_tags against known region IDs
            for loc_tag in q_def.required_location_tags:
                if loc_tag not in regions:
                    warnings.append(
                        f"QuestDefinition '{qid}' required_location_tag '{loc_tag}' "
                        f"does not match any region ID in this world"
                    )

            # Seed a minimal reward from reward_budget (procedural layer will refine)
            reward = RewardState(
                xp=q_def.reward_budget,
                gold=q_def.reward_budget // 2,
                items=[]
            )

            # Build metadata from procedural_hints and authoring tags
            metadata: Dict[str, Any] = dict(q_def.procedural_hints)
            if q_def.tags:
                metadata["tags"] = list(q_def.tags)
            if q_def.source_module:
                metadata["source_module"] = q_def.source_module
            if q_def.required_participant_tags:
                metadata["required_participant_tags"] = list(q_def.required_participant_tags)

            q_state = QuestState(
                id=qid,
                kind=ProjectKind.QUEST,
                quest_kind=qkind,
                quest_status=QuestStatus.ACTIVE,
                goal_value=1.0,
                current_value=0.0,
                reward=reward,
                name=qid,
                metadata=metadata
            )
            compiled_quests.append(q_state)

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
