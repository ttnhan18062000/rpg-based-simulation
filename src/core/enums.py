"""Enumerations."""
from __future__ import annotations
from enum import IntEnum, unique

@unique
class ActionType(IntEnum):
    REST = 0; MOVE = 1; ATTACK = 2; USE_ITEM = 3; LOOT = 4; HARVEST = 5; USE_SKILL = 6; REPAIR = 7

@unique
class AIState(IntEnum):
    IDLE = 0; WANDER = 1; HUNT = 2; COMBAT = 3; FLEE = 4; RETURN_TO_TOWN = 5; RESTING_IN_TOWN = 6; RETURN_TO_CAMP = 7; GUARD_CAMP = 8; LOOTING = 9; ALERT = 10; VISIT_SHOP = 11; VISIT_BLACKSMITH = 12; VISIT_GUILD = 13; HARVESTING = 14; VISIT_CLASS_HALL = 15; VISIT_INN = 16; VISIT_HOME = 17

@unique
class Direction(IntEnum): NORTH = 0; EAST = 1; SOUTH = 2; WEST = 3

@unique
class Domain(IntEnum): COMBAT = 0; LOOT = 1; AI_DECISION = 2; SPAWN = 3; WEATHER = 4; LEVEL_UP = 5; ITEM = 6; HARVEST = 7; MAP_GEN = 8; CALAMITY = 9

@unique
class Material(IntEnum): FLOOR = 0; WALL = 1; WATER = 2; TOWN = 3; CAMP = 4; SANCTUARY = 5; FOREST = 6; DESERT = 7; SWAMP = 8; MOUNTAIN = 9; ROAD = 10; BRIDGE = 11; RUINS = 12; DUNGEON_ENTRANCE = 13; LAVA = 14; GRASSLAND = 15; SNOW = 16; JUNGLE = 17; SHALLOW_WATER = 18; FARMLAND = 19; CAVE = 20; VOLCANIC = 21; GRAVEYARD = 22

@unique
class ItemType(IntEnum): WEAPON = 0; ARMOR = 1; ACCESSORY = 2; CONSUMABLE = 3; MATERIAL = 4

@unique
class Rarity(IntEnum): COMMON = 0; UNCOMMON = 1; RARE = 2; EPIC = 3; LEGENDARY = 4

@unique
class EntityRole(IntEnum): HERO = 0; MOB = 1; NPC = 2; WORLD_BOSS = 3

@unique
class EnemyTier(IntEnum):
    """Enemy difficulty tiers — affects stats, behavior, and loot."""

    BASIC = 0
    SCOUT = 1
    WARRIOR = 2
    ELITE = 3

@unique
class HeroClass(IntEnum):
    """Available classes for hero entities."""
    WARRIOR = 0
    RANGER = 1
    MAGE = 2
    ROGUE = 3
    CHAMPION = 4
    ELITE_ARCHER = 5
    ARCHMAGE = 6
    ASSASSIN = 7

@unique
class Faction(IntEnum):
    """World factions for alignment and aggression."""
    HERO_GUILD = 0
    GOBLIN_TRIBE = 1
    WOLF_PACK = 2
    BANDIT_GANG = 3
    UNDEAD_HORDE = 4
    ORC_CLAN = 5
    GOBLIN_HORDE = 6

@unique
class DamageType(IntEnum): PHYSICAL = 0; MAGICAL = 1

@unique
class Element(IntEnum): NONE = 0; FIRE = 1; ICE = 2; LIGHTNING = 3; DARK = 4; HOLY = 5

@unique
class TraitType(IntEnum): AGGRESSIVE = 0; CAUTIOUS = 1; BRAVE = 2; COWARDLY = 3; BLOODTHIRSTY = 4; GREEDY = 5; GENEROUS = 6; CHARISMATIC = 7; LONER = 8; DILIGENT = 9; LAZY = 10; CURIOUS = 11; BERSERKER = 12; TACTICAL = 13; RESILIENT = 14; ARCANE_GIFTED = 15; SPIRIT_TOUCHED = 16; ELEMENTALIST = 17; KEEN_EYED = 18; OBLIVIOUS = 19

@unique
class VeterancyRank(IntEnum): GREEN = 0; BLOODED = 1; VETERAN = 2; ELITE = 3; LEGEND = 4

from dataclasses import dataclass
@dataclass(frozen=True)
class RaceProfile: train_rate: float; level_cap: int; evolves: bool

RACE_PROFILES = {"hero": RaceProfile(1.0, 30, False), "goblin": RaceProfile(1.3, 12, True)} # truncated
