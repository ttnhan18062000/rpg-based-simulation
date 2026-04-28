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
