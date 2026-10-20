"""Where a mid-run entity add came from (M0 gate V8: every add has a declared source).

Carried BESIDE an ``entities_add`` entry in the staged update (``StateUpdate.entity_spawn_sources``, keyed by the added entity's id), never on
``EntityState``: it is the record of one add, so no state hash moves. A source is well-formed by construction (``__post_init__`` rejects the rest).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class SpawnKind(str, Enum):
    """The three honest ways an entity enters the world."""

    INITIAL = "INITIAL"  # part of the world as assembled (no producer tags it yet: world assembly does not go through entities_add)
    BIRTH = "BIRTH"  # born of two parents
    AUTHORED_ARRIVAL = "AUTHORED_ARRIVAL"  # arrives by an authored content rule (rule_kind, rule_id)


@dataclass(frozen=True, slots=True)
class SpawnSource:
    """One add's declared source: ``parent_ids`` only for BIRTH, ``rule_kind``/``rule_id`` required for AUTHORED_ARRIVAL."""

    kind: SpawnKind
    parent_ids: Tuple[int, ...] = ()
    rule_kind: Optional[str] = None
    rule_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind is SpawnKind.BIRTH and not self.parent_ids:
            raise ValueError("a BIRTH source names its parents")
        if self.kind is not SpawnKind.BIRTH and self.parent_ids:
            raise ValueError("only a BIRTH source has parent_ids")
        if self.kind is SpawnKind.AUTHORED_ARRIVAL and not (self.rule_kind and self.rule_id):
            raise ValueError("an AUTHORED_ARRIVAL source names its rule (rule_kind and rule_id)")
