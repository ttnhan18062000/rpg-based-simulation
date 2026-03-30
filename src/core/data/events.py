from dataclasses import dataclass
from typing import Dict, Optional

class DomainEvent:
    """Base class for all strictly-typed simulation events."""
    pass

@dataclass
class CombatEvent(DomainEvent):
    attacker_id: int
    defender_id: int
    damage: int
    is_crit: bool
    is_evasion: bool
    skill_used: str
    attacker_hp: int
    defender_hp: int

@dataclass
class DeathEvent(DomainEvent):
    entity_id: int
    killer_id: Optional[int]
    x: int
    y: int
    level_at_death: int
    is_permadeath: bool

@dataclass
class LootEvent(DomainEvent):
    entity_id: int
    item_id: str
    item_name: str
    source: str

@dataclass
class LevelUpEvent(DomainEvent):
    entity_id: int
    old_level: int
    new_level: int
    attribute_gains: Dict[str, int]

@dataclass
class TradeEvent(DomainEvent):
    entity_id: int
    action: str  # "buy" or "sell"
    item_id: str
    gold_change: int

@dataclass
class CraftEvent(DomainEvent):
    entity_id: int
    recipe_id: str
    output_item: str

@dataclass
class QuestEvent(DomainEvent):
    entity_id: int
    quest_title: str
    quest_type: str
    status: str # "accepted", "completed", "failed"
    gold_reward: int
    xp_reward: int

@dataclass
class RenownEvent(DomainEvent):
    entity_id: int
    glory_type: str # "boss_kill", "saved_town", "monument_builder", "evolution"
    description: str
    renown_gain: float

@dataclass
class WarEvent(DomainEvent):
    faction_id: int
    is_declared: bool
    aggression: float

@dataclass
class ConquestEvent(DomainEvent):
    region_id: str
    region_name: str
    old_owner: str | None
    new_owner: str | None
    is_liberation: bool
