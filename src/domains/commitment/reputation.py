"""
src/domains/commitment/reputation.py
───────────────────────────────────────────────────────────────────────────────
ReputationUpdateService for Phase 15.
"""

from __future__ import annotations
from dataclasses import replace
from src.core.cognition import PublicReputationProfile

class ReputationUpdateService:
    """Updates public labels and reputation profiles based on witnessed events."""

    @staticmethod
    def process_witnessed_event(profile: PublicReputationProfile, event_kind: str) -> PublicReputationProfile:
        labels = dict(profile.labels)
        
        if event_kind == "successful_escort":
            labels["reliable"] = min(1.0, labels.get("reliable", 0.5) + 0.1)
        elif event_kind == "betrayal":
            labels["betrayer"] = min(1.0, labels.get("betrayer", 0.0) + 0.4)
            labels["reliable"] = max(0.0, labels.get("reliable", 0.5) - 0.3)
        elif event_kind == "clear_camp":
            labels["camp_clearer"] = min(1.0, labels.get("camp_clearer", 0.0) + 0.2)
            labels["heroic"] = min(1.0, labels.get("heroic", 0.5) + 0.1)

        return replace(profile, labels=labels)
