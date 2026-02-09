"""Simulation configuration with sensible defaults."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SimulationConfig:
    """Immutable configuration for the simulation run."""

    # World
    world_seed: int = 42
    grid_width: int = 128
    grid_height: int = 128

    # Timing
    max_ticks: int = 1000
    worker_timeout_seconds: float = 2.0

    # Workers
    num_workers: int = 4

    # Entities
    initial_entity_count: int = 25
    generator_spawn_interval: int = 10
    generator_max_entities: int = 80

    # Spatial hash
    spatial_cell_size: int = 8

    # AI
    vision_range: int = 6
    flee_hp_threshold: float = 0.3

    # Town
    town_center_x: int = 12
    town_center_y: int = 12
    town_radius: int = 4
    town_aura_damage: int = 2              # HP lost per tick by hostile entities in town
    town_passive_heal: int = 1             # HP regained per tick by heroes in town (even outside rest)

    # Hero
    hero_respawn_ticks: int = 10
    hero_heal_per_tick: int = 3

    # Combat
    base_damage: int = 5
    damage_variance: float = 0.3
    crit_chance: float = 0.1
    crit_multiplier: float = 2.0

    # Leveling
    xp_per_kill_base: int = 30
    xp_per_level_scale: float = 1.5
    stat_growth_hp: int = 5
    stat_growth_atk: int = 1
    stat_growth_def: int = 1
    stat_growth_spd: int = 1
    max_level: int = 20

    # Inventory
    hero_inventory_slots: int = 12
    hero_inventory_weight: float = 30.0
    goblin_inventory_slots: int = 4
    goblin_inventory_weight: float = 10.0

    # Camps
    num_camps: int = 8
    camp_radius: int = 2
    camp_spawn_interval: int = 20
    camp_max_guards: int = 5
    camp_min_distance_from_town: int = 25

    # Sanctuary (buffer zone around town)
    sanctuary_radius: int = 7

    # Regions
    num_forest_regions: int = 4
    num_desert_regions: int = 3
    num_swamp_regions: int = 3
    num_mountain_regions: int = 3
    region_min_radius: int = 6
    region_max_radius: int = 12
    region_min_distance: int = 8

    # Roads & structures
    num_ruins: int = 4                         # Scattered ruins on the map
    num_dungeon_entrances: int = 2             # Dungeon entrances in remote areas
    road_from_town: bool = True                # Generate roads from town outward

    # Resource nodes
    resources_per_region: int = 4
    resource_respawn_ticks: int = 30
    harvest_duration: int = 2

    # Territory intrusion
    territory_debuff_duration: int = 3      # Ticks the debuff lasts after leaving
    territory_alert_radius: int = 6         # How far intrusion alert propagates

    # Looting
    loot_duration: int = 3                  # Ticks to channel before picking up loot

    # Logging
    log_level: str = "INFO"
    replay_file: str = "replay.json"
