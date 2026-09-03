# Compliance IDs: WORLD-050, WORLD-051, WORLD-052
from __future__ import annotations

import json
import time
import yaml
from pathlib import Path
from typing import Optional, Any, Dict, List, Set

from src.platform.rng import DeterministicRNG
from src.core.enums import Domain
from src.core.state import (
    AuthoritativeState,
    RegionState,
    EntityState,
    BuildingState,
    ResourceNodeState,
    InventoryComponent,
    PersonalityComponent,
    FactionState,
    PlaceState,
    PlaceKind,
)
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.replay.fingerprint import StateFingerprinter
from src.engine.checkpoint import CanonicalStateHasher
from src.worldbuilding.schema import WorldSpec
from src.core.quests import QuestState, QuestStatus, QuestKind, RewardState
from src.core.strategic import ProjectKind
from src.domains.demographics.cohort import PopulationCohort
from src.domains.information.schema import InformationSourceProfile
from src.world.providers.information import InformationResponse as _ProviderInformationResponse
from src.world.providers.information import KnowledgeFact as _ProviderKnowledgeFact


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



# get_bravery_bias/get_action_style_for_bravery moved to src/content_semantics/personality.py
# (TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY) -- shared with ArchetypeEntityFactory's own
# entity-construction path, matching content_semantics/'s established role for cross-cutting
# semantic helpers. Re-imported here so this module's own existing callers/tests are unaffected.
from src.content_semantics.personality import get_bravery_bias, get_action_style_for_bravery  # noqa: E402, F401


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
    elif "ESCORT" in k:
        return QuestKind.ESCORT
    return QuestKind.EXPLORE


_SPAWN_TABLES_PATH = Path(__file__).parent.parent.parent / "data" / "content" / "spawn_tables.yaml"

# LAW-SPAWN-OCCUPANCY collision resolution (TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE).
# sub_id 0/1 are the base x/y draw; 10-14 are personality/class. Reroll sub_ids start well above
# that range so reroll draws are a distinct RNG stream from any other per-entity field.
_ENTITY_SPAWN_COLLISION_MAX_REROLLS = 12
_ENTITY_SPAWN_COLLISION_SUB_ID_BASE = 100


def _resolve_entity_spawn_tile(
    rng: "DeterministicRNG",
    entity_id: int,
    min_x: int,
    min_y: int,
    max_x: int,
    max_y: int,
    occupied: "Set[tuple[int, int]]",
) -> "tuple[int, int]":
    """
    Deterministically resolve an entity spawn tile that collides with an already-occupied
    tile (LAW-SPAWN-OCCUPANCY). Only called when the base draw actually collides, so a
    previously non-colliding world/seed's entity placements are never perturbed.

    Root cause: each entity's spawn tile (`WorldCompiler.compile`, step 6) is drawn purely
    as a hash of (seed, entity_id, sub_id) with no occupancy awareness -- two distinct
    entity IDs can legitimately hash to the same tile within a region's bounds. This was
    confirmed by direct reproduction: `unit_selfmodel_pilot` at seed=42 places entity 6 and
    entity 14 both at (27, 38) inside the `hometown` region (bounds (10, 10, 40, 40)).

    Strategy: deterministically re-roll using bumped sub_id values (still a pure function
    of seed/entity_id/sub_id -- fully reproducible and order-independent), then fall back to
    a deterministic raster scan of the region's bounding box for the rare case a region is
    densely packed enough that rerolling doesn't find a free tile within the attempt budget.
    """
    for attempt in range(_ENTITY_SPAWN_COLLISION_MAX_REROLLS):
        sub_id = _ENTITY_SPAWN_COLLISION_SUB_ID_BASE + attempt * 2
        x = rng.get_int(Domain.WORLD, 0, entity_id, min_x, max_x, sub_id=sub_id)
        y = rng.get_int(Domain.WORLD, 0, entity_id, min_y, max_y, sub_id=sub_id + 1)
        if (x, y) not in occupied:
            return x, y

    # Deterministic raster fallback: scan in stable row-major order so the outcome stays
    # reproducible even when rerolling can't find a free tile within the attempt budget.
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if (x, y) not in occupied:
                return x, y

    # Region fully packed (more spawns than tiles) -- no free tile exists. Keep the last
    # deterministic reroll draw; the caller records a compile warning for this case.
    sub_id = _ENTITY_SPAWN_COLLISION_SUB_ID_BASE + (_ENTITY_SPAWN_COLLISION_MAX_REROLLS - 1) * 2
    x = rng.get_int(Domain.WORLD, 0, entity_id, min_x, max_x, sub_id=sub_id)
    y = rng.get_int(Domain.WORLD, 0, entity_id, min_y, max_y, sub_id=sub_id + 1)
    return x, y


def _load_class_table() -> Dict[str, List[str]]:
    """Return role→[class_ids] from spawn_tables.yaml. Falls back to empty dict on error."""
    try:
        with open(_SPAWN_TABLES_PATH) as f:
            entries = yaml.safe_load(f) or []
        for entry in entries:
            if entry.get("schema_version") == "classtable.v1":
                return {k.lower(): v for k, v in entry.get("class_id_by_role", {}).items()}
    except (OSError, yaml.YAMLError):
        pass
    return {}


# Fixed young/adult/elder distribution ratio for compile-time population_cohorts seeding.
# Authored 2026-09-01 (TCK-20260831-POPULATION-COHORT-SEEDING) -- no prior anchor existed
# in code or docs. Chosen as a plausible stable/mildly-growing population pyramid shape:
# a plurality of working-age adults, a meaningful youth cohort, and a smaller elder
# cohort -- directionally consistent with PopulationCohort's own default birth_rate
# (0.02) > mortality_rate (0.01), which already implies net growth (cohort.py:41-42).
# Ratio is intentionally simple/round, not derived from any external demographic
# dataset -- this is a fresh design choice, not a parity claim against real-world data.
_YOUNG_ADULT_ELDER_RATIO: Dict[str, float] = {"young": 0.30, "adult": 0.50, "elder": 0.20}
# Fixed priority order used only to break exact remainder ties deterministically.
_BRACKET_PRIORITY: List[str] = ["young", "adult", "elder"]


def _seed_population_cohorts(declared_population: int) -> Dict[str, "PopulationCohort"]:
    """
    Split declared_population into young/adult/elder PopulationCohort counts using the
    fixed _YOUNG_ADULT_ELDER_RATIO, via largest-remainder (Hamilton apportionment)
    rounding so the three counts always sum exactly to declared_population, including
    at small totals (0, 1, 2) where naive per-bracket floor/truncation can lose 1-2
    units.

    Pure arithmetic, no RNG -- consistent with the only two existing precedents for
    deriving a RegionState field from other spec values (`influence`, `owner_faction_id`),
    neither of which uses RNG.

    Returns {} (not three zero-count cohorts) when declared_population == 0, so the
    DemographicCycleService guard at cohort.py:349 (`if not region.population_cohorts:
    continue`) no-ops via plain dict-truthiness. Seeded cohorts leave
    birth_rate/mortality_rate at their PopulationCohort dataclass defaults (0.02/0.01,
    cohort.py:41-42) untouched -- this ticket seeds counts only, it does not rebalance
    or reinterpret the existing per-200-tick-cycle rates.
    """
    if declared_population <= 0:
        return {}

    raw = {b: declared_population * r for b, r in _YOUNG_ADULT_ELDER_RATIO.items()}
    floors = {b: int(v) for b, v in raw.items()}
    remainder = declared_population - sum(floors.values())

    remainders = sorted(
        _BRACKET_PRIORITY,
        key=lambda b: (-(raw[b] - floors[b]), _BRACKET_PRIORITY.index(b)),
    )
    counts = dict(floors)
    for b in remainders[:remainder]:
        counts[b] += 1

    return {
        bracket: PopulationCohort(bracket=bracket, count=counts[bracket])
        for bracket in _BRACKET_PRIORITY
    }


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

        # 0. Initialize deterministic RNG and load class table
        rng = DeterministicRNG(seed)
        class_table = _load_class_table()

        # 1. Compile map topology
        terrain: Dict[tuple[int, int], str] = {}
        for x in range(spec.topology.width):
            for y in range(spec.topology.height):
                terrain[(x, y)] = "PLAIN"

        # 1a. Aggregate declared population per region from spec.entities (PopulationSpec.count),
        # summed by spawn_region. Must run before step 2 constructs RegionState, since RegionState
        # is @dataclass(frozen=True, slots=True) (src/core/state.py) and cannot be field-mutated
        # after construction. Multiple PopulationSpec entries may share one spawn_region
        # (WorldSpec.validate_unique_identifiers only enforces uniqueness of PopulationSpec.id,
        # not spawn_region), so this must sum, not overwrite.
        region_declared_population: Dict[str, int] = {}
        for pop_spec in spec.entities:
            region_declared_population[pop_spec.spawn_region] = (
                region_declared_population.get(pop_spec.spawn_region, 0) + pop_spec.count
            )

        # 2. Compile regions & terrain painting
        regions: Dict[str, RegionState] = {}
        places: Dict[str, PlaceState] = {}  # Idea 66
        town_tiles: Set[tuple[int, int]] = set()

        for r_spec in spec.regions:
            min_x, min_y, max_x, max_y = r_spec.bounds
            
            # Default to "GRASS" if terrain not specified on RegionSpec
            r_terrain = getattr(r_spec, "terrain", "GRASS")
            region_hash = 0
            if r_spec.terrain_variants:
                for ch in r_spec.id:
                    region_hash = (region_hash * 31 + ord(ch)) & 0xFFFFFFFF
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    if 0 <= x < spec.topology.width and 0 <= y < spec.topology.height:
                        if r_spec.terrain_variants:
                            tile_offset = ((x & 0xFFFF) << 16) | (y & 0xFFFF)
                            entity_id = (region_hash ^ tile_offset) & 0xFFFFFFFF
                            tile_terrain = rng.weighted_choice(
                                Domain.INIT, tick=0, entity_id=entity_id,
                                seq=[v.terrain for v in r_spec.terrain_variants],
                                weights=[v.weight for v in r_spec.terrain_variants],
                                sub_id=1,
                            )
                        else:
                            tile_terrain = r_terrain
                        terrain[(x, y)] = tile_terrain
                        if r_spec.type == "town":
                            town_tiles.add((x, y))

            # Map RegionSpec to RegionState
            owner_faction = Faction.HERO_GUILD if r_spec.type == "town" else None
            if context is not None and hasattr(context, "region_ownership") and r_spec.id in context.region_ownership:
                owner_faction = context.region_ownership[r_spec.id]

            # Idea 66 (TCK-20260902-WORLDCOMPILER-PLACE-WIRING): construct real PlaceState
            # instances from any Place-shaped content declared on this region (r_spec.places,
            # RegionSpec's new field). Empty for all existing content today -- new, opt-in
            # only; existing worlds compile with places=[] exactly as before this ticket.
            for p_spec in getattr(r_spec, "places", []):
                places[p_spec.id] = PlaceState(
                    place_id=p_spec.id,
                    region_id=r_spec.id,
                    kind=PlaceKind(p_spec.kind),
                    position=(float(p_spec.position[0]), float(p_spec.position[1])),
                    footprint=p_spec.footprint,
                    owner_faction_id=(int(p_spec.owner_faction_id) if p_spec.owner_faction_id is not None else None),
                    scale=p_spec.scale,
                    maturity=p_spec.maturity,
                    hazard_level=p_spec.hazard_level,
                )

            regions[r_spec.id] = RegionState(
                id=r_spec.id,
                name=r_spec.id.replace("_", " ").title(),
                bounds=(r_spec.bounds[0], r_spec.bounds[1], r_spec.bounds[2], r_spec.bounds[3]),
                kind=r_spec.type.upper(),
                influence=100.0 if r_spec.type == "town" else 0.0,
                owner_faction_id=owner_faction,
                hazard_level=getattr(r_spec, "hazard_level", 0.0),
                hazard_kind=getattr(r_spec, "hazard_kind", "PHYSICAL"),
                population_cohorts=_seed_population_cohorts(region_declared_population.get(r_spec.id, 0)),
                places=[p_spec.id for p_spec in getattr(r_spec, "places", [])],
            )

        # 2a. Derive town_center as the centroid of the first type=="town" region in
        # spec.regions declaration order (SUB-387; docs/mechanics/06_worldbuilding_foundation.md).
        # Left unset (dataclass default (0.0, 0.0)) if no town-type region exists.
        town_center: Optional[tuple[float, float]] = None
        for r_spec in spec.regions:
            if r_spec.type == "town":
                min_x, min_y, max_x, max_y = r_spec.bounds
                town_center = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
                break

        # 3. Compile factions (Initialize starting vaults in global_resources)
        global_resources: Dict[str, float] = {}
        factions: Dict[str, FactionState] = {}
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

            factions[f_spec.id] = FactionState(
                faction_id=f_spec.id,
                tension_level=f_spec.initial_tension_level,
            )

        # Collected across steps 4-7; step 6 also appends LAW-SPAWN-OCCUPANCY
        # region-exhaustion warnings (see _resolve_entity_spawn_tile).
        warnings: List[str] = []

        # 4. Compile resources
        resource_nodes: Dict[int, ResourceNodeState] = {}
        next_resource_id = 10000
        for res_spec in spec.resources:
            region_id = res_spec.region
            region = regions.get(region_id)
            if region:
                min_x, min_y, max_x, max_y = region.bounds
                x = rng.get_int(Domain.WORLD, 0, next_resource_id, min_x, max_x, sub_id=0)
                y = rng.get_int(Domain.WORLD, 0, next_resource_id, min_y, max_y, sub_id=1)

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
                    cooldown_remaining=0,
                    regen_rate_per_tick=res_spec.regen_rate,
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
                x = rng.get_int(Domain.WORLD, 0, next_building_id, min_x, max_x, sub_id=0)
                y = rng.get_int(Domain.WORLD, 0, next_building_id, min_y, max_y, sub_id=1)

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
        # LAW-SPAWN-OCCUPANCY: track tiles already claimed by buildings, resource nodes, and
        # previously-placed entities so a colliding draw can be deterministically resolved
        # (TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE). Seeded once, before
        # any entity is placed, so entity placement order (ascending entity_id, i.e. population
        # authoring order) alone determines which entity of a colliding pair gets nudged --
        # never the earlier one, which keeps every non-colliding world's placements unchanged.
        occupied_entity_tiles: Set[tuple[int, int]] = set(blocked_tiles) | {
            (int(node.position[0]), int(node.position[1])) for node in resource_nodes.values()
        }
        for pop_idx, pop_spec in enumerate(spec.entities):
            region_id = pop_spec.spawn_region
            region = regions.get(region_id)
            if region:
                min_x, min_y, max_x, max_y = region.bounds
                for _ in range(pop_spec.count):
                    x = rng.get_int(Domain.WORLD, 0, next_entity_id, min_x, max_x, sub_id=0)
                    y = rng.get_int(Domain.WORLD, 0, next_entity_id, min_y, max_y, sub_id=1)

                    if (x, y) in occupied_entity_tiles:
                        x, y = _resolve_entity_spawn_tile(
                            rng, next_entity_id, min_x, min_y, max_x, max_y, occupied_entity_tiles
                        )
                        if (x, y) in occupied_entity_tiles:
                            warnings.append(
                                f"entity {next_entity_id} (population "
                                f"'{getattr(pop_spec, 'id', f'pop_{pop_idx}')}') could not be "
                                f"placed on a free tile in region '{region_id}' "
                                f"(bounds {region.bounds}) -- region is fully packed; "
                                f"LAW-SPAWN-OCCUPANCY will still flag tile ({x}, {y})"
                            )
                    occupied_entity_tiles.add((x, y))

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

                    # Seed personality deterministically from entity ID + world seed.
                    # Bravery is biased by the entity's real faction alignment_bucket (see
                    # get_bravery_bias) so race/faction produces a real, measurable population
                    # skew (e.g. wild_beast_pack trending brave) while individual per-entity RNG
                    # variance is preserved within that skew.
                    bravery_bias = get_bravery_bias(pop_spec.faction)
                    personality = PersonalityComponent(
                        greed=rng.get_float(Domain.WORLD, 0, next_entity_id, sub_id=10),
                        bravery=min(1.0, max(0.0, rng.get_float(Domain.WORLD, 0, next_entity_id, sub_id=11) + bravery_bias)),
                        sociability=rng.get_float(Domain.WORLD, 0, next_entity_id, sub_id=12),
                        industry=rng.get_float(Domain.WORLD, 0, next_entity_id, sub_id=13),
                    )

                    # Assign class_id by role from spawn table; fall back to NOVICE
                    role_key = pop_spec.role.lower()
                    class_pool = class_table.get(role_key) or ["NOVICE"]
                    ent_class_id = rng.choice(Domain.WORLD, 0, next_entity_id, class_pool, sub_id=14)

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
                        .navigation(region_id=region_id)
                        .identity(
                            role=role_enum,
                            faction=faction_enum,
                            class_id=ent_class_id,
                            personality=personality,
                            properties=ent_properties
                        )
                        .combat(
                            hp=hp,
                            max_hp=max_hp,
                            atk=atk,
                            def_stat=def_stat,
                            attack_range=attack_range,
                            alive=True,
                            readiness=readiness,
                            action_style=get_action_style_for_bravery(personality.bravery)
                        )
                        .lifecycle(active=True)
                    )
                    entities[next_entity_id] = builder.build()
                    if region.kind == "TOWN":
                        town_entity_ids.add(next_entity_id)
                    next_entity_id += 1


        # 7. Compile quest_definitions (authoring blueprints) into seeded QuestState records
        compiled_quests: List[QuestState] = []

        # Build a pool of all semantic location labels reachable in this world.
        # Use spec.regions (RegionSpec list) — regions dict holds RegionState (runtime
        # objects with a 'kind' field) which has already lost the original type string
        # and the explicit tags list. RegionSpec.type + RegionSpec.tags are the
        # authoritative location vocabulary at compile time.
        tag_pool: set = set()
        for r_spec in spec.regions:
            if r_spec.type:
                tag_pool.add(r_spec.type)
            for t in getattr(r_spec, "tags", []):
                tag_pool.add(t)

        for quest_idx, q_def in enumerate(spec.quest_definitions):
            qid = q_def.id
            # Map QuestDefinition.type (authoring) → QuestKind (runtime enum)
            qkind = get_quest_kind(q_def.type)

            # Validate required_location_tags against region types and explicit tags
            for loc_tag in q_def.required_location_tags:
                if loc_tag not in tag_pool:
                    warnings.append(
                        f"QuestDefinition '{qid}' required_location_tag '{loc_tag}' "
                        f"does not match any region type or tag in this world"
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

        information_source_profiles: List[InformationSourceProfile] = [
            InformationSourceProfile(
                source_id=p.source_id,
                source_kind=p.source_kind,
                knowledge_scopes=tuple(p.knowledge_scopes),
                accuracy=p.accuracy,
                freshness=p.freshness,
                bias=p.bias,
                cost_gold=p.cost_gold,
                max_answers_per_query=p.max_answers_per_query,
            )
            for p in spec.information_source_profiles
        ]

        # 6b. Resolve pending_information_responses: target_population_id -> compiled actor_id
        pending_information_responses: List[Dict[str, Any]] = []
        for r in spec.pending_information_responses:
            actor_id = next(
                (eid for eid, e in entities.items()
                 if e.properties.get("population_id") == r.target_population_id),
                None,
            )
            if actor_id is None:
                warnings.append(
                    f"pending_information_responses target_population_id "
                    f"'{r.target_population_id}' matched no compiled entity; entry skipped"
                )
                continue
            pending_information_responses.append({
                "actor_id": actor_id,
                "subject": r.subject,
                "query_kind": r.query_kind,
                "source_id": r.source_id,
                "raw_response": {
                    "answer_kind": r.answer_kind,
                    "certainty": r.certainty,
                    "details": dict(r.details),
                    "reason": r.reason,
                },
                "cost_paid": r.cost_paid,
            })

        # 6c. Resolve pending_self_model_information_events: target_population_id -> compiled actor_id,
        # construct real InformationResponse objects (Step 1's consumer needs attribute access, not
        # dict-item access — a different construction shape from 6b above).
        pending_self_model_information_events: List[Dict[str, Any]] = []
        for r in spec.pending_self_model_information_events:
            actor_id = next(
                (eid for eid, e in entities.items()
                 if e.properties.get("population_id") == r.target_population_id),
                None,
            )
            if actor_id is None:
                warnings.append(
                    f"pending_self_model_information_events target_population_id "
                    f"'{r.target_population_id}' matched no compiled entity; entry skipped"
                )
                continue
            event = _ProviderInformationResponse(
                answer_kind=r.answer_kind,
                facts=tuple(
                    _ProviderKnowledgeFact(subject=f.subject, fact_type=f.fact_type, details=dict(f.details))
                    for f in r.facts
                ),
                unknowns=tuple(r.unknowns),
                suggested_leads=(),
                certainty=r.certainty,
                source_id=r.source_id,
                cost_gold=r.cost_gold,
            )
            pending_self_model_information_events.append({"actor_id": actor_id, "event": event})

        # Assemble final AuthoritativeState
        state = AuthoritativeState(
            tick=0,
            seed=seed,
            entities=entities,
            resource_nodes=resource_nodes,
            buildings=buildings,
            regions=regions,
            places=places,  # Idea 66
            terrain=terrain,
            global_resources=global_resources,
            blocked_tiles=blocked_tiles,
            town_tiles=town_tiles,
            town_center=town_center if town_center is not None else (0.0, 0.0),
            town_entity_ids=town_entity_ids,
            factions=factions,
            information_source_profiles=information_source_profiles,
            pending_information_responses=pending_information_responses,
            pending_self_model_information_events=pending_self_model_information_events
        )

        # Calculate fingerprint state hash
        fingerprint = StateFingerprinter.get_fingerprint(state)
        state_hash = fingerprint["state_hash"]

        # Idea 66 (TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT): StateFingerprinter is
        # intentionally lightweight and does not cover Place data (or most of
        # NavigationComponent, see TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP) -- a
        # world's "state_hash" staying unchanged does not mean its Place-shaped content
        # migration was a no-op. canonical_state_hash is the real, full-coverage check
        # (CanonicalStateHasher, the same hash src/engine/kernel.py uses for its
        # per-tick/final-run determinism checks) -- the one that actually detects a
        # Place addition.
        canonical_state_hash = CanonicalStateHasher.get_hash(state)

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
            "distinct_populated_factions": len({
                fid for e in entities.values()
                if (fid := e.properties.get("faction_id"))
            }),
            "warnings": warnings,
            "compile_duration_ms": compile_duration_ms,
            "state_hash": state_hash,
            "canonical_state_hash": canonical_state_hash,
            "place_count": len(places),
        }

        if output_report_path:
            with open(output_report_path, "w") as f:
                json.dump(report, f, indent=2)

        return state, report
