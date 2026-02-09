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
    VISIT_HOME = 17        # Going to / interacting with home storage


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


@unique
class DamageType(IntEnum):
    """Core damage categories for attacks and skills."""

    PHYSICAL = 0
    MAGICAL = 1


@unique
class Element(IntEnum):
    """Elemental tags applied to skills/weapons for vulnerability modifiers."""

    NONE = 0
    FIRE = 1
    ICE = 2
    LIGHTNING = 3
    DARK = 4
    HOLY = 5


@unique
class TraitType(IntEnum):
    """Discrete personality traits assigned to entities (Rimworld-style).

    Each entity gets 2-4 traits at spawn.  Traits modify utility scores
    in the goal-evaluation layer and can gate special behaviours.
    """

    # Combat disposition
    AGGRESSIVE = 0      # Higher hunt/combat utility, lower flee threshold
    CAUTIOUS = 1        # Higher flee/retreat utility, prefers safe routes
    BRAVE = 2           # Resists fleeing even at low HP, bonus morale
    COWARDLY = 3        # Flees earlier, avoids strong enemies
    BLOODTHIRSTY = 4    # Seeks combat even when not necessary, bonus crit

    # Social / economic
    GREEDY = 5          # Prioritises loot/gold, hoards items
    GENEROUS = 6        # Shares loot, lower sell threshold
    CHARISMATIC = 7     # Better trade prices, higher recruitment chance
    LONER = 8           # Avoids allies, prefers solo exploration

    # Work ethic
    DILIGENT = 9        # Faster interaction/harvest, lower rest need
    LAZY = 10           # Slower interaction, higher rest utility
    CURIOUS = 11        # Explores unknown areas, higher frontier utility

    # Combat style
    BERSERKER = 12      # Bonus damage at low HP, ignores some defense
    TACTICAL = 13       # Prefers skills over basic attacks, better positioning
    RESILIENT = 14      # Faster HP regen, higher effective VIT

    # Magical affinity
    ARCANE_GIFTED = 15  # Bonus MATK, higher skill utility
    SPIRIT_TOUCHED = 16 # Bonus MDEF, resist dark/holy elements
    ELEMENTALIST = 17   # Bonus elemental damage, varied element preference

    # Perception / awareness
    KEEN_EYED = 18      # Bonus vision range, detects hidden enemies
    OBLIVIOUS = 19      # Reduced vision, but higher focus on current task
