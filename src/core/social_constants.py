"""
src/core/social_constants.py
───────────────────────────────────────────────────────────────────────────────
Cross-layer social-mechanics constants.

Neutral base-layer home for constants that both a domains module and an
observability module need to reference without crossing the domains ->
observability import boundary (see tests/architecture/test_phase18_import_boundaries.py).
src/core/ is already imported freely by both layers.
"""
from __future__ import annotations

# Minimum trust score in SocialMemoryRecord.relationship_scores to trigger grief.
# Used by src.domains.campaigns.grief_urgency (episode-boundary grief injection) and
# src.observability.event_extractor (mid-episode grief-trigger detection) to keep both
# paths consistent with a single source of truth.
ALLY_TRUST_THRESHOLD: float = 0.30
