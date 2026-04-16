"""Enumerations."""
from __future__ import annotations
from enum import IntEnum, unique

@unique
class ActionType(IntEnum):
    REST = 0; MOVE = 1; ATTACK = 2; USE_ITEM = 3; LOOT = 4; HARVEST = 5; USE_SKILL = 6; REPAIR = 7; SLEEP = 8; EAT = 9

@unique
class SkillType(IntEnum):
    """Skill categories."""
    ACTIVE = 0
    PASSIVE = 1

@unique
class SkillTarget(IntEnum):
    """Who a skill targets."""
    SELF = 0
    SINGLE_ENEMY = 1
    AREA_ENEMIES = 2
    SINGLE_ALLY = 3
    AREA_ALLIES = 4

@unique
class AIState(IntEnum):
    IDLE = 0; WANDER = 1; HUNT = 2; COMBAT = 3; FLEE = 4; RETURN_TO_TOWN = 5; RESTING_IN_TOWN = 6; RETURN_TO_CAMP = 7; GUARD_CAMP = 8; LOOTING = 9; ALERT = 10; VISIT_SHOP = 11; VISIT_BLACKSMITH = 12; VISIT_GUILD = 13; HARVESTING = 14; VISIT_CLASS_HALL = 15; VISIT_INN = 16; VISIT_HOME = 17; RAID = 18; EXHAUSTED = 19; RECOVER_CORPSE = 20; SLEEPING = 21; EATING = 22; INVESTIGATING = 23

@unique
class Direction(IntEnum): NORTH = 0; EAST = 1; SOUTH = 2; WEST = 3

@unique
class Domain(IntEnum): COMBAT = 0; LOOT = 1; AI_DECISION = 2; SPAWN = 3; WEATHER = 4; LEVEL_UP = 5; ITEM = 6; HARVEST = 7; MAP_GEN = 8; CALAMITY = 9; SOCIAL = 10

@unique
class Material(IntEnum): FLOOR = 0; WALL = 1; WATER = 2; TOWN = 3; CAMP = 4; SANCTUARY = 5; FOREST = 6; DESERT = 7; SWAMP = 8; MOUNTAIN = 9; ROAD = 10; BRIDGE = 11; RUINS = 12; DUNGEON_ENTRANCE = 13; LAVA = 14; GRASSLAND = 15; SNOW = 16; JUNGLE = 17; SHALLOW_WATER = 18; FARMLAND = 19; CAVE = 20; VOLCANIC = 21; GRAVEYARD = 22

@unique
class ItemType(IntEnum): WEAPON = 0; ARMOR = 1; ACCESSORY = 2; CONSUMABLE = 3; MATERIAL = 4

@unique
class Rarity(IntEnum): COMMON = 0; UNCOMMON = 1; RARE = 2; EPIC = 3; LEGENDARY = 4

@unique
class EntityRole(IntEnum): HERO = 0; MOB = 1; NPC = 2; WORLD_BOSS = 3; STRONGHOLD = 4

@unique
class LifeRole(IntEnum):
    """Lived-world roles separate from combat class. [PHASE 3]"""
    NONE = 0; GUARD = 1; SCOUT = 2; RAIDER = 3; CRAFTER = 4; HOUSEHOLDER = 5; SENTRY = 6; HEALER = 7; APPRENTICE = 8; HERO = 9; MERCHANT = 10; BLACKSMITH = 11

@unique
class GroupKind(IntEnum):
    """Small-group coordination types. [PHASE 3]"""
    SOCIAL_CLIQUE = 0; PATROL = 1; RAID_PACK = 2; ESCORT = 3; HOUSEHOLD = 4; PARTY = 5

@unique
class AttachmentKind(IntEnum):
    """Types of location-based sentiment. [PHASE 3]"""
    HOME = 0; WORKPLACE = 1; TRAINING_GROUND = 2; MARKET = 3; FAVORITE_SPOT = 4; SHRINE = 5

@unique
class ContractKind(IntEnum):
    """Categories for negotiated social agreements. [PHASE 4]"""
    EXPEDITION = 0 # Objective-driven travel
    ESCORT = 1 # Protection-driven movement
    MILITIA = 2 # Collective defense
    MERCENARY = 3 # Paid combat/service
    REVENGE_PACT = 4 # Vendetta-driven cooperation

@unique
class OfferStatus(IntEnum):
    """Lifecycle of a recruitment or social proposal. [PHASE 4]"""
    PENDING = 0
    ACCEPTED = 1
    DECLINED = 2
    EXPIRED = 3
    CANCELLED = 4
    COUNTERED = 5

@unique
class StrategicStatus(IntEnum):
    """Lifecycle status for projects and objectives."""
    ACTIVE = 0
    SUSPENDED = 1
    RESOLVED = 2
    ABANDONED = 3

@unique
class DirectiveKind(IntEnum):
    """Categories for enduring orientations."""
    IDEOLOGICAL = 0
    PROFESSIONAL = 1
    FACTIONAL = 2
    PERSONAL = 3

@unique
class ProjectKind(IntEnum):
    """Broad categories for strategic pursuits."""
    QUEST = 0
    EXPLORATION = 1
    SOCIAL = 2
    INVESTIGATION = 3
    DEVELOPMENT = 4

@unique
class ObjectiveKind(IntEnum):
    """Specific types of strategic sub-tasks."""
    VISIT = 0
    KILL = 1
    COLLECT = 2
    INTERACT = 3
    WAIT = 4
    INVESTIGATE = 5
    SCOUT = 6
    TRAIN = 7

@unique
class ConcernKind(IntEnum):
    """Immediate strategic interrupts or priorities."""
    THREAT = 0
    OPPORTUNITY = 1
    OBLIGATION = 2

@unique
class LeadKind(IntEnum):
    """Types of uncertain strategic clues."""
    LOCATION = 0
    PERSON = 1
    OBJECT = 2
    EVENT = 3

@unique
class BlockerKind(IntEnum):
    """Reasons why a project or objective cannot proceed."""
    KNOWLEDGE = 0; CAPABILITY = 1; ACCESS = 2; SOCIAL = 3; MATERIAL = 4; TIMING = 5; OBLIGATION = 6; ENVIRONMENTAL = 7; CONFIDENCE = 8

@unique
class EnemyTier(IntEnum):
    """Enemy difficulty tiers — affects stats, behavior, and loot."""

    BASIC = 0
    SCOUT = 1
    WARRIOR = 2
    ELITE = 3

@unique
class HeroClass(IntEnum):
    """Available classes for hero entities and mob archetypes."""
    NONE = 0
    # --- Primary Hero Classes ---
    WARRIOR = 1
    RANGER = 2
    MAGE = 3
    ROGUE = 4
    # --- Breakthrough Classes (Tier 2) ---
    CHAMPION = 5
    SHARPSHOOTER = 6
    ARCHMAGE = 7
    ASSASSIN = 8
    # --- Transcendence Classes (Tier 3) ---
    WARLORD = 9
    STORM_CALLER = 10
    GHOST_STALKER = 11
    NIGHTSHADE = 12
    # --- Mob Archetypes ---
    BRUTE = 20
    SCOUT = 21
    CASTER = 22
    TANK = 23
    BEAST = 24

class Faction(IntEnum):
    """World factions for alignment, territory, and aggression."""
    HERO_GUILD = 0
    GOBLIN_HORDE = 1
    WOLF_PACK = 2
    BANDIT_CLAN = 3
    UNDEAD = 4
    ORC_TRIBE = 5
    CENTAUR_HERD = 6
    FROST_KIN = 7
    LIZARDFOLK = 8
    DEMON_HORDE = 9
    # Legacy aliases (to be removed in future refactor)
    GOBLIN_TRIBE = 1
    BANDIT_GANG = 3
    UNDEAD_HORDE = 4
    ORC_CLAN = 5

@unique
class DamageType(IntEnum): PHYSICAL = 0; MAGICAL = 1

@unique
class Element(IntEnum): NONE = 0; FIRE = 1; ICE = 2; LIGHTNING = 3; DARK = 4; HOLY = 5

@unique
class TraitType(IntEnum): AGGRESSIVE = 0; CAUTIOUS = 1; BRAVE = 2; COWARDLY = 3; BLOODTHIRSTY = 4; GREEDY = 5; GENEROUS = 6; CHARISMATIC = 7; LONER = 8; DILIGENT = 9; LAZY = 10; CURIOUS = 11; BERSERKER = 12; TACTICAL = 13; RESILIENT = 14; ARCANE_GIFTED = 15; SPIRIT_TOUCHED = 16; ELEMENTALIST = 17; KEEN_EYED = 18; OBLIVIOUS = 19

@unique
class VeterancyRank(IntEnum): GREEN = 0; BLOODED = 1; VETERAN = 2; ELITE = 3; LEGEND = 4

@unique
class GoalType(IntEnum):
    """Specific AI goals for utility selection."""
    COMBAT = 0
    FLEE = 1
    EXPLORE = 2
    LOOT = 3
    TRADE = 4
    REST = 5
    CRAFT = 6
    SOCIAL = 7
    GUARD = 8
    CORPSE_RUN = 9
    SLEEP = 10
    EAT = 11
    INVESTIGATE = 12

@unique
class EmotionType(IntEnum):
    """Emotional dimensions for AI appraisal."""
    BRAVERY = 0
    PANIC = 1
    STUCK = 2
    DREAD = 3
    JOY = 4

@unique
class Archetype(IntEnum):
    """Static behavioral templates for entities."""
    BALANCED = 0
    CAUTIOUS_OPPORTUNIST = 1
    GLORY_SEEKER = 2
    HONORABLE_DEFENDER = 3
    GREEDY_SCAVENGER = 4
    BLOODTHIRSTY_SLAYER = 5
    COWARDLY_SURVIVOR = 6

@unique
class PersonalMotiveType(IntEnum):
    """Broad categories for AI long-term motives. [STAGE 1]"""
    BUILD_WEALTH = 0
    SEEK_SAFETY = 1
    PROVE_STRENGTH = 2
    EXPLORE_WORLD = 3
    SOCIAL_STATUS = 4

@unique
class TurningPointKind(IntEnum):
    """Categories for life-defining moments. [PHASE 2]"""
    NEAR_DEATH = 0
    ALLY_DIED = 1
    AVENGED_ALLY = 2
    BETRAYAL = 3
    RESCUE = 4
    DISGRACE = 5
    REVENGE = 6
    HOME_LOST = 7
    BOSS_ENCOUNTER = 8
    FIRST_KILL = 9

@unique
class InterpretedLifeEventKind(IntEnum):
    """Semantic tags for socially meaningful event interpretations. [PHASE 2]"""
    NEAR_DEATH = 0
    ALLY_DIED_NEARBY = 1
    AVENGED_ALLY = 2
    FLED_FROM_THREAT = 3
    HELD_POSITION = 4
    LOOTED_DURING_DANGER = 5
    FIRST_BOSS_ENCOUNTER = 6
    BETRAYAL = 7
    FIRST_KILL = 8
    SLAY_FOE = 9
    
    # Phase 5 Expansion [Task 8]
    RESCUE_PERFORMED = 10
    RESCUED_BY_OTHER = 11
    DEFENSE_FAILED = 12
    HOME_DAMAGED = 13
    CONTRACT_HONORED_PUBLICLY = 14
    CONTRACT_BETRAYED_PUBLICLY = 15
    REPEATED_FAILED_ATTEMPT = 16
    PUBLIC_DISGRACE = 17
    WARNING_IGNORED = 18
    TRESPASS = 19
    BODY_RECOVERED = 20
    BODY_ABANDONED = 21
    HOMECOMING = 22
    INTEL_CONFIRMED = 23
    INTEL_REFUTED = 24

from typing import Annotated
from pydantic import BeforeValidator, PlainSerializer

def _parse_enum(cls):
    def _parse(v):
        if isinstance(v, cls): return v
        if isinstance(v, int):
            try: return cls(v)
            except ValueError: return v
        if isinstance(v, str):
            try: return cls[v.upper()]
            except (KeyError, ValueError): pass
        return v
    return _parse

FactionSer = Annotated[Faction, BeforeValidator(_parse_enum(Faction)), PlainSerializer(lambda v: Faction(v).name.lower(), return_type=str)]
HeroClassSer = Annotated[HeroClass, BeforeValidator(_parse_enum(HeroClass)), PlainSerializer(lambda v: HeroClass(v).name.lower(), return_type=str)]
EnemyTierSer = Annotated[EnemyTier, BeforeValidator(_parse_enum(EnemyTier)), PlainSerializer(lambda v: EnemyTier(v).name.lower(), return_type=str)]
ItemTypeSer = Annotated[ItemType, BeforeValidator(_parse_enum(ItemType)), PlainSerializer(lambda v: ItemType(v).name.lower(), return_type=str)]
RaritySer = Annotated[Rarity, BeforeValidator(_parse_enum(Rarity)), PlainSerializer(lambda v: Rarity(v).name.lower(), return_type=str)]
SkillTypeSer = Annotated[SkillType, BeforeValidator(_parse_enum(SkillType)), PlainSerializer(lambda v: SkillType(v).name.lower(), return_type=str)]
SkillTargetSer = Annotated[SkillTarget, BeforeValidator(_parse_enum(SkillTarget)), PlainSerializer(lambda v: SkillTarget(v).name.lower(), return_type=str)]
DamageTypeSer = Annotated[int, BeforeValidator(_parse_enum(DamageType)), PlainSerializer(lambda v: DamageType(v).name.lower(), return_type=str)]
ElementSer = Annotated[int, BeforeValidator(_parse_enum(Element)), PlainSerializer(lambda v: Element(v).name.lower(), return_type=str)]
VetryRankSer = Annotated[int, BeforeValidator(_parse_enum(VeterancyRank)), PlainSerializer(lambda v: VeterancyRank(v).name.lower(), return_type=str)] # Standardizing formatting
LifeRoleSer = Annotated[LifeRole, BeforeValidator(_parse_enum(LifeRole)), PlainSerializer(lambda v: LifeRole(v).name.lower(), return_type=str)]
GroupKindSer = Annotated[GroupKind, BeforeValidator(_parse_enum(GroupKind)), PlainSerializer(lambda v: GroupKind(v).name.lower(), return_type=str)]
AttachmentKindSer = Annotated[AttachmentKind, BeforeValidator(_parse_enum(AttachmentKind)), PlainSerializer(lambda v: AttachmentKind(v).name.lower(), return_type=str)]
ContractKindSer = Annotated[ContractKind, BeforeValidator(_parse_enum(ContractKind)), PlainSerializer(lambda v: ContractKind(v).name.lower(), return_type=str)]
OfferStatusSer = Annotated[OfferStatus, BeforeValidator(_parse_enum(OfferStatus)), PlainSerializer(lambda v: OfferStatus(v).name.lower(), return_type=str)]
ArchetypeSer = Annotated[Archetype, BeforeValidator(_parse_enum(Archetype)), PlainSerializer(lambda v: Archetype(v).name.lower(), return_type=str)]
StrategicStatusSer = Annotated[StrategicStatus, BeforeValidator(_parse_enum(StrategicStatus)), PlainSerializer(lambda v: StrategicStatus(v).name.lower(), return_type=str)]
DirectiveKindSer = Annotated[DirectiveKind, BeforeValidator(_parse_enum(DirectiveKind)), PlainSerializer(lambda v: DirectiveKind(v).name.lower(), return_type=str)]
ProjectKindSer = Annotated[ProjectKind, BeforeValidator(_parse_enum(ProjectKind)), PlainSerializer(lambda v: ProjectKind(v).name.lower(), return_type=str)]
ObjectiveKindSer = Annotated[ObjectiveKind, BeforeValidator(_parse_enum(ObjectiveKind)), PlainSerializer(lambda v: ObjectiveKind(v).name.lower(), return_type=str)]
ConcernKindSer = Annotated[ConcernKind, BeforeValidator(_parse_enum(ConcernKind)), PlainSerializer(lambda v: ConcernKind(v).name.lower(), return_type=str)]
LeadKindSer = Annotated[LeadKind, BeforeValidator(_parse_enum(LeadKind)), PlainSerializer(lambda v: LeadKind(v).name.lower(), return_type=str)]
BlockerKindSer = Annotated[BlockerKind, BeforeValidator(_parse_enum(BlockerKind)), PlainSerializer(lambda v: BlockerKind(v).name.lower(), return_type=str)]

from dataclasses import dataclass, field
@dataclass(frozen=True)
class RaceProfile:
    train_rate: float
    level_cap: int
    evolves: bool
    starting_skills: list[str] = field(default_factory=list)
    factions: list[FactionSer] = field(default_factory=list)
    stat_mods: list[float] = field(default_factory=lambda: [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

RACE_PROFILES: dict[str, RaceProfile] = {
    "hero": RaceProfile(1.0, 30, False),
    "goblin": RaceProfile(1.3, 12, True),
    "goblin_scout": RaceProfile(1.3, 12, True),
    "goblin_warrior": RaceProfile(1.3, 12, True),
    "goblin_chief": RaceProfile(1.3, 12, False),
    "wolf": RaceProfile(0.7, 8, True),
    "dire_wolf": RaceProfile(0.7, 8, True),
    "alpha_wolf": RaceProfile(0.7, 8, False),
    "bandit": RaceProfile(1.0, 15, True),
    "bandit_archer": RaceProfile(1.0, 15, True),
    "bandit_chief": RaceProfile(1.0, 15, False),
    "undead": RaceProfile(0.0, 1, False),  # Cannot level up
    "skeleton": RaceProfile(0.0, 1, False),
    "skeleton_mage": RaceProfile(0.0, 1, False),
    "zombie": RaceProfile(0.0, 1, False),
    "lich": RaceProfile(0.0, 1, False),
    "orc": RaceProfile(0.6, 15, True),
    "orc_warrior": RaceProfile(0.6, 15, True),
    "orc_warlord": RaceProfile(0.6, 15, False),
}
