"""
BehaviorNormalizationContext — lightweight context for normalization.

Provides the minimal contextual information a BehaviorEventNormalizer
may use when mapping raw events to behavior events. Must not carry
full world state or require database/network access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class BehaviorNormalizationContext:
    """
    Minimal context passed to BehaviorEventNormalizer.

    Intentionally minimal — normalization must be stateless enough to
    run in a sidecar worker or post-run processor without access to live
    world state.
    """

    run_id: str
    """The run being processed."""

    entity_subject_map: dict[int, str] = field(default_factory=dict)
    """Optional mapping of entity_id → subject label (e.g. class name)."""

    route_family_map: dict[int, str] = field(default_factory=dict)
    """Optional mapping of entity_id → current route family."""

    debug_entity_ids: frozenset[int] = field(default_factory=frozenset)
    """Entity IDs to produce enriched debug output for."""

    @classmethod
    def minimal(cls, run_id: str) -> "BehaviorNormalizationContext":
        """Create a minimal no-enrichment context."""
        return cls(run_id=run_id)
