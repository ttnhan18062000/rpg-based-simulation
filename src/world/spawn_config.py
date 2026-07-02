# Compliance IDs: SOC-026, SOC-027, SOC-028, SOC-029, SOC-030, SOC-031, SOC-032, SOC-033, SOC-034, SOC-035, SOC-036, SOC-037, SOC-038, SOC-039, SOC-040, SOC-041, TOWN-072, TOWN-078, WORLD-042, WORLD-048, WORLD-049
# Compliance IDs: SOC-026, SOC-027, SOC-028, SOC-029, SOC-030, SOC-031, SOC-032, SOC-033, SOC-034, SOC-035, SOC-036, SOC-037, SOC-038, SOC-039, SOC-040, SOC-041, TOWN-072, TOWN-078
# Parity: WORLD-103 (SpawnService two-tier cadence)
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class DifficultyMultipliers:
    """Stat multipliers for a given difficulty tier."""
    hp: float
    atk: float
    def_stat: float
    xp: float
    gold: float
    level_min: int
    level_max: int

DIFFICULTY_TIERS: dict[int, DifficultyMultipliers] = {
    1: DifficultyMultipliers(hp=1.0, atk=1.0, def_stat=1.0, xp=1.0, gold=1.0, level_min=1, level_max=3),
    2: DifficultyMultipliers(hp=1.5, atk=1.3, def_stat=1.2, xp=1.5, gold=1.5, level_min=3, level_max=6),
    3: DifficultyMultipliers(hp=2.5, atk=2.0, def_stat=1.8, xp=3.0, gold=2.5, level_min=5, level_max=10),
    4: DifficultyMultipliers(hp=4.0, atk=3.0, def_stat=2.5, xp=5.0, gold=4.0, level_min=8, level_max=15),
}

# Mapping distance from town center to difficulty tier
DIFFICULTY_ZONES = (
    (80, 1),
    (150, 2),
    (220, 3),
    (999, 4),
)
# Regional Spawn Pools
SPAWN_POOLS = {
    "FOREST": ["goblin", "wolf", "bear"],
    "PLAINS": ["slime", "bandit"],
    "MOUNTAIN": ["harpy", "golem"],
}

# Target density (Monsters per 100x100 area per hazard level)
BASE_MONSTER_DENSITY = 2.0


# ---------------------------------------------------------------------------
# Two-tier spawn cadence configuration (WORLD-103)
#
# Problem: A single entity spawned per region per 50-tick interval cannot
# compensate for late-run combat attrition (ticks 800–1000). The population
# trends downward and risks approaching zero in runs beyond 1,000 ticks.
#
# Fix: Two-tier cadence — slow early spawn, faster late spawn:
#   - Ticks 0 … late_spawn_threshold_tick-1  → base_spawn_batch_size  (default 1)
#   - Ticks late_spawn_threshold_tick …       → late_spawn_batch_size  (default 2)
#
# The batch cap is applied per region per interval; it never exceeds the
# density deficit (target_count - current_count) for that region.
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SpawnConfig:
    """Cadence parameters for SpawnService.process_spawns()."""
    # How many entities to spawn per region per interval in early game
    base_spawn_batch_size: int = 1
    # Tick at which the late-game cadence kicks in
    late_spawn_threshold_tick: int = 500
    # How many entities to spawn per region per interval in late game
    late_spawn_batch_size: int = 2


DEFAULT_SPAWN_CONFIG = SpawnConfig()
