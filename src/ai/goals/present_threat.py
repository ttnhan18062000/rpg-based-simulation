"""
src/ai/goals/present_threat.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07

World Rule SURV-07: only a present threat to life outranks a pressing need, so a need's escalation gives way while a present
threat holds (a need never outbids combat flight or engagement). "Present threat" is AGENCY-07's own test (`present_threat_terms`:
wounded, a hostile adjacent, targeting or closing, or outmatching), over the hostiles the subject perceives, with the catalog
hostility the combat scorers use. A wound alone is not a threat here: with no hostile in view there is nothing to give way to.
A pure read of the state.

ACTING (TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE, owner decision memo row 88): a hostile ACTS on a subject only by an act, never by a state.
`present_threat_to` keeps AGENCY-07's full terms (they are why flight is warranted); `acting_threat_to` is the narrower test that decides whether a hostile
holds back an escalated need: the subject perceives it AND either (a) its current task is an attack or a pursuit aimed at the subject, or (b) it took hp
from the subject by a hit within `NEED_WAKE_CADENCE` ticks. Wounded, adjacent, closing without (a) and outmatched are not acts.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.tactical_threat import hostile_acts_on, present_threat_terms

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


def present_threat_to(entity: "EntityState", state: "AuthoritativeState") -> bool:
    """True when a perceived hostile makes a present threat to `entity` (AGENCY-07's terms)."""
    hostiles = perceived_hostiles(entity, state)
    return bool(hostiles) and bool(present_threat_terms(entity, hostiles))


def acting_threat_to(entity: "EntityState", state: "AuthoritativeState") -> bool:
    """True when a perceived hostile is acting on `entity` (see the module docstring). A pure read of the state."""
    return any(hostile_acts_on(h, entity, state.tick) for h in perceived_hostiles(entity, state))
