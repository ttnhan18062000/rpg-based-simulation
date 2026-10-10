"""The faction treasury: one typed account per region-owner bucket (EXCH-02, owner decisions 37, 38 and 51).

A treasury is coin like any other purse: it is debited when it pays and credited when it receives, and its balance is never negative. It
lives in `AuthoritativeState.global_resources` (the existing durable, checkpointed, fingerprinted and exported location that apply.py
folds `StateUpdate.resource_updates` into); this module is the one place that knows the key scheme, so the compiler, the town phase and
the resolver cannot disagree about which key is whose.

Debt (rpg-planner's engineering ruling): the account unit is the four-value legacy bucket (`Faction`) that regions and entity identity are
defined on, so catalog factions that share a bucket share one treasury (today only HERO_GUILD owns regions, so the effect is nil). A typed
`AuthoritativeState.treasuries` keyed by catalog faction belongs with M2's ledger.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from src.core.enums import Faction

_KEY_PREFIX = "faction_"
_KEY_SUFFIX = "_gold"


def treasury_key(faction: int) -> str:
    """The `global_resources` key of the treasury of the region-owner bucket `faction` (a `Faction` value)."""
    return f"{_KEY_PREFIX}{Faction(int(faction)).name.lower()}{_KEY_SUFFIX}"


def neutral_faction() -> int:
    """The bucket of the neutral treasury, where coin goes when nobody holds the ground."""
    return int(Faction.NEUTRAL)


def treasury_keys() -> frozenset[str]:
    """Every treasury key there can be: the four buckets."""
    return frozenset(treasury_key(f) for f in Faction)


@dataclass(frozen=True, slots=True)
class TreasuryTransfer:
    """A signed change to one treasury: positive when it receives, negative when it pays. Never a free-floating number: a transfer is
    always one half of a coin movement whose other half is a purse, a building or a corpse (conservation, `total_coin`)."""
    faction: int
    gold_delta: int

    @property
    def key(self) -> str:
        """The `global_resources` key of the treasury this transfer changes."""
        return treasury_key(self.faction)


def balance(resources: Mapping[str, float], faction: int, pending: Optional[Mapping[str, float]] = None) -> float:
    """The treasury's balance: what the state holds plus the changes already accepted this tick (`pending`, keyed by treasury key)."""
    key = treasury_key(faction)
    return float(resources.get(key, 0.0)) + float((pending or {}).get(key, 0.0))


def can_pay(resources: Mapping[str, float], faction: int, amount: float, pending: Optional[Mapping[str, float]] = None) -> bool:
    """Whether the treasury holds `amount` after this tick's accepted changes (a payer short of it pays nothing)."""
    return amount >= 0 and balance(resources, faction, pending) >= amount


def apply_transfer(pending: dict[str, float], transfer: TreasuryTransfer) -> dict[str, float]:
    """`pending` with `transfer` folded in (the same shape `StateUpdate.resource_updates` takes)."""
    out = dict(pending)
    out[transfer.key] = out.get(transfer.key, 0.0) + transfer.gold_delta
    return out


def treasury_coin(resources: Mapping[str, float]) -> float:
    """All coin held in treasuries."""
    keys = treasury_keys()
    return float(sum(v for k, v in resources.items() if k in keys))


def total_coin(state: Any) -> float:
    """Every coin in the world: entity purses (alive or dead), building purses, corpses and treasuries. Conservation says this changes only by
    declared world-creation coin (a spawn's inventory profile, a building's declared till)."""
    entities = sum(e.inventory.gold for e in state.entities.values())
    buildings = sum(b.inventory.gold for b in state.buildings.values())
    corpses = sum(getattr(c, "gold", 0) for c in getattr(state, "corpses", {}).values()) if isinstance(getattr(state, "corpses", None), dict) else 0
    return float(entities + buildings + corpses + treasury_coin(state.global_resources))


def declared_starting_gold(members: Iterable[float]) -> float:
    """A bucket's treasury starts with each member faction's declared starting gold once (EXCH-02: no orphan vaults)."""
    return float(sum(members))
