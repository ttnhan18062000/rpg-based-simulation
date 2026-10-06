"""
src/core/violent_cause.py
───────────────────────────────────────────────────────────────────────────────
Which deaths and destructions count toward regional trauma (Mechanics Bible 05 §2, rule ENV-07,
owner decision 15): only those with a **violent cause**. Ambient attrition (environmental hazard
drain, natural death, passive starvation) is exposure, not unrest, and does not count.

The test is the recorded *cause*, never "has a killer": a death is violent when its combat outcome
is one of ``VIOLENT_DEATH_OUTCOME_KINDS``. To admit a future declared catastrophe (a plague, a
famine event) the owner decides it and adds its cause here, in this one place; nothing else in the
engine hard-codes the rule. ``HAZARD`` (the slot hazard drain writes when no combat outcome decided
the death) is deliberately absent.

Measured basis (frontier_living_world and 23 other corpus worlds, 10,000 ticks, audit_mode): 2,112
of 2,144 deaths were ``HAZARD``; none of them had taken attacker damage at any earlier tick.

NOT IMPLEMENTED (ratified, owner 2026-10-05, ENV-07): "a wounded-then-drained death still counts". A
death that hazard drain finishes after combat wounded the entity is recorded ``HAZARD`` and is judged
non-violent here, because the engine keeps no authoritative record of an entity's recent attacker damage
to consult. Counting it needs such a record (a state change); it changes nothing on today's corpus.
"""
from __future__ import annotations

from src.core.combat_constants import TERMINAL_COMBAT_OUTCOME_KINDS

# Combat outcomes a violent death can carry. Derived from the terminal combat result so the two
# cannot drift; extend by decision, not by convenience.
VIOLENT_DEATH_OUTCOME_KINDS = frozenset(TERMINAL_COMBAT_OUTCOME_KINDS)


def is_violent_death_cause(outcome_kind: str | None) -> bool:
    """True when a death carrying this combat ``outcome_kind`` counts toward regional trauma."""
    return outcome_kind in VIOLENT_DEATH_OUTCOME_KINDS


def is_violent_building_destruction(hp_delta: int) -> bool:
    """True when a building's destruction counts toward regional trauma.

    Verified at implementation (rule ENV-07): the only producer of a negative building ``hp_delta``
    is ``SabotageService`` (src/engine/sabotage.py), an actor deliberately damaging the building;
    maintenance insolvency only clears ``functional``. So a destruction that arrives with a
    damaging delta is violent by cause, and one without it is not.
    """
    return hp_delta < 0
