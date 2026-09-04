# Compliance IDs: AUTH-003
# Compliance IDs: TOWN-003
from enum import Enum, IntEnum, unique

@unique
class EntityRole(IntEnum):
    HERO = 0
    SHOPKEEPER = 1
    MONSTER = 2
    CITIZEN = 3
    WORKER = 4
    GUARD = 5

class DiplomaticState(str, Enum):
    """Typed diplomatic relationship state between two factions (E53Ba)."""
    NEUTRAL = "NEUTRAL"
    TENSE = "TENSE"
    HOSTILE = "HOSTILE"
    WAR = "WAR"
    ALLIED = "ALLIED"
    VASSAL = "VASSAL"

@unique
class Faction(IntEnum):
    HERO_GUILD = 0
    MONSTER_HORDE = 1
    TOWN_COUNCIL = 2
    NEUTRAL = 3

@unique
class Direction(IntEnum):
    """Cardinal directions for grid movement."""
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

@unique
class MovementIntention(IntEnum):
    """Explicit purpose of the current movement."""
    NONE = 0
    PURSUE = 1
    RETREAT = 2
    HOLD = 3
    REPOSITION = 4
    INTERCEPT = 5
    GUARD = 6
    WANDER = 7
    REGROUP = 8
@unique
class ActionType(IntEnum):
    """Authoritative action categories."""
    REST = 0
    MOVE = 1
    INTERACT = 2
    ATTACK = 3
    SKILL = 4

@unique
class ActionStyle(IntEnum):
    """Tactical bias for action selection."""
    BALANCED = 0
    AGGRESSIVE = 1
    EVASIVE = 2

class ReasonCode(str, Enum):
    """
    Authoritative reason codes for all state changes.
    Logic ID: TOWN-003 (Structured authoritative reason models)
    Stable identifiers for simulation decision drivers.
    """
    # General
    LEGAL = "LEGAL"
    
    # Movement
    ADVANCING = "advancing"
    OCCUPANCY_VIOLATION = "occupancy_violation"
    PATH_NOT_FOUND = "path_not_found"
    BUILDING_OBSTRUCTION = "BUILDING_OBSTRUCTION"
    YIELDING = "yielding"
    SIDESTEPPING = "sidestepping"
    WAITING = "waiting"
    CONGESTION = "congestion"
    PATH_EXHAUSTED = "path_exhausted"
    TARGET_REACHED = "target_reached"
    
    # Movement / position swap
    POSITION_SWAP = "position_swap"
    POSITION_SWAP_ACCEPTED = "position_swap_accepted"
    POSITION_SWAP_REFUSED = "position_swap_refused"
    
    # Combat/Interaction
    OUT_OF_RANGE = "OUT_OF_RANGE"
    TARGET_INVALID = "TARGET_INVALID"
    ACTION_EXHAUSTION = "exhaustion"
    INTERACTION_REJECTED = "interaction_rejected"
    INTERACTION_INTERRUPTED = "interaction_interrupted"
    ENGAGED = "engaged"
    
    # Combat Legality Matrix (Hardening)
    ATTACKER_INCAPACITATED = "ATTACKER_INCAPACITATED"
    TARGET_INCAPACITATED = "TARGET_INCAPACITATED"
    LOS_OBSTRUCTED = "LOS_OBSTRUCTED"
    FRIENDLY_FIRE_ILLEGAL = "FRIENDLY_FIRE_ILLEGAL"
    INSUFFICIENT_READINESS = "INSUFFICIENT_READINESS"
    READINESS_NOT_READY = "READINESS_NOT_READY"
    SELF_ATTACK_ILLEGAL = "SELF_ATTACK_ILLEGAL"
    SKILL_ON_COOLDOWN = "SKILL_ON_COOLDOWN"
    SKILL_NOT_LEARNED = "SKILL_NOT_LEARNED"
    REGIONAL_SUPPRESSION = "REGIONAL_SUPPRESSION"
    ATTACKER_STATUS_BLOCKED = "ATTACKER_STATUS_BLOCKED"
    
    # Tactical AI
    NO_TARGET = "no_target"
    LOW_HP_RETREAT = "low_hp_retreat"
    KITING = "kiting"
    MAINTAIN_DISTANCE = "maintain_distance"
    ALLY_SPACING = "ally_spacing"
    CLOSING_RANGE = "closing_range"
    GROUP_PRIORITY = "group_priority"
    
    # Routine / Biological
    HUNGER = "hunger"
    SLEEPY = "sleepy"
    FORCED_REST = "forced_rest"
    
    # Strategic / Capacity
    INSUFFICIENT_CAPACITY = "INSUFFICIENT_CAPACITY"
    INVENTORY_FULL_DROPPED = "inventory_full_dropped"
    BUDGET_EXHAUSTED = "budget_exhausted"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    LIQUIDITY_EXHAUSTED = "liquidity_exhausted"
    
    # Conservation / Transaction
    TARGET_LOCKED = "target_locked"
    IDEMPOTENCY_VIOLATION = "idempotency_violation"
    SOURCE_DEPLETED = "SOURCE_DEPLETED"
    INSUFFICIENT_GOLD = "INSUFFICIENT_GOLD"
    INSUFFICIENT_RESOURCES = "INSUFFICIENT_RESOURCES"
    PRICE_STALE = "PRICE_STALE"
    INVENTORY_FULL = "INVENTORY_FULL"
    SOURCE_MISSING = "SOURCE_MISSING"
    UNKNOWN_SOURCE_KIND = "UNKNOWN_SOURCE_KIND"
    GROUP_ROLLBACK = "GROUP_ROLLBACK"
    
    # Social
    TOTAL_DISTRUST = "total_distrust"
    BETRAYAL_HISTORY = "betrayal_history"
    LOYALTY_ACCEPTANCE = "loyalty_acceptance"
    FAIR_COMPENSATION = "fair_compensation"
    HAGGLING_FOR_PAY = "haggling_for_pay"
    INSUFFICIENT_INCENTIVE = "insufficient_incentive"
    USURY_REJECTION = "usury_rejection"
    DESPERATION_ACCEPTANCE = "desperation_acceptance"
    FRIENDLY_LOAN = "friendly_loan"
    UNNECESSARY_DEBT = "unnecessary_debt"
    TEAM_UP_ACCEPTED = "team_up_accepted"
    TEAM_UP_DECLINED = "team_up_declined"
    INFORMATION_SALE_ACCEPTED = "information_sale_accepted"
    TEACH_ACCEPTED = "teach_accepted"
    TEACH_DECLINED = "teach_declined"
    MARRIAGE_ACCEPTED = "marriage_accepted"
    MARRIAGE_DECLINED = "marriage_declined"
    CLAN_JOIN_ACCEPTED = "clan_join_accepted"
    CLAN_JOIN_DECLINED = "clan_join_declined"

    # Quest
    QUEST_COMPLETED = "quest_completed"
    QUEST_FAILED = "quest_failed"
    QUEST_EXPIRED = "quest_expired"
    
    # Legacy/Fallback
    ILLEGAL_ACTION = "ILLEGAL_ACTION"
    UNKNOWN = "unknown"

@unique
class Domain(IntEnum):
    """Scoping for deterministic RNG."""
    DEFAULT = 0
    SPAWN = 1
    WORLD = 2
    CALAMITY = 3
    SOCIAL = 4
    STRATEGIC = 5
    TACTICAL = 6
    ECONOMY = 7
    QUEST = 8
    COMBAT = 9     # Reserved: Combat is deterministic-by-formula (no RNG), but domain exists for future use
    LOOT = 10      # Loot table rolls (future)
    INIT = 11      # World initialization / entity placement
