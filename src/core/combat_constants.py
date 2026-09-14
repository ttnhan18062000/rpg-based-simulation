"""
src/core/combat_constants.py
───────────────────────────────────────────────────────────────────────────────
Cross-layer combat-mechanics constants.

Neutral base-layer home for constants that both an engine/domains module and an observability
module need to reference without pointing gameplay logic at a telemetry module (or vice versa) --
same rationale and precedent as src/core/social_constants.py. src/core/ is already imported freely
by both layers.
"""
from __future__ import annotations

# hp/max_hp ratio below which an entity's survival counts as "near death" -- used by
# src.observability.event_extractor/event_shapers (near_death_survival event detection) and
# src.domains.combat_engagement.power (Sec 13.5a's WON_EASY/NEAR_DEATH combat-learning outcome
# classification, TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER) to keep both paths consistent
# with a single source of truth, rather than two independently-drifting near-death cutoffs.
NEAR_DEATH_HP_RATIO: float = 0.2
