"""EngineManager — singleton wrapper that runs the WorldLoop on a background thread.

The API reads from an atomically-swapped immutable Snapshot; the WorldLoop
mutates WorldState exclusively on its own thread (Single-Writer preserved).
"""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

from src.ai.brain import AIBrain
from src.core.buildings import Building
from src.core.enums import AIState, Domain, EnemyTier, EntityRole, Material
from src.core.faction import Faction, FactionRegistry
from src.core.grid import Grid
from src.core.items import Inventory, TERRAIN_RACE, RACE_FACTION
from src.core.models import Entity, Stats, Vector2
from src.core.regions import (
    Region, Location, LOCATION_NAME_TEMPLATES, TERRAIN_RACE_LABEL,
    difficulty_for_distance, pick_region_name, reset_name_counters,
)
from src.core.resource_nodes import ResourceNode, TERRAIN_RESOURCES
from src.core.snapshot import Snapshot
from src.core.world_state import WorldState
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.engine.world_loop import WorldLoop
from src.systems.generator import EntityGenerator
from src.systems.rng import DeterministicRNG
from src.systems.spatial_hash import SpatialHash
from src.utils.event_log import EventLog, SimEvent

if TYPE_CHECKING:
    from src.config import SimulationConfig

logger = logging.getLogger(__name__)


class EngineManager:
    """Manages the simulation lifecycle on a background thread.

    Provides thread-safe access to:
      - latest snapshot (atomic reference swap)
      - event log (lock-guarded ring buffer)
      - control commands (start / pause / resume / step / reset)
    """

    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self.config = config
        self._tick_rate: float = 0.05  # seconds between ticks (20 tps default)

        # Simulation components (built in _build)
        self._rng: DeterministicRNG | None = None
        self._loop: WorldLoop | None = None
        self._worker_pool: WorkerPool | None = None

        # Thread-safe shared state
        self._snapshot_lock = threading.Lock()
        self._latest_snapshot: Snapshot | None = None
        self._event_log = EventLog()

        # Counters
        self._total_spawned: int = 0
        self._total_deaths: int = 0

        # Control
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._paused = threading.Event()
        self._step_requested = threading.Event()
        self._stop_requested = threading.Event()

        self._build()

    # -- public properties --

    @property
    def running(self) -> bool:
        return self._running.is_set()

    @property
    def paused(self) -> bool:
        return self._paused.is_set()

    @property
    def tick_rate(self) -> float:
        return self._tick_rate

    @tick_rate.setter
    def tick_rate(self, value: float) -> None:
        self._tick_rate = max(0.01, min(value, 2.0))

    @property
    def event_log(self) -> EventLog:
        return self._event_log

    @property
    def total_spawned(self) -> int:
        return self._total_spawned

    @property
    def total_deaths(self) -> int:
        return self._total_deaths

    # -- snapshot access --

    def get_snapshot(self) -> Snapshot | None:
        with self._snapshot_lock:
            return self._latest_snapshot

    def get_grid(self) -> Grid | None:
        """Return the grid from the latest snapshot (static data)."""
        snap = self.get_snapshot()
        return snap.grid if snap else None

    # -- lifecycle --

    def start(self) -> None:
        if self._running.is_set():
            return
        self._stop_requested.clear()
        self._paused.clear()
        self._running.set()
        self._thread = threading.Thread(target=self._run_loop, name="engine-loop", daemon=True)
        self._thread.start()
        logger.info("EngineManager started (tick_rate=%.3fs)", self._tick_rate)

    def pause(self) -> None:
        self._paused.set()
        logger.info("EngineManager paused at tick %d", self._current_tick())

    def resume(self) -> None:
        self._paused.clear()
        logger.info("EngineManager resumed at tick %d", self._current_tick())

    def step(self) -> None:
        """Execute exactly one tick (must be paused)."""
        if not self._paused.is_set():
            self.pause()
        self._step_requested.set()

    def stop(self) -> None:
        self._stop_requested.set()
        self._paused.clear()
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        if self._worker_pool:
            self._worker_pool.shutdown()
        logger.info("EngineManager stopped.")

    def reset(self) -> None:
        """Stop, rebuild, and leave in paused state ready to start."""
        self.stop()
        self._event_log.clear()
        self._total_spawned = 0
        self._total_deaths = 0
        self._build()
        # Take initial snapshot
        if self._loop:
            snap = self._loop.create_snapshot()
            with self._snapshot_lock:
                self._latest_snapshot = snap
        logger.info("EngineManager reset.")

    # -- internals --

    def _build(self) -> None:
        """Construct all simulation components from config."""
        cfg = self._config
        self._rng = DeterministicRNG(cfg.world_seed)
        grid = Grid(cfg.grid_width, cfg.grid_height)
        spatial = SpatialHash(cfg.spatial_cell_size)
        world = WorldState(seed=cfg.world_seed, grid=grid, spatial_index=spatial)

        town_center = Vector2(cfg.town_center_x, cfg.town_center_y)

        # --- Place town tiles (safe zone) ---
        for ty in range(cfg.town_center_y - cfg.town_radius, cfg.town_center_y + cfg.town_radius + 1):
            for tx in range(cfg.town_center_x - cfg.town_radius, cfg.town_center_x + cfg.town_radius + 1):
                pos = Vector2(tx, ty)
                if grid.in_bounds(pos):
                    grid.set(pos, Material.TOWN)

        # --- Place sanctuary tiles (debuff zone around town) ---
        for sy in range(cfg.town_center_y - cfg.sanctuary_radius, cfg.town_center_y + cfg.sanctuary_radius + 1):
            for sx in range(cfg.town_center_x - cfg.sanctuary_radius, cfg.town_center_x + cfg.sanctuary_radius + 1):
                pos = Vector2(sx, sy)
                if grid.in_bounds(pos) and grid.get(pos) == Material.FLOOR:
                    grid.set(pos, Material.SANCTUARY)

        # --- Create named regions with sub-locations (epic-15) ---
        # Voronoi tessellation: place region centers, then assign every
        # non-town tile to its nearest center so regions border each other
        # like countries on a continent — no empty gaps.
        reset_name_counters()
        generator = EntityGenerator(cfg, self._rng)
        from src.core.items import TreasureChest

        TOWN_TILES = frozenset({Material.TOWN, Material.SANCTUARY})

        region_specs = [
            (Material.FOREST, cfg.num_forest_regions),
            (Material.DESERT, cfg.num_desert_regions),
            (Material.SWAMP, cfg.num_swamp_regions),
            (Material.MOUNTAIN, cfg.num_mountain_regions),
        ]
        camp_positions: list[Vector2] = []
        zone_bounds = list(cfg.difficulty_zones)

        # ---- Step 1: Place region centers (seeds) ----
        region_seeds: list[tuple[Vector2, Material]] = []  # (center, terrain)
        for mat, count in region_specs:
            for ri in range(count):
                seed_key = mat * 100 + ri
                for attempt in range(120):
                    rx = self._rng.next_int(Domain.MAP_GEN, seed_key, attempt, 6, cfg.grid_width - 7)
                    ry = self._rng.next_int(Domain.MAP_GEN, seed_key, attempt + 200, 6, cfg.grid_height - 7)
                    rpos = Vector2(rx, ry)
                    if rpos.manhattan(town_center) < cfg.camp_min_distance_from_town:
                        continue
                    too_close = any(rpos.manhattan(s[0]) < cfg.region_min_distance for s in region_seeds)
                    if too_close:
                        continue
                    region_seeds.append((rpos, mat))
                    break
                else:
                    logger.warning("Failed to place %s region #%d center", mat.name, ri)

        # ---- Step 2: Voronoi assignment — paint every non-town tile ----
        # For each tile, find nearest region center and paint with that region's terrain.
        # Also track max distance per region for effective radius.
        region_max_dist: dict[int, int] = {i: 0 for i in range(len(region_seeds))}
        for y in range(cfg.grid_height):
            for x in range(cfg.grid_width):
                pos = Vector2(x, y)
                if grid.get(pos) in TOWN_TILES:
                    continue
                # Find nearest region center
                best_idx = -1
                best_dist = float("inf")
                for idx, (center, _mat) in enumerate(region_seeds):
                    d = center.manhattan(pos)
                    if d < best_dist:
                        best_dist = d
                        best_idx = idx
                if best_idx >= 0:
                    _center, r_mat = region_seeds[best_idx]
                    grid.set(pos, r_mat)
                    d_int = int(best_dist)
                    if d_int > region_max_dist[best_idx]:
                        region_max_dist[best_idx] = d_int

        # ---- Step 3: Create Region objects with computed radius ----
        region_centers: list[Vector2] = []
        for idx, (rpos, mat) in enumerate(region_seeds):
            dist_to_town = rpos.manhattan(town_center)
            difficulty = difficulty_for_distance(dist_to_town, zone_bounds)
            region_name = pick_region_name(mat)
            region_id = region_name.lower().replace(" ", "_").replace("'", "")
            effective_radius = region_max_dist.get(idx, cfg.region_max_radius)
            region = Region(
                region_id=region_id, name=region_name,
                terrain=mat, center=rpos, radius=effective_radius,
                difficulty=difficulty,
            )

            # ---- Step 4: Generate sub-locations within this region ----
            seed_key = mat * 100 + (idx % 10)
            num_locs = self._rng.next_int(Domain.MAP_GEN, seed_key, 500 + idx,
                                          cfg.min_locations_per_region, cfg.max_locations_per_region)
            loc_positions: list[Vector2] = []
            race_label = TERRAIN_RACE_LABEL.get(int(mat), "Goblin")

            # Location type budget per region
            loc_types: list[str] = ["enemy_camp", "resource_grove"]
            if difficulty >= 3:
                loc_types.append("dungeon_entrance")
                loc_types.append("boss_arena")
            else:
                loc_types.append("shrine")
            loc_types.append("ruins")
            while len(loc_types) < num_locs:
                extra = ["enemy_camp", "resource_grove", "ruins"]
                pick = self._rng.next_int(Domain.MAP_GEN, seed_key + len(loc_types), 600 + idx,
                                          0, len(extra) - 1)
                loc_types.append(extra[pick])

            # Use half the effective radius as placement range (locations stay in core)
            loc_range = max(effective_radius // 2, 8)
            for li, loc_type in enumerate(loc_types[:num_locs]):
                loc_placed = False
                for loc_attempt in range(60):
                    ox = self._rng.next_int(Domain.MAP_GEN, seed_key + li * 100, loc_attempt + 700,
                                            -loc_range, loc_range)
                    oy = self._rng.next_int(Domain.MAP_GEN, seed_key + li * 100, loc_attempt + 800,
                                            -loc_range, loc_range)
                    lpos = Vector2(rpos.x + ox, rpos.y + oy)
                    if not grid.in_bounds(lpos):
                        continue
                    # Must be on this region's terrain (Voronoi guarantees nearby tiles are ours)
                    tile_at = grid.get(lpos)
                    if tile_at != mat:
                        continue
                    too_close_loc = any(lpos.manhattan(lp) < cfg.location_min_spacing for lp in loc_positions)
                    if too_close_loc:
                        continue

                    # Pick a name
                    templates = LOCATION_NAME_TEMPLATES.get(loc_type, ["{race} Place"])
                    tpl_idx = self._rng.next_int(Domain.MAP_GEN, seed_key + li, loc_attempt + 900,
                                                 0, len(templates) - 1)
                    loc_name = templates[tpl_idx].format(race=race_label)
                    loc_id = f"{region_id}_{loc_type}_{li}"

                    loc = Location(
                        location_id=loc_id, name=loc_name,
                        location_type=loc_type, pos=lpos, region_id=region_id,
                    )
                    region.locations.append(loc)
                    loc_positions.append(lpos)

                    # Paint location-specific tiles
                    if loc_type == "enemy_camp":
                        for cdy in range(-cfg.camp_radius, cfg.camp_radius + 1):
                            for cdx in range(-cfg.camp_radius, cfg.camp_radius + 1):
                                cp = Vector2(lpos.x + cdx, lpos.y + cdy)
                                if grid.in_bounds(cp) and grid.get(cp) == mat:
                                    grid.set(cp, Material.CAMP)
                        camp_positions.append(lpos)
                        world.camps.append(lpos)
                    elif loc_type == "ruins":
                        for rdy in range(-1, 2):
                            for rdx in range(-1, 2):
                                rtp = Vector2(lpos.x + rdx, lpos.y + rdy)
                                if grid.in_bounds(rtp) and grid.get(rtp) == mat:
                                    grid.set(rtp, Material.RUINS)
                    elif loc_type == "dungeon_entrance":
                        grid.set(lpos, Material.DUNGEON_ENTRANCE)
                    elif loc_type == "resource_grove":
                        pass  # Nodes placed later; terrain stays as region material
                    elif loc_type == "shrine":
                        pass  # Shrine is a gameplay marker, no special tile yet
                    elif loc_type == "boss_arena":
                        pass  # Boss arena uses region terrain

                    # Spawn treasure chest at ruins/dungeon locations
                    if loc_type in ("ruins", "dungeon_entrance"):
                        cid = world._next_chest_id
                        world._next_chest_id += 1
                        chest = TreasureChest(chest_id=cid, pos=lpos, tier=min(difficulty, 4))
                        world.treasure_chests[cid] = chest

                    loc_placed = True
                    break

            world.regions.append(region)
            region_centers.append(rpos)
            logger.info("Created region '%s' (%s, tier %d) at %s r=%d with %d locations",
                        region.name, mat.name, difficulty, rpos, effective_radius, len(region.locations))

        # --- Generate roads from town to nearest regions ---
        if cfg.road_from_town:
            road_targets: list[Vector2] = []
            sorted_regions = sorted(region_centers, key=lambda r: r.manhattan(town_center))
            road_targets.extend(sorted_regions[:4])
            for rt in road_targets:
                cx, cy = town_center.x, town_center.y
                tx, ty = rt.x, rt.y
                step_x = 1 if tx > cx else -1
                x = cx
                while x != tx:
                    x += step_x
                    rp = Vector2(x, cy)
                    if grid.in_bounds(rp) and grid.get(rp) == Material.FLOOR:
                        grid.set(rp, Material.ROAD)
                step_y = 1 if ty > cy else -1
                y = cy
                while y != ty:
                    y += step_y
                    rp = Vector2(tx, y)
                    if grid.in_bounds(rp) and grid.get(rp) == Material.FLOOR:
                        grid.set(rp, Material.ROAD)
            logger.info("Generated roads to %d regions", len(road_targets))

        # --- Place town buildings ---
        # Store: top-left of town
        store_pos = Vector2(cfg.town_center_x - cfg.town_radius + 1, cfg.town_center_y - cfg.town_radius + 1)
        world.buildings.append(Building(
            building_id="store", name="General Store", pos=store_pos, building_type="store"))
        # Blacksmith: top-right of town
        bs_pos = Vector2(cfg.town_center_x + cfg.town_radius - 1, cfg.town_center_y - cfg.town_radius + 1)
        world.buildings.append(Building(
            building_id="blacksmith", name="Blacksmith", pos=bs_pos, building_type="blacksmith"))
        # Guild: bottom-center of town
        guild_pos = Vector2(cfg.town_center_x, cfg.town_center_y + cfg.town_radius - 1)
        world.buildings.append(Building(
            building_id="guild", name="Adventurer's Guild", pos=guild_pos, building_type="guild"))
        # Class Hall: bottom-left of town
        class_hall_pos = Vector2(cfg.town_center_x - cfg.town_radius + 1, cfg.town_center_y + cfg.town_radius - 1)
        world.buildings.append(Building(
            building_id="class_hall", name="Class Hall", pos=class_hall_pos, building_type="class_hall"))
        # Inn: bottom-right of town
        inn_pos = Vector2(cfg.town_center_x + cfg.town_radius - 1, cfg.town_center_y + cfg.town_radius - 1)
        world.buildings.append(Building(
            building_id="inn", name="Traveler's Inn", pos=inn_pos, building_type="inn"))
        logger.info(
            "Placed town buildings: Store@%s, Blacksmith@%s, Guild@%s, ClassHall@%s, Inn@%s",
            store_pos, bs_pos, guild_pos, class_hall_pos, inn_pos,
        )

        # --- Spawn hero via EntityBuilder ---
        from src.core.classes import HeroClass, CLASS_DEFS
        from src.core.entity_builder import EntityBuilder

        hero_eid = world.allocate_entity_id()
        class_choices = [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]
        class_roll = self._rng.next_int(Domain.SPAWN, hero_eid, 6, 0, len(class_choices) - 1)
        hero_class = class_choices[class_roll]

        hero = (
            EntityBuilder(self._rng, hero_eid, tick=0)
            .kind("hero")
            .at(Vector2(cfg.town_center_x, cfg.town_center_y))
            .home(town_center)
            .faction(Faction.HERO_GUILD)
            .role(EntityRole.HERO)
            .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3,
                             crit_rate=0.08, crit_dmg=1.8, evasion=0.03, gold=50)
            .with_randomized_stats()
            .with_hero_class(hero_class)
            .with_race_skills("hero")
            .with_class_skills(hero_class, level=1)
            .with_inventory(max_slots=cfg.hero_inventory_slots,
                            max_weight=cfg.hero_inventory_weight,
                            weapon="iron_sword", armor="leather_vest")
            .with_starting_items(["small_hp_potion"] * 3)
            .with_home_storage()
            .with_traits(race_prefix="hero")
            .build()
        )
        world.add_entity(hero)
        self._total_spawned += 1
        class_def = CLASS_DEFS.get(hero_class)
        logger.info("Spawned hero #%d as %s", hero_eid, class_def.name if class_def else "unknown")

        # --- Register hero house as a building ---
        hero_house_pos = Vector2(cfg.town_center_x + 1, cfg.town_center_y)
        world.buildings.append(Building(
            building_id=f"hero_house_{hero_eid}",
            name=f"Hero's House",
            pos=hero_house_pos,
            building_type="hero_house",
        ))
        logger.info("Placed hero house at %s for hero #%d", hero_house_pos, hero_eid)

        # --- Spawn initial goblins (wanderers, not tied to a region) ---
        for i in range(1, cfg.initial_entity_count):
            entity = generator.spawn(world)
            world.add_entity(entity)
            self._total_spawned += 1

        # --- Spawn entities + resources at region locations (epic-15) ---
        for region in world.regions:
            mat = region.terrain
            race = TERRAIN_RACE.get(int(mat))

            for loc in region.locations:
                if loc.location_type == "enemy_camp":
                    # Chief + guards at camp
                    chief = generator.spawn(world, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=region.difficulty)
                    chief.region_id = region.region_id
                    world.add_entity(chief)
                    self._total_spawned += 1
                    for g in range(min(cfg.camp_max_guards, 3)):
                        guard = generator.spawn(world, tier=EnemyTier.WARRIOR, near_pos=loc.pos, difficulty_tier=region.difficulty)
                        guard.region_id = region.region_id
                        world.add_entity(guard)
                        self._total_spawned += 1
                    # Also spawn race-specific mobs if terrain has a race
                    if race:
                        mob_count = self._rng.next_int(
                            Domain.SPAWN, int(mat) * 1000 + loc.pos.x, loc.pos.y, 2, 4)
                        for mi in range(mob_count):
                            ent = generator.spawn_race(world, race, near_pos=loc.pos, difficulty_tier=region.difficulty)
                            ent.region_id = region.region_id
                            world.add_entity(ent)
                            self._total_spawned += 1
                    logger.info("Spawned camp mobs at '%s' in %s (tier %d)", loc.name, region.name, region.difficulty)

                elif loc.location_type == "boss_arena":
                    # Elite boss + a few guards — boss arenas get +1 effective difficulty
                    boss_diff = min(region.difficulty + 1, 4)
                    boss = generator.spawn(world, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=boss_diff)
                    boss.region_id = region.region_id
                    world.add_entity(boss)
                    self._total_spawned += 1
                    if race:
                        elite = generator.spawn_race(world, race, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=boss_diff)
                        elite.region_id = region.region_id
                        world.add_entity(elite)
                        self._total_spawned += 1
                    logger.info("Spawned boss at '%s' in %s (tier %d)", loc.name, region.name, boss_diff)

                elif loc.location_type == "resource_grove":
                    # Cluster of 3-5 resource nodes
                    resource_defs = TERRAIN_RESOURCES.get(int(mat), [])
                    if resource_defs:
                        node_count = self._rng.next_int(
                            Domain.HARVEST, loc.pos.x * 100, loc.pos.y, 3, 5)
                        for ni in range(node_count):
                            rtype, rname, yields, max_h, respawn, h_ticks = resource_defs[
                                ni % len(resource_defs)]
                            for attempt in range(30):
                                ox = self._rng.next_int(Domain.HARVEST, loc.pos.x * 10 + ni, attempt, -4, 4)
                                oy = self._rng.next_int(Domain.HARVEST, loc.pos.y * 10 + ni, attempt + 50, -4, 4)
                                npos = Vector2(loc.pos.x + ox, loc.pos.y + oy)
                                if grid.in_bounds(npos) and grid.get(npos) in (mat, Material.FLOOR):
                                    nid = world.allocate_node_id()
                                    node = ResourceNode(
                                        node_id=nid, resource_type=rtype, name=rname,
                                        pos=npos, terrain=mat, yields_item=yields,
                                        remaining=max_h, max_harvests=max_h,
                                        respawn_cooldown=respawn, harvest_ticks=h_ticks,
                                    )
                                    world.add_resource_node(node)
                                    break

                elif loc.location_type == "dungeon_entrance":
                    # Elite guards at dungeon
                    if race:
                        for di in range(2):
                            guard = generator.spawn_race(world, race, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=region.difficulty)
                            guard.region_id = region.region_id
                            world.add_entity(guard)
                            self._total_spawned += 1

            # Also spawn some roaming race mobs throughout the region
            if race:
                roam_count = self._rng.next_int(
                    Domain.SPAWN, int(mat) * 500 + region.center.x, region.center.y, 2, 4)
                for mi in range(roam_count):
                    ent = generator.spawn_race(world, race, near_pos=region.center, difficulty_tier=region.difficulty)
                    ent.region_id = region.region_id
                    world.add_entity(ent)
                    self._total_spawned += 1

        # Also spawn some berry bushes on FLOOR tiles (wilds resources)
        for bi in range(12):
            for attempt in range(30):
                bx = self._rng.next_int(Domain.HARVEST, 5000 + bi, attempt, 0, cfg.grid_width - 1)
                by = self._rng.next_int(Domain.HARVEST, 5000 + bi, attempt + 50, 0, cfg.grid_height - 1)
                bpos = Vector2(bx, by)
                if grid.in_bounds(bpos) and grid.get(bpos) == Material.FLOOR:
                    nid = world.allocate_node_id()
                    node = ResourceNode(
                        node_id=nid, resource_type="berry_bush", name="Wild Berry Bush",
                        pos=bpos, terrain=Material.FLOOR, yields_item="wild_berries",
                        remaining=2, max_harvests=2, respawn_cooldown=25, harvest_ticks=1,
                    )
                    world.add_resource_node(node)
                    break
        logger.info("Placed %d resource nodes, %d regions with %d total locations",
                     len(world.resource_nodes), len(world.regions),
                     sum(len(r.locations) for r in world.regions))

        faction_reg = FactionRegistry.default()
        brain = AIBrain(cfg, self._rng, faction_reg)
        self._worker_pool = WorkerPool(cfg, brain)
        conflict_resolver = ConflictResolver(cfg, self._rng)

        self._loop = WorldLoop(
            config=cfg, world=world, worker_pool=self._worker_pool,
            conflict_resolver=conflict_resolver, generator=generator,
            faction_reg=faction_reg, rng=self._rng,
        )

        # Initial snapshot
        snap = self._loop.create_snapshot()
        with self._snapshot_lock:
            self._latest_snapshot = snap

    def _run_loop(self) -> None:
        """Background thread main loop."""
        logger.info("Engine thread started.")
        assert self._loop is not None

        while not self._stop_requested.is_set():
            # Handle pause
            if self._paused.is_set() and not self._step_requested.is_set():
                time.sleep(0.01)
                continue

            single_step = self._step_requested.is_set()
            if single_step:
                self._step_requested.clear()

            # Execute one tick
            alive_before = set(self._loop.world.entities.keys())
            can_continue = self._loop.tick_once()

            if not can_continue:
                self._publish_snapshot_and_events()
                logger.info("Simulation ended at tick %d.", self._loop.world.tick)
                break

            # Track spawns / deaths
            alive_after = set(self._loop.world.entities.keys())
            new_ids = alive_after - alive_before
            dead_ids = alive_before - alive_after
            self._total_spawned += len(new_ids)
            self._total_deaths += len(dead_ids)

            self._publish_snapshot_and_events()

            # Rate limiting
            if not single_step:
                time.sleep(self._tick_rate)

        self._running.clear()
        logger.info("Engine thread exited.")

    def _publish_snapshot_and_events(self) -> None:
        """Swap snapshot + push events from last_applied."""
        assert self._loop is not None
        snap = self._loop.create_snapshot()
        with self._snapshot_lock:
            self._latest_snapshot = snap

        events: list[SimEvent] = self._loop.tick_events
        if events:
            self._event_log.append_many(events)

    def _current_tick(self) -> int:
        if self._loop:
            return self._loop.world.tick
        return 0
