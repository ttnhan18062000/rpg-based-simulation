# Compliance IDs: SOC-026, SOC-027, SOC-028, SOC-029, SOC-030, SOC-031, SOC-032, SOC-033, SOC-034, SOC-035, SOC-036, SOC-037, SOC-038, SOC-039, SOC-040, SOC-041, TOWN-072, TOWN-078, WORLD-042, WORLD-048, WORLD-049
# Compliance IDs: SOC-026, SOC-027, SOC-028, SOC-029, SOC-030, SOC-031, SOC-032, SOC-033, SOC-034, SOC-035, SOC-036, SOC-037, SOC-038, SOC-039, SOC-040, SOC-041, TOWN-072, TOWN-078
# The regional density top-up (SPAWN_POOLS, BASE_MONSTER_DENSITY, SpawnConfig) was removed: divergence 2.122 (D67/D70). What stays are the tier
# multipliers and the distance zones that the generator and region code read.
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
    # World boss / Lair-occupant tier (TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY).
    # First-pass numbers, chosen to continue tier 1-4's own ~1.4-1.6x growth curve and
    # recorded as provisional in docs/plans/deferred_tuning_decisions_register.md D-05 --
    # not a tuned balance answer, just enough to make a "world boss" meaningfully harder
    # than an ordinary tier-4 monster instead of silently falling back to tier-1 stats.
    5: DifficultyMultipliers(hp=6.5, atk=4.5, def_stat=3.5, xp=8.0, gold=6.5, level_min=14, level_max=22),
}

# Mapping distance from town center to difficulty tier
DIFFICULTY_ZONES = (
    (80, 1),
    (150, 2),
    (220, 3),
    (999, 4),
)
