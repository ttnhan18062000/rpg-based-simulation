"""Standalone ITEM_REGISTRY to break circular dependencies."""

from __future__ import annotations

from typing import Annotated
from pydantic import PlainSerializer, BeforeValidator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from src.core.enums import DamageType, Element, ItemType, Rarity

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

_ItemTypeSer = Annotated[ItemType, BeforeValidator(_parse_enum(ItemType)), PlainSerializer(lambda v: ItemType(v).name.lower(), return_type=str)]
_RaritySer = Annotated[Rarity, BeforeValidator(_parse_enum(Rarity)), PlainSerializer(lambda v: Rarity(v).name.lower(), return_type=str)]
_DamageTypeSer = Annotated[int, BeforeValidator(_parse_enum(DamageType)), PlainSerializer(lambda v: DamageType(v).name.lower(), return_type=str)]
_ElementSer = Annotated[int, BeforeValidator(_parse_enum(Element)), PlainSerializer(lambda v: Element(v).name.lower(), return_type=str)]


@pydantic_dataclass(frozen=True)
class ItemTemplate:
    item_id: str
    name: str
    item_type: _ItemTypeSer
    rarity: _RaritySer
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
    damage_type: _DamageTypeSer = DamageType.PHYSICAL
    element: _ElementSer = Element.NONE
    weapon_range: int = 1
    heal_amount: int = 0
    mana_restore: int = 0
    gold_value: int = 0
    sell_value: int = 0
    description: str = ""


ITEM_REGISTRY: dict[str, ItemTemplate] = {}
