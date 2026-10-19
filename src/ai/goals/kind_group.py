"""The kind group of an entity: what its kind DECLARES it can eat, never its role (decision 42, D46: no predator/prey labels).

``kind_group`` is the sorted food classes of the entity's body diet joined with ``+`` (``meat``, ``plant+prepared``), ``undeclared`` when the
kind declares no diet. The run ledger and the gate's metric module group by it, so a new kind lands in a group by its content properties alone.
"""
from __future__ import annotations

from typing import Optional

from src.content_semantics.faction import get_species_id_str
from src.core.items import food_class
from src.core.state import EntityState
from src.engine.appraisal import kind_can_eat_item
from src.engine.behavior_consumers import get_kind_properties
from src.engine.serves import keeps_coin

UNDECLARED = "undeclared"
NO_DIET = "none"


def species_kind_group(species_id: Optional[str]) -> str:
    """The group of a species id: its declared diet's food classes, ``none`` for a declared empty diet, ``undeclared`` when absent."""
    _, body = get_kind_properties(species_id)
    diet = getattr(body, "diet", None)
    if diet is None:
        return UNDECLARED
    return "+".join(sorted(diet)) if diet else NO_DIET


def kind_group(entity: EntityState) -> str:
    """The group of an entity (see the module docstring)."""
    return species_kind_group(get_species_id_str(entity))


def is_person(entity: EntityState) -> bool:
    """True when the entity's species declares the coin-and-trade trait (D43: personhood is that trait, never inferred from a diet or a role)."""
    return bool(keeps_coin(entity))


def eats_outside_its_diet(entity: EntityState, item_id: str) -> bool:
    """True when ``item_id`` is food of a class the entity's body diet does not declare (D44). A non-food item is never outside a diet."""
    return food_class(item_id) is not None and not kind_can_eat_item(get_species_id_str(entity), item_id)
