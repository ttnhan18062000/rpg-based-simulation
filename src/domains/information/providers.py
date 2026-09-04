"""
src/domains/information/providers.py
───────────────────────────────────────────────────────────────────────────────
Epic 4.2B — InformationProvider Archetypes.

Defines the durable world model for entities that can serve as information
providers (merchants, guild masters, elders). These records are registered
in AuthoritativeState.information_providers and survive across ticks.

Design:
  - Frozen, immutable dataclass — no direct mutation.
  - Durable state: registered in AuthoritativeState.
  - to_canonical_dict() produces a deterministic serialization.

Logic ID: E42B-001
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple


class InformationProviderArchetype(str, Enum):
    """
    Archetype classification for an information provider entity.

    Determines what knowledge domains the provider can answer queries about
    and how reliable their information tends to be.
    """
    MERCHANT = "MERCHANT"
    GUILD_MASTER = "GUILD_MASTER"
    ELDER = "ELDER"


@dataclass(frozen=True, slots=True)
class InformationProviderState:
    """
    Durable state record for an entity registered as an information provider.

    Registered in AuthoritativeState.information_providers keyed by entity_id.
    Serialized deterministically via to_canonical_dict().

    Fields:
        entity_id:        The entity this record belongs to.
        archetype:        Which provider archetype this entity fulfils.
        reliability_score: How trustworthy this provider's information is
                           (0.0–1.0, default 1.0 = fully reliable).
        knowledge_domains: Tuple of domain strings this provider can answer
                           (e.g. "material_source", "recipe_definition").
        knowledge_age:    Ticks since the provider's knowledge was last refreshed.
                          0 = freshly updated.
        knowledge_accumulated: Cumulative count of distinct knowledge-report events this
                          provider has received (e.g. a quest they assigned being reported
                          back). Monotonically non-decreasing. Distinct from
                          reliability_score (trustworthiness) and knowledge_age (freshness)
                          — see Anti-Drift Notes in TCK-20260903-INFORMATION-HUB-ACCUMULATION.
    """
    entity_id: int
    archetype: InformationProviderArchetype
    reliability_score: float = 1.0
    knowledge_domains: Tuple[str, ...] = ()
    knowledge_age: int = 0
    knowledge_accumulated: int = 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        """
        Deterministic serialization of this provider state.

        knowledge_domains is stored as a list to be JSON-serializable;
        the underlying Tuple preserves insertion order (no sort applied —
        order is the provider's declared priority).
        """
        return {
            "entity_id": self.entity_id,
            "archetype": self.archetype.value,
            "reliability_score": self.reliability_score,
            "knowledge_domains": list(self.knowledge_domains),
            "knowledge_age": self.knowledge_age,
            "knowledge_accumulated": self.knowledge_accumulated,
        }
