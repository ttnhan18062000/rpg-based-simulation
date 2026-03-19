"""Data models for spawn and loot configuration."""
from __future__ import annotations
from dataclasses import field
from pydantic.dataclasses import dataclass as pydantic_dataclass
from src.core.enums import EnemyTier, HeroClass, ItemType, EnemyTierSer, HeroClassSer, ItemTypeSer

@pydantic_dataclass(frozen=True)
class SpawnConfig:
    """Maps race and tier to a specific 'kind' string used for naming and lookups."""
    race: str
    tier: EnemyTierSer
    kind: str
    archetype: HeroClassSer
    starting_gear: list[str] = field(default_factory=list)

@pydantic_dataclass(frozen=True)
class LootConfig:
    """Defines drop patterns for different entity types or tiers."""
    kind: str
    drop_chance: float
    guaranteed_items: list[str]
    random_pool: list[str]
    gold_min: int
    gold_max: int

# Global registries to be populated by registry_loader
SPAWN_CONFIGS: dict[tuple[str, EnemyTier], SpawnConfig] = {}
LOOT_CONFIGS: dict[str, LootConfig] = {}
