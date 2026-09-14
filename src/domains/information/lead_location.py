"""
src/domains/information/lead_location.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING

The single, sanctioned way to read a real region out of a `kind="location"` lead's own `detail`.

`docs/mechanics/04_strategic_cognition.md` § "Leads (Knowledge)" declares `detail`'s contract for
a location lead: a coordinate (e.g. `(45, 12)`), never a region id directly. Two real consumers
(`src/domains/information/phase.py`, `src/domains/information/contradiction.py`) need a *region*
out of that same lead to detect a "searched here, found it safe" contradiction — resolving the
coordinate to a region via the same real, existing machinery every other position-to-region lookup
in this codebase already uses (`LegalityServiceV2.get_region_for_position()`), rather than
expecting `detail` to already be a region id string that no real producer has ever emitted.

Centralizing this here, rather than duplicating the parse in both consumers, is deliberate: a
second inline copy of this same parse is exactly how a fourth incompatible `detail` convention
gets invented by accident later.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.strategic import LeadState

logger = logging.getLogger(__name__)


def resolve_location_lead_region_id(lead: "LeadState", state: "AuthoritativeState") -> Optional[str]:
    """
    Parse `lead.detail` as the declared `"x,y"` coordinate contract and resolve it to a real
    region id via `LegalityServiceV2.get_region_for_position()`.

    Returns `None` (never raises) when `detail` isn't parseable as coordinates -- a real, known
    shape mismatch for `kind="location"` leads from producers that don't yet conform to the
    declared contract (see the ticket above) -- or when the resolved position falls outside every
    declared region. Both are known-shape outcomes, logged at WARNING naming the lead so a genuine
    mismatch stays visible rather than disappearing into a bare `except`; neither crashes the
    caller.
    """
    if not lead.detail:
        return None

    try:
        x_str, y_str = lead.detail.split(",")
        coords = (float(x_str), float(y_str))
    except (ValueError, AttributeError) as parse_ex:
        logger.warning(
            "Lead %s (subject=%s) has a non-coordinate detail (%r); cannot resolve a region "
            "for it: %s",
            lead.id, lead.subject, lead.detail, parse_ex,
        )
        return None

    from src.engine.legality import LegalityServiceV2

    region = LegalityServiceV2.get_region_for_position(coords, state)
    return region.id if region is not None else None
