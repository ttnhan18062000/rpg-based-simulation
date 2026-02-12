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
from src.core.items import Inventory, TERRAIN_RACE
from src.core.models import Entity, Stats, Vector2
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

        # --- Place terrain regions (forest, desert, swamp, mountain) ---
        region_specs = [
            (Material.FOREST, cfg.num_forest_regions),
            (Material.DESERT, cfg.num_desert_regions),
            (Material.SWAMP, cfg.num_swamp_regions),
            (Material.MOUNTAIN, cfg.num_mountain_regions),
        ]
        region_centers: list[Vector2] = []  # track all region centers for spacing
        terrain_region_centers: dict[int, list[Vector2]] = {}  # Material -> list of centers

        for mat, count in region_specs:
            terrain_region_centers[mat] = []
            for ri in range(count):
                seed_key = mat * 100 + ri
                for attempt in range(80):
                    rx = self._rng.next_int(Domain.MAP_GEN, seed_key, attempt, 4, cfg.grid_width - 5)
                    ry = self._rng.next_int(Domain.MAP_GEN, seed_key, attempt + 200, 4, cfg.grid_height - 5)
                    rpos = Vector2(rx, ry)
                    if rpos.manhattan(town_center) < cfg.camp_min_distance_from_town:
                        continue
                    too_close = any(rpos.manhattan(rc) < cfg.region_min_distance for rc in region_centers)
                    if too_close:
                        continue
                    # Place region tiles with organic shape
                    radius = self._rng.next_int(Domain.MAP_GEN, seed_key, attempt + 400,
                                                cfg.region_min_radius, cfg.region_max_radius)
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            # Use Manhattan distance with some noise for organic shape
                            dist = abs(dx) + abs(dy)
                            if dist > radius:
                                continue
                            # Noise: skip some edge tiles for organic feel
                            if dist > radius - 2:
                                noise = self._rng.next_float(Domain.MAP_GEN, seed_key + dx * 31 + dy * 17, attempt)
                                if noise < 0.3:
                                    continue
                            tp = Vector2(rx + dx, ry + dy)
                            if grid.in_bounds(tp) and grid.get(tp) == Material.FLOOR:
                                grid.set(tp, mat)
                    region_centers.append(rpos)
                    terrain_region_centers[mat].append(rpos)
                    logger.info("Placed %s region at %s (r=%d)", mat.name, rpos, radius)
                    break

        # --- Place goblin camps (on FLOOR tiles) ---
        generator = EntityGenerator(cfg, self._rng)
        camp_positions: list[Vector2] = []
        for camp_idx in range(cfg.num_camps):
            for attempt in range(80):
                cx = self._rng.next_int(Domain.SPAWN, 9000 + camp_idx, attempt, 0, cfg.grid_width - 1)
                cy = self._rng.next_int(Domain.SPAWN, 9000 + camp_idx, attempt + 100, 0, cfg.grid_height - 1)
                camp_pos = Vector2(cx, cy)
                if camp_pos.manhattan(town_center) < cfg.camp_min_distance_from_town:
                    continue
                too_close = any(camp_pos.manhattan(ex) < cfg.camp_radius * 4 for ex in camp_positions)
                if too_close:
                    continue
                if not grid.in_bounds(camp_pos):
                    continue
                # Place camp tiles
                for cty in range(cy - cfg.camp_radius, cy + cfg.camp_radius + 1):
                    for ctx_val in range(cx - cfg.camp_radius, cx + cfg.camp_radius + 1):
                        cp = Vector2(ctx_val, cty)
                        if grid.in_bounds(cp) and grid.get(cp) in (Material.FLOOR, Material.FOREST, Material.DESERT, Material.SWAMP, Material.MOUNTAIN):
                            grid.set(cp, Material.CAMP)
                camp_positions.append(camp_pos)
                world.camps.append(camp_pos)
                logger.info("Placed goblin camp at %s", camp_pos)
                break

        # --- Generate roads from town to nearby camps/regions ---
        if cfg.road_from_town:
            road_targets: list[Vector2] = []
            # Pick the 3 closest camps
            sorted_camps = sorted(camp_positions, key=lambda c: c.manhattan(town_center))
            road_targets.extend(sorted_camps[:3])
            # Pick the 2 closest region centers
            sorted_regions = sorted(region_centers, key=lambda r: r.manhattan(town_center))
            road_targets.extend(sorted_regions[:2])
            for rt in road_targets:
                # Simple axis-aligned road: walk X first, then Y
                cx, cy = town_center.x, town_center.y
                tx, ty = rt.x, rt.y
                # Horizontal segment
                step_x = 1 if tx > cx else -1
                x = cx
                while x != tx:
                    x += step_x
                    rp = Vector2(x, cy)
                    if grid.in_bounds(rp) and grid.get(rp) == Material.FLOOR:
                        grid.set(rp, Material.ROAD)
                # Vertical segment
                step_y = 1 if ty > cy else -1
                y = cy
                while y != ty:
                    y += step_y
                    rp = Vector2(tx, y)
                    if grid.in_bounds(rp) and grid.get(rp) == Material.FLOOR:
                        grid.set(rp, Material.ROAD)
            logger.info("Generated roads to %d targets", len(road_targets))

        # --- Place ruins ---
        ruin_positions: list[Vector2] = []
        for ri in range(cfg.num_ruins):
            for attempt in range(60):
                rx = self._rng.next_int(Domain.MAP_GEN, 7000 + ri, attempt, 4, cfg.grid_width - 5)
                ry = self._rng.next_int(Domain.MAP_GEN, 7000 + ri, attempt + 100, 4, cfg.grid_height - 5)
                rpos = Vector2(rx, ry)
                if rpos.manhattan(town_center) < cfg.camp_min_distance_from_town // 2:
                    continue
                too_close = any(rpos.manhattan(rp) < 8 for rp in ruin_positions)
                if too_close:
                    continue
                if grid.in_bounds(rpos) and grid.get(rpos) in (Material.FLOOR, Material.ROAD):
                    # Place a small 3x3 ruin patch
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            tp = Vector2(rx + dx, ry + dy)
                            if grid.in_bounds(tp) and grid.get(tp) in (Material.FLOOR, Material.ROAD):
                                grid.set(tp, Material.RUINS)
                    ruin_positions.append(rpos)
                    logger.info("Placed ruins at %s", rpos)
                    break

        # --- Place dungeon entrances ---
        dungeon_positions: list[Vector2] = []
        for di in range(cfg.num_dungeon_entrances):
            for attempt in range(80):
                dx = self._rng.next_int(Domain.MAP_GEN, 8000 + di, attempt, 4, cfg.grid_width - 5)
                dy = self._rng.next_int(Domain.MAP_GEN, 8000 + di, attempt + 100, 4, cfg.grid_height - 5)
                dpos = Vector2(dx, dy)
                if dpos.manhattan(town_center) < cfg.camp_min_distance_from_town:
                    continue
                too_close = any(dpos.manhattan(dp) < 15 for dp in dungeon_positions)
                if too_close:
                    continue
                if grid.in_bounds(dpos) and grid.get(dpos) in (Material.FLOOR, Material.MOUNTAIN, Material.FOREST):
                    grid.set(dpos, Material.DUNGEON_ENTRANCE)
                    dungeon_positions.append(dpos)
                    logger.info("Placed dungeon entrance at %s", dpos)
                    break

        # --- Spawn treasure chests near camps ---
        from src.core.items import TreasureChest
        chest_tier_cycle = [1, 1, 2, 2, 3]  # Distribute tiers across camps
        for ci, camp_pos in enumerate(camp_positions):
            chest_tier = chest_tier_cycle[ci % len(chest_tier_cycle)]
            # Place chest a few tiles from camp center
            offset_x = self._rng.next_int(Domain.MAP_GEN, 11000 + ci, 0, -3, 3)
            offset_y = self._rng.next_int(Domain.MAP_GEN, 11000 + ci, 1, -3, 3)
            cx = max(1, min(cfg.grid_width - 2, camp_pos.x + offset_x))
            cy = max(1, min(cfg.grid_height - 2, camp_pos.y + offset_y))
            chest_pos = Vector2(cx, cy)
            cid = world._next_chest_id
            world._next_chest_id += 1
            chest = TreasureChest(chest_id=cid, pos=chest_pos, tier=chest_tier)
            world.treasure_chests[cid] = chest
            logger.info("Placed tier-%d treasure chest #%d at %s (near camp %s)",
                        chest_tier, cid, chest_pos, camp_pos)

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

        # --- Spawn initial goblins ---
        for i in range(1, cfg.initial_entity_count):
            entity = generator.spawn(world)
            world.add_entity(entity)
            self._total_spawned += 1

        # --- Spawn camp guards (chief + guards at each camp) ---
        for camp_pos in camp_positions:
            chief = generator.spawn(world, tier=EnemyTier.ELITE, near_pos=camp_pos)
            world.add_entity(chief)
            self._total_spawned += 1
            logger.info("Spawned %s #%d (chief) at camp %s", chief.kind, chief.id, camp_pos)

            for g in range(min(cfg.camp_max_guards, 3)):
                guard = generator.spawn(world, tier=EnemyTier.WARRIOR, near_pos=camp_pos)
                world.add_entity(guard)
                self._total_spawned += 1

        # --- Spawn race-specific mobs in terrain regions ---
        for mat, centers in terrain_region_centers.items():
            race = TERRAIN_RACE.get(int(mat))
            if not race:
                continue
            for center in centers:
                # Spawn 2-4 mobs per region
                mob_count = self._rng.next_int(Domain.SPAWN, int(mat) * 1000 + center.x, center.y, 2, 4)
                for mi in range(mob_count):
                    ent = generator.spawn_race(world, race, near_pos=center)
                    world.add_entity(ent)
                    self._total_spawned += 1
                # Spawn 1 elite per region
                elite = generator.spawn_race(world, race, tier=EnemyTier.ELITE, near_pos=center)
                world.add_entity(elite)
                self._total_spawned += 1
                logger.info("Spawned %s pack at %s region %s", race, mat.name, center)

        # --- Spawn resource nodes in terrain regions ---
        for mat, centers in terrain_region_centers.items():
            resource_defs = TERRAIN_RESOURCES.get(int(mat), [])
            if not resource_defs:
                continue
            for center in centers:
                for ri in range(cfg.resources_per_region):
                    rtype, rname, yields, max_h, respawn, h_ticks = resource_defs[
                        ri % len(resource_defs)]
                    # Random position near region center
                    for attempt in range(30):
                        ox = self._rng.next_int(Domain.HARVEST, center.x * 100 + ri, attempt, -6, 6)
                        oy = self._rng.next_int(Domain.HARVEST, center.y * 100 + ri, attempt + 50, -6, 6)
                        npos = Vector2(center.x + ox, center.y + oy)
                        if grid.in_bounds(npos) and grid.get(npos) == mat:
                            nid = world.allocate_node_id()
                            node = ResourceNode(
                                node_id=nid, resource_type=rtype, name=rname,
                                pos=npos, terrain=mat, yields_item=yields,
                                remaining=max_h, max_harvests=max_h,
                                respawn_cooldown=respawn, harvest_ticks=h_ticks,
                            )
                            world.add_resource_node(node)
                            break
        # Also spawn some berry bushes on FLOOR tiles
        for bi in range(8):
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
        logger.info("Placed %d resource nodes", len(world.resource_nodes))

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
