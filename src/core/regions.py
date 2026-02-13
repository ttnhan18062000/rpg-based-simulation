"""Region & Location data model for the world map (epic-15).

Regions are large named areas with a terrain type, difficulty tier, and
sub-locations.  Locations are points of interest within a region (camps,
groves, ruins, dungeons, shrines, boss arenas).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.core.enums import Material
from src.core.models import Vector2

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Location types
# ---------------------------------------------------------------------------

LOCATION_TYPES = (
    "enemy_camp",
    "resource_grove",
    "ruins",
    "dungeon_entrance",
    "shrine",
    "boss_arena",
)


@dataclass(slots=True)
class Location:
    """A point of interest within a region."""

    location_id: str
    name: str
    location_type: str          # one of LOCATION_TYPES
    pos: Vector2
    region_id: str


@dataclass(slots=True)
class Region:
    """A named area of the world map."""

    region_id: str
    name: str
    terrain: Material           # FOREST, DESERT, SWAMP, MOUNTAIN
    center: Vector2
    radius: int
    difficulty: int             # 1–4
    locations: list[Location] = field(default_factory=list)

    def contains(self, pos: Vector2) -> bool:
        """Rough bounding check (Manhattan distance).

        For authoritative Voronoi ownership use ``find_region_at()``.
        """
        return self.center.manhattan(pos) <= self.radius

    def copy(self) -> Region:
        return Region(
            region_id=self.region_id,
            name=self.name,
            terrain=self.terrain,
            center=Vector2(self.center.x, self.center.y),
            radius=self.radius,
            difficulty=self.difficulty,
            locations=[Location(
                location_id=loc.location_id,
                name=loc.name,
                location_type=loc.location_type,
                pos=Vector2(loc.pos.x, loc.pos.y),
                region_id=loc.region_id,
            ) for loc in self.locations],
        )


# ---------------------------------------------------------------------------
# Region name tables (per terrain)
# ---------------------------------------------------------------------------

REGION_NAMES: dict[int, list[str]] = {
    Material.FOREST: [
        "Whispering Woods",
        "Verdant Hollow",
        "Thornwood",
        "Mossy Glen",
        "Eldergrove",
        "Shadeleaf Thicket",
    ],
    Material.DESERT: [
        "Scorched Wastes",
        "Dustwind Basin",
        "Sunfire Plateau",
        "Sandstone Reach",
        "Dry Gulch",
        "Ember Flats",
    ],
    Material.SWAMP: [
        "Rotmire Bog",
        "Gloomfen",
        "Witchwater Marsh",
        "Deadtide Swamp",
        "Murkhollow",
        "Venom Pools",
    ],
    Material.MOUNTAIN: [
        "Ironpeak Ridge",
        "Stormcrag Heights",
        "Frostbreak Summit",
        "Ashvein Slopes",
        "Granite Pass",
        "Windshear Cliffs",
    ],
}

# Name index counters (reset per world build)
_name_counters: dict[int, int] = {}


def pick_region_name(terrain: Material) -> str:
    """Return the next unique name for a terrain type."""
    key = int(terrain)
    idx = _name_counters.get(key, 0)
    names = REGION_NAMES.get(key, ["Unknown Region"])
    name = names[idx % len(names)]
    _name_counters[key] = idx + 1
    return name


def reset_name_counters() -> None:
    """Reset name counters (call before each world build)."""
    _name_counters.clear()


# ---------------------------------------------------------------------------
# Location name templates (per location type)
# ---------------------------------------------------------------------------

LOCATION_NAME_TEMPLATES: dict[str, list[str]] = {
    "enemy_camp": [
        "{race} Outpost",
        "{race} Encampment",
        "{race} Hideout",
        "{race} Stockade",
        "{race} Watchtower",
    ],
    "resource_grove": [
        "Harvest Clearing",
        "Gatherer's Nook",
        "Rich Vein",
        "Abundant Patch",
        "Forager's Dell",
    ],
    "ruins": [
        "Crumbling Tower",
        "Forgotten Shrine",
        "Ancient Pillars",
        "Lost Archway",
        "Broken Monument",
    ],
    "dungeon_entrance": [
        "Dark Cavern",
        "Sunken Passage",
        "Sealed Gate",
        "Obsidian Rift",
    ],
    "shrine": [
        "Shrine of Vigor",
        "Blessed Stone",
        "Wayward Altar",
        "Pilgrim's Rest",
    ],
    "boss_arena": [
        "The Arena",
        "Champion's Ring",
        "Proving Ground",
        "Warlord's Domain",
    ],
}

# Race labels for location names
TERRAIN_RACE_LABEL: dict[int, str] = {
    Material.FOREST: "Wolf",
    Material.DESERT: "Bandit",
    Material.SWAMP: "Undead",
    Material.MOUNTAIN: "Orc",
}


# ---------------------------------------------------------------------------
# Difficulty multiplier tables
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DifficultyMultipliers:
    """Stat multipliers for a given difficulty tier."""
    hp: float
    atk: float
    def_: float
    xp: float
    gold: float
    level_min: int
    level_max: int


DIFFICULTY_TIERS: dict[int, DifficultyMultipliers] = {
    1: DifficultyMultipliers(hp=1.0, atk=1.0, def_=1.0, xp=1.0, gold=1.0, level_min=1, level_max=3),
    2: DifficultyMultipliers(hp=1.5, atk=1.3, def_=1.2, xp=1.5, gold=1.5, level_min=3, level_max=6),
    3: DifficultyMultipliers(hp=2.5, atk=2.0, def_=1.8, xp=3.0, gold=2.5, level_min=5, level_max=10),
    4: DifficultyMultipliers(hp=4.0, atk=3.0, def_=2.5, xp=5.0, gold=4.0, level_min=8, level_max=15),
}


def find_region_at(pos: Vector2, regions: list[Region] | tuple[Region, ...]) -> Region | None:
    """Return the region whose center is nearest to *pos* (Voronoi ownership).

    Returns ``None`` if *regions* is empty.
    """
    best: Region | None = None
    best_dist = float("inf")
    for r in regions:
        d = r.center.manhattan(pos)
        if d < best_dist:
            best_dist = d
            best = r
    return best


def difficulty_for_distance(distance: float, zone_boundaries: list[tuple[int, int]]) -> int:
    """Determine difficulty tier based on distance from town center.

    zone_boundaries is a list of (max_distance, tier) sorted ascending.
    """
    for max_dist, tier in zone_boundaries:
        if distance <= max_dist:
            return tier
    # Beyond all boundaries → highest tier
    return zone_boundaries[-1][1] if zone_boundaries else 1
