# Compliance IDs: WORLD-SEM-001, WORLD-SEM-002
from __future__ import annotations

from typing import Optional
from src.core.enums import Faction
from src.content.repository import CatalogRepository


class FactionSemanticsService:
    """
    Code-based interpretation of Faction catalog definition meaning.
    Performs hostiles, protections, and legacy bucket mapping queries.
    """

    def __init__(self, repo: CatalogRepository):
        self.repo = repo

    def get_legacy_faction_bucket(self, faction_id: str) -> Faction:
        """Translates a dynamic catalog faction ID to a legacy Faction enum."""
        defn = self.repo.get_faction(faction_id)
        if not defn:
            # Predictable fallback matching legacy string-to-enum mappers
            f = faction_id.upper()
            if "HERO" in f or "GUILD" in f or "VILLAGE" in f:
                return Faction.HERO_GUILD
            elif "MONSTER" in f or "HORDE" in f or "HOSTILE" in f:
                return Faction.MONSTER_HORDE
            elif "COUNCIL" in f or "TOWN" in f:
                return Faction.TOWN_COUNCIL
            return Faction.NEUTRAL
        
        # Parse legacy bucket string to enum
        try:
            return Faction[defn.legacy_engine_bucket]
        except KeyError:
            return Faction.NEUTRAL

    def get_alignment_bucket(self, faction_id: str) -> str:
        """Returns the alignment category bucket (e.g. defender, invader, neutral)."""
        defn = self.repo.get_faction(faction_id)
        return defn.alignment_bucket if defn else "neutral"

    def get_influence_role(self, faction_id: str) -> str:
        """Returns the influence role configuration."""
        defn = self.repo.get_faction(faction_id)
        return defn.influence_role if defn else "non_combatant"

    def is_hostile(self, faction_a: str, faction_b: str) -> bool:
        """
        Determines if two factions are actively hostile.
        Uses relationship groups and alignment buckets.
        """
        if faction_a == faction_b:
            return False

        defn_a = self.repo.get_faction(faction_a)
        defn_b = self.repo.get_faction(faction_b)

        if not defn_a or not defn_b:
            # Fallback legacy bucket hostility logic
            bucket_a = self.get_legacy_faction_bucket(faction_a)
            bucket_b = self.get_legacy_faction_bucket(faction_b)
            if bucket_a == Faction.MONSTER_HORDE or bucket_b == Faction.MONSTER_HORDE:
                return bucket_a != bucket_b
            return False

        # Hostility Law: Defenders are hostile to Invaders, Invaders hostile to all non-invaders
        align_a = defn_a.alignment_bucket
        align_b = defn_b.alignment_bucket

        if align_a == "invader" or align_b == "invader":
            return align_a != align_b

        return False

    def is_protector(self, faction_id: str) -> bool:
        return self.get_alignment_bucket(faction_id) == "defender"

    def is_invader(self, faction_id: str) -> bool:
        return self.get_alignment_bucket(faction_id) == "invader"

    def is_neutral(self, faction_id: str) -> bool:
        return self.get_alignment_bucket(faction_id) == "neutral"
