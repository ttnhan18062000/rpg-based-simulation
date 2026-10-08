"""
src/ai/goals/present_threat.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07

World Rule SURV-07: only a present threat to life outranks a pressing need, so a need's escalation gives way while a present
threat holds (a need never outbids combat flight or engagement). "Present threat" is AGENCY-07's own test (`present_threat_terms`:
wounded, a hostile adjacent, targeting or closing, or outmatching), over the hostiles the subject perceives, with the catalog
hostility the combat scorers use. A wound alone is not a threat here: with no hostile in view there is nothing to give way to.
A pure read of the state.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.tactical_threat import present_threat_terms

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


def present_threat_to(entity: "EntityState", state: "AuthoritativeState") -> bool:
    """True when a perceived hostile makes a present threat to `entity` (AGENCY-07's terms)."""
    hostiles = perceived_hostiles(entity, state)
    return bool(hostiles) and bool(present_threat_terms(entity, hostiles))
