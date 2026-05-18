# Suggested file 4: tests/helpers/resources.py

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from typing import Any, Iterable

from src.core.state import (
    AuthoritativeState,
    ChestState,
    CorpseState,
    GroundItemState,
    InventoryComponent,
    ItemStack,
    RegionState,
    ResourceNodeState,
)
from tests.helpers.entities import make_state, stack


def _safe_dataclass(cls: type, **kwargs):
    """Construct a dataclass using only fields that exist in the current model."""
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")

    allowed = {field.name for field in fields(cls) if field.init}
    return cls(**{key: value for key, value in kwargs.items() if key in allowed})


def make_resource_node(
    node_id: int = 101,
    *,
    kind: str = "IRON_NODE",
    pos: tuple[float, float] = (1.0, 0.0),
    yields_item: str = "iron_ore",
    remaining_charges: int = 5,
    max_charges: int = 5,
    required_ticks: int = 1,
    cooldown_until_tick: int | None = None,
    **extra,
) -> ResourceNodeState:
    return _safe_dataclass(
        ResourceNodeState,
        id=node_id,
        kind=kind,
        position=pos,
        yields_item=yields_item,
        remaining_charges=remaining_charges,
        max_charges=max_charges,
        required_ticks=required_ticks,
        cooldown_until_tick=cooldown_until_tick,
        **extra,
    )


def make_ground_item(
    item_id: int = 201,
    *,
    pos: tuple[float, float] = (0.0, 0.0),
    item: ItemStack | None = None,
    item_stack: ItemStack | None = None,
    decay_tick: int | None = None,
    **extra,
) -> GroundItemState:
    actual_item = item_stack or item or stack("wood", 1)

    return _safe_dataclass(
        GroundItemState,
        id=item_id,
        position=pos,
        item=actual_item,
        item_stack=actual_item,
        item_id=actual_item.item_id,
        quantity=actual_item.quantity,
        decay_tick=decay_tick,
        **extra,
    )


def make_corpse(
    corpse_id: int = 301,
    *,
    original_entity_id: int = 99,
    pos: tuple[float, float] = (0.0, 0.0),
    items: list[ItemStack] | None = None,
    gold: int = 0,
    decay_tick: int = 200,
    **extra,
) -> CorpseState:
    return _safe_dataclass(
        CorpseState,
        id=corpse_id,
        original_entity_id=original_entity_id,
        position=pos,
        items=items or [stack("wood", 1)],
        gold=gold,
        decay_tick=decay_tick,
        **extra,
    )


def make_chest(
    chest_id: int = 401,
    *,
    pos: tuple[float, float] = (0.0, 0.0),
    items: list[ItemStack] | None = None,
    gold: int = 0,
    opened: bool = False,
    **extra,
) -> ChestState:
    return _safe_dataclass(
        ChestState,
        id=chest_id,
        position=pos,
        inventory=InventoryComponent(items=items or [], gold=gold),
        items=items or [],
        gold=gold,
        opened=opened,
        **extra,
    )


def make_region(
    region_id: str = "test_region",
    *,
    name: str = "Test Region",
    bounds: tuple[int, int, int, int] = (0, 0, 20, 20),
    influence: float = 0.0,
    owner_faction_id=None,
    suppression_active: bool = False,
    threat_level: float = 0.0,
    **extra,
) -> RegionState:
    return _safe_dataclass(
        RegionState,
        id=region_id,
        name=name,
        bounds=bounds,
        influence=influence,
        owner_faction_id=owner_faction_id,
        suppression_active=suppression_active,
        threat_level=threat_level,
        **extra,
    )


def make_resource_state(
    *,
    entities=(),
    nodes: Iterable[ResourceNodeState] = (),
    ground_items: Iterable[GroundItemState] = (),
    corpses: Iterable[CorpseState] = (),
    chests: Iterable[ChestState] = (),
    regions: Iterable[RegionState] = (),
    terrain: dict[tuple[int, int], str] | None = None,
    blocked_tiles: set[tuple[int, int]] | None = None,
    tick: int = 1,
    seed: int = 42,
    **overrides,
) -> AuthoritativeState:
    state = make_state(entities=entities, tick=tick, seed=seed)

    update_values = {
        "resource_nodes": {node.id: node for node in nodes},
        "ground_items": {item.id: item for item in ground_items},
        "corpses": {corpse.id: corpse for corpse in corpses},
        "chests": {chest.id: chest for chest in chests},
        "regions": {region.id: region for region in regions},
        "terrain": terrain or {},
        "blocked_tiles": blocked_tiles or set(),
    }
    update_values.update(overrides)

    return replace(state, **update_values)

