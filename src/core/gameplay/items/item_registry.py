"""Standalone ITEM_REGISTRY to break circular dependencies."""

from __future__ import annotations

from typing import Annotated
from pydantic import PlainSerializer, BeforeValidator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from src.core.models.enums import (
    DamageType, Element, ItemType, Rarity,
    DamageTypeSer, ElementSer, ItemTypeSer, RaritySer
)

# Serialization helpers
def _parse_enum(cls):
    def _parse(v):
        if isinstance(v, cls): return v
        if isinstance(v, int):
            try: return cls(v)
            except ValueError: return v
        if isinstance(v, str):
            try: return cls[v.upper()]
            except KeyError: pass
        return v
    return _parse




@pydantic_dataclass(frozen=True)
class ItemTemplate:
    item_id: str
    name: str
    item_type: ItemTypeSer
    rarity: RaritySer
    weight: float = 1.0
    atk_bonus: int = 0
    def_bonus: int = 0
    spd_bonus: int = 0
    max_hp_bonus: int = 0
    crit_rate_bonus: float = 0.0
    evasion_bonus: float = 0.0
    luck_bonus: int = 0
    matk_bonus: int = 0
    mdef_bonus: int = 0
    damage_type: DamageTypeSer = DamageType.PHYSICAL
    element: ElementSer = Element.NONE
    weapon_range: int = 1
    heal_amount: int = 0
    hunger_reduction: float = 0.0
    mana_restore: int = 0
    gold_value: int = 0
    sell_value: int = 0
    description: str = ""


ITEM_REGISTRY: dict[str, ItemTemplate] = {}

def get_item(item_id: str) -> ItemTemplate | None:
    """Return an ItemTemplate from the registry, or None if not found."""
    return ITEM_REGISTRY.get(item_id)
