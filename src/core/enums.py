"""Enumerations used throughout the engine."""

from __future__ import annotations

from enum import IntEnum, unique


@unique
class ActionType(IntEnum):
    """Types of actions an entity can propose."""

    REST = 0
    MOVE = 1
    ATTACK = 2
    USE_ITEM = 3
    LOOT = 4
    HARVEST = 5
    USE_SKILL = 6


@unique
class AIState(IntEnum):
    """Finite-state-machine states for entity AI."""

    IDLE = 0
    WANDER = 1
    HUNT = 2
    COMBAT = 3
    FLEE = 4
    RETURN_TO_TOWN = 5
    RESTING_IN_TOWN = 6
    RETURN_TO_CAMP = 7
    GUARD_CAMP = 8
    LOOTING = 9
    ALERT = 10          # Responding to territory intrusion
    VISIT_SHOP = 11     # Going to / interacting with shop
    VISIT_BLACKSMITH = 12  # Going to / interacting with blacksmith
    VISIT_GUILD = 13    # Going to / interacting with guild hall
    HARVESTING = 14     # Channeling resource harvest
    VISIT_CLASS_HALL = 15  # Going to / interacting with class building
    VISIT_INN = 16         # Going to / interacting with inn


@unique
class Direction(IntEnum):
    """Cardinal movement directions."""

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


@unique
class Domain(IntEnum):
    """RNG domains for deterministic randomness isolation."""

    COMBAT = 0
    LOOT = 1
    AI_DECISION = 2
    SPAWN = 3
    WEATHER = 4
    LEVEL_UP = 5
    ITEM = 6
    HARVEST = 7
    MAP_GEN = 8


@unique
class Material(IntEnum):
    """Tile materials on the grid."""

    FLOOR = 0
    WALL = 1
    WATER = 2
    TOWN = 3
    CAMP = 4
    SANCTUARY = 5
    FOREST = 6
    DESERT = 7
    SWAMP = 8
    MOUNTAIN = 9
    ROAD = 10
    BRIDGE = 11
    RUINS = 12
    DUNGEON_ENTRANCE = 13
    LAVA = 14


@unique
class ItemType(IntEnum):
    """Item categories."""

    WEAPON = 0
    ARMOR = 1
    ACCESSORY = 2
    CONSUMABLE = 3
    MATERIAL = 4


@unique
class Rarity(IntEnum):
    """Item rarity tiers."""

    COMMON = 0
    UNCOMMON = 1
    RARE = 2


@unique
class EnemyTier(IntEnum):
    """Enemy difficulty tiers — affects stats, behavior, and loot."""

    BASIC = 0
    SCOUT = 1
    WARRIOR = 2
    ELITE = 3
