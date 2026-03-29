
import logging
from src.core.models.enums import Domain, EnemyTier, EntityRole, Material
from src.core.gameplay.faction import Faction
from src.core.world.grid import Grid
from src.core.models import Vector2, TreasureChest
from src.core.gameplay.buildings import Building
from src.core.models.world_state import WorldState
from src.core.world.regions import (
    Region, Location, LOCATION_NAME_TEMPLATES, TERRAIN_RACE_LABEL,
    difficulty_for_distance, pick_region_name, reset_name_counters,
)
from src.core.world.resource_nodes import ResourceNode, TERRAIN_RESOURCES
from src.core.gameplay.items.items import TERRAIN_RACE
from src.systems.world.generator import EntityGenerator
from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash

logger = logging.getLogger(__name__)

TERRAIN_RACE_MAP = {
    int(Material.FOREST): "Goblin",
    int(Material.DESERT): "Orc",
    int(Material.SWAMP): "Undead",
    int(Material.MOUNTAIN): "Drake",
    int(Material.GRASSLAND): "Humanoid",
    int(Material.SNOW): "Frostborn",
    int(Material.JUNGLE): "Beast",
    int(Material.VOLCANIC): "Elemental",
}

class WorldGenerator:
    """Service class responsible for procedurally generating a new WorldState.
    
    This decouples the engine's lifecycle management (EngineManager) from the
    complex map generation, building placement, and initial entity spawning.
    """

    def __init__(self, cfg, rng: DeterministicRNG):
        self.cfg = cfg
        self.rng = rng
        self.total_spawned = 0

    def generate(self) -> tuple[WorldState, EntityGenerator]:
        """Generate a completely new world from scratch based on the provided config."""
        cfg = self.cfg
        rng = self.rng
        self.total_spawned = 0

        grid = Grid(cfg.grid_width, cfg.grid_height)
        spatial = SpatialHash(cfg.spatial_cell_size)
        world = WorldState(seed=cfg.world_seed, grid=grid, spatial_index=spatial)

        town_center = Vector2(cfg.town_center_x, cfg.town_center_y)
        TOWN_TILES = frozenset({Material.TOWN, Material.SANCTUARY})

        # --- 1. Base Terrain Layout ---
        self._place_town_and_sanctuary(grid, cfg)
        
        region_seeds = self._place_region_seeds(cfg, rng, town_center)
        region_max_dist = self._assign_voronoi_regions(grid, cfg, region_seeds, TOWN_TILES)
        
        # --- 2. Regions and Locations ---
        reset_name_counters()
        generator = EntityGenerator(cfg, rng)
        zone_bounds = list(cfg.difficulty_zones)
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

            self._generate_locations_in_region(world, region, grid, cfg, rng, idx, mat, region_id, difficulty, effective_radius)
            
            world.regions.append(region)
            region_centers.append(rpos)
            logger.info("Created region '%s' (%s, tier %d) at %s r=%d with %d locations",
                        region.name, mat.name, difficulty, rpos, effective_radius, len(region.locations))

        # --- 3. Terrain Detail & Roads ---
        from src.systems.world.terrain_detail import TerrainDetailGenerator
        terrain_gen = TerrainDetailGenerator(grid, rng)
        terrain_gen.generate_all(world.regions)

        if cfg.road_from_town:
            self._generate_roads(grid, cfg, town_center, region_centers)

        # --- 4. Buildings (Town) ---
        self._place_town_buildings(world, cfg, town_center)

        # --- 5. Initial Entities ---
        self._spawn_initial_entities(world, generator, cfg, rng, town_center)

        logger.info("Generated world with %d entities, %d buildings, %d regions",
                    len(world.entities), len(world.buildings), len(world.regions))
        return world, generator

    def _place_town_and_sanctuary(self, grid: Grid, cfg):
        # Place town tiles (safe zone)
        for ty in range(cfg.town_center_y - cfg.town_radius, cfg.town_center_y + cfg.town_radius + 1):
            for tx in range(cfg.town_center_x - cfg.town_radius, cfg.town_center_x + cfg.town_radius + 1):
                pos = Vector2(tx, ty)
                if grid.in_bounds(pos):
                    grid.set(pos, Material.TOWN)

        # Place sanctuary tiles (debuff zone around town)
        for sy in range(cfg.town_center_y - cfg.sanctuary_radius, cfg.town_center_y + cfg.sanctuary_radius + 1):
            for sx in range(cfg.town_center_x - cfg.sanctuary_radius, cfg.town_center_x + cfg.sanctuary_radius + 1):
                pos = Vector2(sx, sy)
                if grid.in_bounds(pos) and grid.get(pos) == Material.FLOOR:
                    grid.set(pos, Material.SANCTUARY)

    def _place_region_seeds(self, cfg, rng: DeterministicRNG, town_center: Vector2):
        region_specs = [
            (Material.FOREST, cfg.num_forest_regions),
            (Material.DESERT, cfg.num_desert_regions),
            (Material.SWAMP, cfg.num_swamp_regions),
            (Material.MOUNTAIN, cfg.num_mountain_regions),
            (Material.GRASSLAND, cfg.num_grassland_regions),
            (Material.SNOW, cfg.num_snow_regions),
            (Material.JUNGLE, cfg.num_jungle_regions),
            (Material.VOLCANIC, cfg.num_volcanic_regions),
        ]
        region_seeds: list[tuple[Vector2, Material]] = []
        for mat, count in region_specs:
            for ri in range(count):
                seed_key = mat * 100 + ri
                for attempt in range(120):
                    rx = rng.next_int(Domain.MAP_GEN, seed_key, attempt, 6, cfg.grid_width - 7)
                    ry = rng.next_int(Domain.MAP_GEN, seed_key, attempt + 200, 6, cfg.grid_height - 7)
                    rpos = Vector2(rx, ry)
                    if rpos.manhattan(town_center) < cfg.camp_min_distance_from_town:
                        continue
                    too_close = any(rpos.manhattan(s[0]) < cfg.region_min_distance for s in region_seeds)
                    if too_close:
                        continue
                    region_seeds.append((rpos, mat))
                    break
        return region_seeds

    def _assign_voronoi_regions(self, grid: Grid, cfg, region_seeds, town_tiles):
        region_max_dist: dict[int, int] = {i: 0 for i in range(len(region_seeds))}
        for y in range(cfg.grid_height):
            for x in range(cfg.grid_width):
                pos = Vector2(x, y)
                if grid.get(pos) in town_tiles:
                    continue
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
        return region_max_dist

    def _generate_locations_in_region(self, world, region, grid, cfg, rng: DeterministicRNG, idx, mat, region_id, difficulty, effective_radius):
        seed_key = mat * 100 + (idx % 10)
        num_locs = rng.next_int(Domain.MAP_GEN, seed_key, 500 + idx, cfg.min_locations_per_region, cfg.max_locations_per_region)
        loc_positions: list[Vector2] = []
        race_label = TERRAIN_RACE_LABEL.get(int(mat), "Goblin")

        loc_types: list[str] = ["enemy_camp", "resource_grove"]
        if difficulty >= 3:
            loc_types.extend(["dungeon_entrance", "boss_arena", "portal"])
        else:
            loc_types.extend(["shrine", "outpost"])
        loc_types.append("ruins")
        
        if mat in (Material.SWAMP, Material.SNOW, Material.GRAVEYARD):
            loc_types.append("graveyard")
        if mat in (Material.GRASSLAND, Material.JUNGLE, Material.FOREST):
            loc_types.append("watchtower")
        if mat in (Material.DESERT, Material.VOLCANIC, Material.MOUNTAIN):
            loc_types.append("obelisk")

        while len(loc_types) < num_locs:
            extra = ["enemy_camp", "resource_grove", "ruins", "fishing_spot"]
            pick = rng.next_int(Domain.MAP_GEN, seed_key + len(loc_types), 600 + idx, 0, len(extra) - 1)
            loc_types.append(extra[pick])

        loc_range = max(effective_radius // 2, 8)
        for li, loc_type in enumerate(loc_types[:num_locs]):
            for loc_attempt in range(60):
                ox = rng.next_int(Domain.MAP_GEN, seed_key + li * 100, loc_attempt + 700, -loc_range, loc_range)
                oy = rng.next_int(Domain.MAP_GEN, seed_key + li * 100, loc_attempt + 800, -loc_range, loc_range)
                lpos = Vector2(region.center.x + ox, region.center.y + oy)
                if not grid.in_bounds(lpos) or grid.get(lpos) != mat:
                    continue
                if any(lpos.manhattan(lp) < cfg.location_min_spacing for lp in loc_positions):
                    continue

                templates = LOCATION_NAME_TEMPLATES.get(loc_type, ["{race} Place"])
                tpl_idx = rng.next_int(Domain.MAP_GEN, seed_key + li, loc_attempt + 900, 0, len(templates) - 1)
                loc_name = templates[tpl_idx].format(race=race_label)
                loc_id = f"{region_id}_{loc_type}_{li}"

                loc = Location(location_id=loc_id, name=loc_name, location_type=loc_type, pos=lpos, region_id=region_id)
                region.locations.append(loc)
                loc_positions.append(lpos)
                self._paint_location_terrain(world, loc, grid, cfg, mat, difficulty)
                break

    def _paint_location_terrain(self, world, loc, grid, cfg, mat, difficulty):
        if loc.location_type == "enemy_camp":
            for cdy in range(-cfg.camp_radius, cfg.camp_radius + 1):
                for cdx in range(-cfg.camp_radius, cfg.camp_radius + 1):
                    cp = Vector2(loc.pos.x + cdx, loc.pos.y + cdy)
                    if grid.in_bounds(cp) and grid.get(cp) == mat:
                        grid.set(cp, Material.CAMP)
            world.camps.append(loc.pos)
        elif loc.location_type == "ruins":
            for rdy in range(-1, 2):
                for rdx in range(-1, 2):
                    rtp = Vector2(loc.pos.x + rdx, loc.pos.y + rdy)
                    if grid.in_bounds(rtp) and grid.get(rtp) == mat:
                        grid.set(rtp, Material.RUINS)
        elif loc.location_type == "dungeon_entrance":
            grid.set(loc.pos, Material.DUNGEON_ENTRANCE)
        elif loc.location_type == "graveyard":
            for gdy in range(-2, 3):
                for gdx in range(-2, 3):
                    gp = Vector2(loc.pos.x + gdx, loc.pos.y + gdy)
                    if grid.in_bounds(gp) and grid.get(gp) == mat:
                        grid.set(gp, Material.GRAVEYARD)
        elif loc.location_type in ("outpost", "watchtower", "portal", "fishing_spot", "obelisk"):
            world.buildings.append(Building(building_id=loc.location_id, name=loc.name, pos=loc.pos, building_type=loc.location_type))

        if loc.location_type in ("ruins", "dungeon_entrance"):
            cid = world._next_chest_id
            world._next_chest_id += 1
            world.treasure_chests[cid] = TreasureChest(chest_id=cid, pos=loc.pos, tier=min(difficulty, 4))

    def _generate_roads(self, grid: Grid, cfg, town_center: Vector2, region_centers: list[Vector2]):
        ROAD_PAINTABLE = frozenset({
            Material.FLOOR, Material.FOREST, Material.DESERT, Material.SWAMP,
            Material.MOUNTAIN, Material.GRASSLAND, Material.SNOW, Material.JUNGLE,
            Material.VOLCANIC, Material.FARMLAND, Material.GRAVEYARD,
        })
        sorted_regions = sorted(region_centers, key=lambda r: r.manhattan(town_center))
        for rt in sorted_regions[:8]:
            cx, cy = town_center.x, town_center.y
            tx, ty = rt.x, rt.y
            step_x = 1 if tx > cx else -1
            x = cx
            while x != tx:
                x += step_x
                rp = Vector2(x, cy)
                if grid.in_bounds(rp):
                    tile = grid.get(rp)
                    if tile in ROAD_PAINTABLE: grid.set(rp, Material.ROAD)
                    elif tile == Material.WATER: grid.set(rp, Material.BRIDGE)
            step_y = 1 if ty > cy else -1
            y = cy
            while y != ty:
                y += step_y
                rp = Vector2(tx, y)
                if grid.in_bounds(rp):
                    tile = grid.get(rp)
                    if tile in ROAD_PAINTABLE: grid.set(rp, Material.ROAD)
                    elif tile == Material.WATER: grid.set(rp, Material.BRIDGE)

    def _place_town_buildings(self, world, cfg, town_center: Vector2):
        town_radius = cfg.town_radius
        buildings = [
            ("store", "General Store", Vector2(town_center.x - town_radius + 1, town_center.y - town_radius + 1), "store"),
            ("blacksmith", "Blacksmith", Vector2(town_center.x + town_radius - 1, town_center.y - town_radius + 1), "blacksmith"),
            ("guild", "Adventurer's Guild", Vector2(town_center.x, town_center.y + town_radius - 1), "guild"),
            ("class_hall", "Class Hall", Vector2(town_center.x - town_radius + 1, town_center.y + town_radius - 1), "class_hall"),
            ("inn", "Traveler's Inn", Vector2(town_center.x + town_radius - 1, town_center.y + town_radius - 1), "inn"),
        ]
        for bid, name, pos, btype in buildings:
            world.buildings.append(Building(building_id=bid, name=name, pos=pos, building_type=btype))

    def _spawn_initial_entities(self, world, generator: EntityGenerator, cfg, rng: DeterministicRNG, town_center: Vector2):
        from src.core.gameplay.classes import HeroClass, HERO_STARTING_GEAR
        from src.core.entities.entity_builder import EntityBuilder
        from src.core.data.hero_names import generate_hero_name
        from src.core.models.enums import Faction

        class_choices = [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]
        for h_idx in range(cfg.hero_count):
            hero_eid = world.allocate_entity_id()
            hero_class = class_choices[h_idx % len(class_choices)]
            gear = HERO_STARTING_GEAR.get(hero_class, {})
            builder = (EntityBuilder(rng, hero_eid, tick=0).kind("hero").at(Vector2(cfg.town_center_x, cfg.town_center_y)).home(town_center).faction(Faction.HERO_GUILD).role(EntityRole.HERO))
            builder.with_traits(race_prefix="hero")
            hero_name = generate_hero_name(rng, hero_eid, 0, builder._traits)
            hero = (builder.with_identity(display_name=hero_name, generation=1).with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3, crit_rate=0.08, crit_dmg=1.8, evasion=0.03, gold=50).with_randomized_stats().with_hero_class(hero_class).with_race_skills("hero").with_class_skills(hero_class, level=1).with_inventory(max_slots=cfg.hero_inventory_slots, max_weight=cfg.hero_inventory_weight, weapon=gear.get("weapon", "iron_sword"), armor=gear.get("armor", "leather_vest"), accessory=gear.get("accessory")).with_starting_items(["small_hp_potion"] * 3).with_home_storage().with_talents(race="hero").build())
            world.add_entity(hero)
            self.total_spawned += 1
            
            # Hero house
            h_pos = Vector2(cfg.town_center_x + (h_idx % 3) - 1, cfg.town_center_y + (h_idx // 3) + 1)
            world.buildings.append(Building(building_id=f"hero_house_{hero_eid}", name=f"{hero_name}'s House", pos=h_pos, building_type="hero_house"))

        # Global wanderers
        for _ in range(1, cfg.initial_entity_count):
            world.add_entity(generator.spawn(world))
            self.total_spawned += 1

        # Region-specific spawns
        for region in world.regions:
            mat = region.terrain
            race = TERRAIN_RACE.get(int(mat))
            for loc in region.locations:
                self._spawn_location_mobs(world, loc, region, generator, cfg, rng, mat, race)
            
            if race:
                roam_count = rng.next_int(Domain.SPAWN, int(mat) * 500 + region.center.x, region.center.y, 2, 4)
                for _ in range(roam_count):
                    ent = generator.spawn_race(world, race, near_pos=region.center, difficulty_tier=region.difficulty)
                    ent.region_id = region.region_id
                    world.add_entity(ent)
                    self.total_spawned += 1

        # Resource nodes
        self._spawn_wild_resources(world, cfg, rng)

    def _spawn_location_mobs(self, world, loc, region, generator: EntityGenerator, cfg, rng: DeterministicRNG, mat, race):
        if loc.location_type == "enemy_camp":
            chief = generator.spawn(world, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=region.difficulty)
            chief.region_id = region.region_id
            world.add_entity(chief)
            self.total_spawned += 1
            for _ in range(min(cfg.camp_max_guards, 3)):
                guard = generator.spawn(world, tier=EnemyTier.WARRIOR, near_pos=loc.pos, difficulty_tier=region.difficulty)
                guard.region_id = region.region_id
                world.add_entity(guard)
                self.total_spawned += 1
            if race:
                mob_count = rng.next_int(Domain.SPAWN, int(mat) * 1000 + loc.pos.x, loc.pos.y, 2, 4)
                for _ in range(mob_count):
                    ent = generator.spawn_race(world, race, near_pos=loc.pos, difficulty_tier=region.difficulty)
                    ent.region_id = region.region_id
                    world.add_entity(ent)
                    self.total_spawned += 1
        elif loc.location_type == "boss_arena":
            boss_diff = min(region.difficulty + 1, 4)
            boss = generator.spawn(world, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=boss_diff)
            boss.region_id = region.region_id
            world.add_entity(boss)
            self.total_spawned += 1
            if race:
                elite = generator.spawn_race(world, race, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=boss_diff)
                elite.region_id = region.region_id
                world.add_entity(elite)
                self.total_spawned += 1
        elif loc.location_type == "resource_grove":
            resource_defs = TERRAIN_RESOURCES.get(int(mat), [])
            if resource_defs:
                node_count = rng.next_int(Domain.HARVEST, loc.pos.x * 100, loc.pos.y, 3, 5)
                for ni in range(node_count):
                    rtype, rname, yields, max_h, respawn, h_ticks = resource_defs[ni % len(resource_defs)]
                    for attempt in range(30):
                        ox = rng.next_int(Domain.HARVEST, loc.pos.x * 10 + ni, attempt, -4, 4)
                        oy = rng.next_int(Domain.HARVEST, loc.pos.y * 10 + ni, attempt + 50, -4, 4)
                        npos = Vector2(loc.pos.x + ox, loc.pos.y + oy)
                        if world.grid.in_bounds(npos) and world.grid.get(npos) in (mat, Material.FLOOR):
                            node = ResourceNode(node_id=world.allocate_node_id(), resource_type=rtype, name=rname, pos=npos, terrain=mat, yields_item=yields, remaining=max_h, max_harvests=max_h, respawn_cooldown=respawn, harvest_ticks=h_ticks)
                            world.add_resource_node(node)
                            break
        elif loc.location_type == "dungeon_entrance":
            if race:
                for _ in range(2):
                    guard = generator.spawn_race(world, race, tier=EnemyTier.ELITE, near_pos=loc.pos, difficulty_tier=region.difficulty)
                    guard.region_id = region.region_id
                    world.add_entity(guard)
                    self.total_spawned += 1

    def _spawn_wild_resources(self, world, cfg, rng: DeterministicRNG):
        for bi in range(12):
            for attempt in range(30):
                bx = rng.next_int(Domain.HARVEST, 5000 + bi, attempt, 0, cfg.grid_width - 1)
                by = rng.next_int(Domain.HARVEST, 5000 + bi, attempt + 50, 0, cfg.grid_height - 1)
                bpos = Vector2(bx, by)
                if world.grid.in_bounds(bpos) and world.grid.get(bpos) == Material.FLOOR:
                    node = ResourceNode(node_id=world.allocate_node_id(), resource_type="berry_bush", name="Wild Berry Bush", pos=bpos, terrain=Material.FLOOR, yields_item="wild_berries", remaining=2, max_harvests=2, respawn_cooldown=25, harvest_ticks=1)
                    world.add_resource_node(node)
                    break
