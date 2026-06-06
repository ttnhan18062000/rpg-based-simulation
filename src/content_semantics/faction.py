# Compliance IDs: WORLD-SEM-001, WORLD-SEM-002
from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING, Any
from src.core.enums import Faction
from src.content.repository import CatalogRepository

if TYPE_CHECKING:
    from src.content_semantics.relation import RelationContext

logger = logging.getLogger(__name__)


# Process-level singleton — valid performance optimization for the hot path.
# Use configure_faction_semantics_service() to pre-install a custom repo (e.g. in tests).
# Use reset_faction_semantics_service() to clear the cache in test teardown.
_semantics_service_cache: Optional[FactionSemanticsService] = None


def get_faction_semantics_service() -> FactionSemanticsService:
    global _semantics_service_cache
    if _semantics_service_cache is None:
        from src.content.paths import ContentPathConfig
        repo = CatalogRepository(ContentPathConfig().content_root)
        repo.load_all()
        _semantics_service_cache = FactionSemanticsService(repo)
    return _semantics_service_cache


def configure_faction_semantics_service(repo: CatalogRepository) -> None:
    """Install a pre-built service into the singleton cache. For test setup and app boot."""
    global _semantics_service_cache
    _semantics_service_cache = FactionSemanticsService(repo)


def reset_faction_semantics_service() -> None:
    """Clear the singleton cache. For test teardown."""
    global _semantics_service_cache
    _semantics_service_cache = None

def get_faction_id_str(entity: Any) -> str:
    """Retrieves the dynamic faction ID string of an entity, falling back to enum name."""
    if hasattr(entity, "identity") and hasattr(entity.identity, "properties"):
        faction_id = entity.identity.properties.get("faction_id")
        if faction_id:
            return faction_id
    if hasattr(entity, "identity") and hasattr(entity.identity, "faction"):
        faction_val = entity.identity.faction
        if isinstance(faction_val, str):
            return faction_val.lower()
        try:
            if isinstance(faction_val, int):
                f_enum = Faction(faction_val)
            else:
                f_enum = faction_val
            return f_enum.name.lower()
        except (ValueError, TypeError, AttributeError):
            pass
    return "neutral"

def get_race_id_str(entity: Any) -> str:
    """Retrieves the race ID string of an entity if present in properties."""
    if hasattr(entity, "identity") and hasattr(entity.identity, "properties"):
        return entity.identity.properties.get("race_id")
    return None



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
        if defn:
            return defn.alignment_bucket
        # Fallback to legacy bucket alignment
        legacy = self.get_legacy_faction_bucket(faction_id)
        from src.core.enums import Faction
        if legacy in (Faction.HERO_GUILD, Faction.TOWN_COUNCIL):
            return "defender"
        elif legacy == Faction.MONSTER_HORDE:
            return "invader"
        return "neutral"

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

    def is_hostile_compat(
        self,
        source: str,
        target: str,
        context: Optional[RelationContext] = None,
    ) -> bool:
        """
        Wrapper that attempts clean perspective/relationship projection first,
        falling back to legacy bucket-based semantics and logging fallback usage.
        """
        from src.content_semantics.relation import RelationProjectionService

        # Check if source faction has perspective OR if there's a relationship definition
        has_perspective = False
        for p in self.repo.perspectives.values():
            if p.chosen_faction == source or p.id == source:
                has_perspective = True
                break

        has_relationship = False
        for rel in self.repo.faction_relationships.values():
            if rel.source_faction == source and rel.target_faction == target:
                has_relationship = True
                break

        if not has_perspective and not has_relationship:
            logger.debug(
                "Falling back to legacy hostility semantics for %s -> %s (missing clean relationship/perspective data)",
                source,
                target,
            )
            return self.is_hostile(source, target)

        projection_service = RelationProjectionService(self.repo)
        perspective_id = source
        for p in self.repo.perspectives.values():
            if p.chosen_faction == source:
                perspective_id = p.id
                break

        proj = projection_service.project_relation(perspective_id, source, target, context)

        if proj.label == "enemy":
            return True
        elif proj.label == "threat":
            if context:
                return bool(context.combat_engaged or (context.distance is not None and context.distance <= 5.0))
            return False
        elif proj.label == "intruder":
            if context:
                return bool(context.intruding or context.combat_engaged)
            return False

        return False
