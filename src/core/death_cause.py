"""The typed cause of a death and the typed source of an hp loss (TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH).

`LifecycleComponent.death_reason` is a string the lifecycle resolver writes; this enum is its typed reading, so a gate reads a member and never
compares a literal. An hp loss has exactly one of three sources (a hit, the region's hazard drain, the starving drain); a loss none of them
explains is UNATTRIBUTED, a count that must stay at zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class DeathCause(str, Enum):
    """Why a body died; the values are the `death_reason` literals the lifecycle resolver records."""
    COMBAT = "COMBAT"  # a lethal hit (outcome KILL)
    DEFEAT = "DEFEAT"  # a non-lethal zeroing by combat
    HAZARD = "HAZARD"  # the region's hazard drain took the last hp
    STARVATION = "STARVATION"
    SLEEP_DEPRIVATION = "SLEEP_DEPRIVATION"
    OLD_AGE = "OLD_AGE"
    UNKNOWN = "UNKNOWN"  # the catch-all: a dead body with no recorded reason; must stay at zero


def death_cause_of(death_reason: Optional[str]) -> DeathCause:
    """The typed cause for a recorded `death_reason`; anything unrecorded or unrecognised is UNKNOWN."""
    try:
        return DeathCause(death_reason) if death_reason is not None else DeathCause.UNKNOWN
    except ValueError:
        return DeathCause.UNKNOWN


class HpLossSource(str, Enum):
    """Where an hp loss came from."""
    HIT = "HIT"  # a combat resolution (damage from an attacker)
    HAZARD = "HAZARD"  # the region's hazard drain (`CombatUpdate.hazard_damage`)
    STARVATION = "STARVATION"  # the starving passive drain, written by the apply path's passive branch (no update carries it)
    UNATTRIBUTED = "UNATTRIBUTED"  # a loss none of the above explains; must stay at zero


@dataclass(frozen=True, slots=True)
class DeathRecord:
    """The durable record of one death, written once by the lifecycle resolver on the tick it records the death.

    `cause` is the typed reading of `death_reason`; `last_attacker_id` is the body that last took hp from this one (this tick's attacker when a hit
    killed it, else the last one `CombatComponent.last_attacker_id` remembers; None when nothing ever hit it); `hazard_kind` is the region's hazard
    kind and is set only for a HAZARD death. It sits in the canonical state, so a wrong record shows in the fingerprint and in replay.
    """
    cause: DeathCause
    tick: int
    last_attacker_id: Optional[int] = None
    hazard_kind: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """The canonical form the state fingerprint carries."""
        return {"cause": self.cause.value, "tick": self.tick, "last_attacker_id": self.last_attacker_id, "hazard_kind": self.hazard_kind}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeathRecord":
        """The record back from its canonical form."""
        return cls(cause=DeathCause(data["cause"]), tick=int(data["tick"]), last_attacker_id=data.get("last_attacker_id"), hazard_kind=data.get("hazard_kind"))
