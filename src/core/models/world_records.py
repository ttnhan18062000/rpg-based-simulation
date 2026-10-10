"""Small durable records of the world's coin and bodies (EXCH-02): a body that can be looted, and a debt a treasury owes. They live in
`AuthoritativeState.corpses` and `AuthoritativeState.owed`; `src/core/state.py` re-exports them."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.models.inventory import ItemStack


@dataclass(frozen=True, slots=True)
class CorpseState:
    """A dead entity that can be looted."""
    id: int
    original_entity_id: int
    position: tuple[float, float]
    items: List[ItemStack]
    decay_tick: int
    gold: int = 0  # the dead entity's coin, moved here at death (EXCH-02): taken by a looter, or paid to the place holder's treasury at decay
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        """The body as plain sorted-key data for hashing and checkpoints."""
        if self._canonical_cache is not None:
            cached: Dict[str, Any] = self._canonical_cache
            return cached
        res = {
            "id": self.id,
            "original_entity_id": self.original_entity_id,
            "position": self.position,
            "items": [i.to_canonical_dict() for i in sorted(self.items, key=lambda x: x.item_id)],
            "decay_tick": self.decay_tick,
            "gold": self.gold,
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res


@dataclass(frozen=True, slots=True)
class OwedRecord:
    """A coin debt a faction treasury could not pay when it fell due (EXCH-02, decision 58): the creditor was promised `amount` and is owed it
    until the treasury can pay, oldest first. It lives in `AuthoritativeState.owed` until paid or written off, and is shown by the presenter."""
    id: str
    creditor_id: int
    debtor_faction: int  # the treasury (a Faction value) that owes it
    amount: int
    posted_tick: int
    reason: str = "QUEST_REWARD"
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        """The record as plain sorted-key data for hashing and checkpoints."""
        if self._canonical_cache is not None:
            cached: Dict[str, Any] = self._canonical_cache
            return cached
        res = {"id": self.id, "creditor_id": self.creditor_id, "debtor_faction": self.debtor_faction, "amount": self.amount,
               "posted_tick": self.posted_tick, "reason": self.reason}
        object.__setattr__(self, "_canonical_cache", res)
        return res


def fold_owed(prior: Dict[str, OwedRecord], removed: List[str], added: List[OwedRecord]) -> Dict[str, OwedRecord]:
    """The debts after payments (`removed`) and new debts (`added`); the prior mapping itself when nothing changed."""
    if not (removed or added):
        return prior
    gone = set(removed)
    merged = {k: v for k, v in prior.items() if k not in gone}
    merged.update({rec.id: rec for rec in added})
    return merged
