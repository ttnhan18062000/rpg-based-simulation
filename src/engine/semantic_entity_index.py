# Compliance IDs: PERF-010, PERF-011
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Set, Tuple, List, Optional, TYPE_CHECKING

from src.engine.world_index import CacheInvalidationPolicy

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.dirty import DirtySet

# docs/mechanics/01_entity_anatomy.md:76 -- "Hunger | +0.1 | 100.0 | 95.0: Starvation (+2 HP damage/tick)"
HUNGER_NEED_THRESHOLD = 95.0
# docs/mechanics/01_entity_anatomy.md:77 -- "Sleep Debt | +0.05 | 100.0 | 98.0: Fatigue (+1 HP damage/tick)"
SLEEP_DEBT_NEED_THRESHOLD = 98.0
# No Mechanics Bible Penalty Threshold exists for rest_pressure (Stamina's "Exhaustion Threshold" is a
# distinct field). Reuses the forced-rest cutoff already shipped in
# src/domains/combat_engagement/perception.py:95 and src/systems/world_systems/routine.py:49.
REST_PRESSURE_NEED_THRESHOLD = 70.0

# Maps a SemanticEntityIndexes dimension name to the CacheInvalidationPolicy domain
# name it depends on. Deliberately different vocabularies: "role_class" and "faction"
# both map to the "identity" invalidation domain, matching the pre-existing ternaries.
_DIMENSION_TO_DOMAIN = {
    "role_class": "identity",
    "region": "region",
    "faction": "identity",
    "need": "needs",
    "knowledge_domain": "knowledge",
}
_ALL_DIMENSIONS: FrozenSet[str] = frozenset(_DIMENSION_TO_DOMAIN.keys())


@dataclass(frozen=True)
class SemanticEntityIndexes:
    """
    Immutable semantic indices over live entity state for a single tick.
    Non-authoritative derived projection -- always rebuildable from AuthoritativeState.
    Logic ID: PERF-010 (Semantic Entity Indexes)
    """
    tick: int
    by_role_class: Dict[Tuple[int, str], Tuple[int, ...]]
    by_region: Dict[str, Tuple[int, ...]]
    by_faction: Dict[int, Tuple[int, ...]]
    by_need: Dict[str, Tuple[int, ...]]
    by_knowledge_domain: Dict[str, Tuple[int, ...]]
    resolved_dimensions: FrozenSet[str] = field(default_factory=frozenset)


class SemanticEntityIndexService:
    """
    Authoritative builder for reusable semantic indices over live entity state.
    Lazy, pull-based, CacheInvalidationPolicy/DirtySet-driven lifecycle, mirroring
    WorldIndexService (src/engine/world_index.py) at a per-entity-dimension granularity
    instead of a spatial one.
    Logic ID: PERF-010 (Semantic Entity Index Service)
    """

    @staticmethod
    def get_indexes(
        state: AuthoritativeState,
        dirty: Optional[DirtySet] = None,
        dimensions: Optional[Set[str]] = None,
    ) -> SemanticEntityIndexes:
        existing: Optional[SemanticEntityIndexes] = getattr(state, "semantic_entity_indexes", None)

        already_resolved: FrozenSet[str] = (
            existing.resolved_dimensions
            if existing is not None and existing.tick == state.tick
            else frozenset()
        )

        role_class_index = (
            existing.by_role_class
            if existing is not None and (
                "role_class" in already_resolved
                or (dimensions is not None and "role_class" not in dimensions)
                or not CacheInvalidationPolicy.should_invalidate("identity", dirty)
            )
            else SemanticEntityIndexService._build_role_class_index(state)
        )
        region_index = (
            existing.by_region
            if existing is not None and (
                "region" in already_resolved
                or (dimensions is not None and "region" not in dimensions)
                or not CacheInvalidationPolicy.should_invalidate("region", dirty)
            )
            else SemanticEntityIndexService._build_region_index(state)
        )
        faction_index = (
            existing.by_faction
            if existing is not None and (
                "faction" in already_resolved
                or (dimensions is not None and "faction" not in dimensions)
                or not CacheInvalidationPolicy.should_invalidate("identity", dirty)
            )
            else SemanticEntityIndexService._build_faction_index(state)
        )
        needs_index = (
            existing.by_need
            if existing is not None and (
                "need" in already_resolved
                or (dimensions is not None and "need" not in dimensions)
                or not CacheInvalidationPolicy.should_invalidate("needs", dirty)
            )
            else SemanticEntityIndexService._build_needs_index(state)
        )
        knowledge_index = (
            existing.by_knowledge_domain
            if existing is not None and (
                "knowledge_domain" in already_resolved
                or (dimensions is not None and "knowledge_domain" not in dimensions)
                or not CacheInvalidationPolicy.should_invalidate("knowledge", dirty)
            )
            else SemanticEntityIndexService._build_knowledge_domain_index(state)
        )

        newly_settled: FrozenSet[str] = (
            _ALL_DIMENSIONS if (existing is None or dimensions is None) else frozenset(dimensions)
        )
        resolved_dimensions = already_resolved | newly_settled

        new_indexes = SemanticEntityIndexes(
            tick=state.tick,
            by_role_class=role_class_index,
            by_region=region_index,
            by_faction=faction_index,
            by_need=needs_index,
            by_knowledge_domain=knowledge_index,
            resolved_dimensions=resolved_dimensions,
        )

        try:
            object.__setattr__(state, "semantic_entity_indexes", new_indexes)
        except AttributeError:
            pass

        return new_indexes

    @staticmethod
    def _build_role_class_index(state: AuthoritativeState) -> Dict[Tuple[int, str], Tuple[int, ...]]:
        buckets: Dict[Tuple[int, str], List[int]] = {}
        for e_id, e in state.entities.items():
            key = (e.identity.role, e.identity.class_id)
            buckets.setdefault(key, []).append(e_id)
        return {k: tuple(sorted(v)) for k, v in buckets.items()}

    @staticmethod
    def _build_region_index(state: AuthoritativeState) -> Dict[str, Tuple[int, ...]]:
        buckets: Dict[str, List[int]] = {}
        for e_id, e in state.entities.items():
            region_id = e.navigation.region_id
            if region_id is None:
                continue
            buckets.setdefault(region_id, []).append(e_id)
        return {k: tuple(sorted(v)) for k, v in buckets.items()}

    @staticmethod
    def _build_faction_index(state: AuthoritativeState) -> Dict[int, Tuple[int, ...]]:
        buckets: Dict[int, List[int]] = {}
        for e_id, e in state.entities.items():
            buckets.setdefault(e.identity.faction, []).append(e_id)
        return {k: tuple(sorted(v)) for k, v in buckets.items()}

    @staticmethod
    def _build_needs_index(state: AuthoritativeState) -> Dict[str, Tuple[int, ...]]:
        buckets: Dict[str, List[int]] = {}
        for e_id, e in state.entities.items():
            bio = e.biological
            if bio.hunger >= HUNGER_NEED_THRESHOLD:
                buckets.setdefault("hunger", []).append(e_id)
            if bio.sleep_debt >= SLEEP_DEBT_NEED_THRESHOLD:
                buckets.setdefault("sleep_debt", []).append(e_id)
            if bio.rest_pressure > REST_PRESSURE_NEED_THRESHOLD:
                buckets.setdefault("rest_pressure", []).append(e_id)
        return {k: tuple(sorted(v)) for k, v in buckets.items()}

    @staticmethod
    def _build_knowledge_domain_index(state: AuthoritativeState) -> Dict[str, Tuple[int, ...]]:
        buckets: Dict[str, List[int]] = {}
        for provider_id, provider in state.information_providers.items():
            for domain in provider.knowledge_domains:
                buckets.setdefault(domain, []).append(provider_id)
        return {k: tuple(sorted(v)) for k, v in buckets.items()}


class SemanticEntityQuery:
    """
    Query-facing entry point over SemanticEntityIndexes. Every method returns only
    entity IDs (Tuple[int, ...]) -- never EntityState/component objects.
    """

    @staticmethod
    def by_role_class(state: AuthoritativeState, dirty: Optional[DirtySet], role: int, class_id: str) -> Tuple[int, ...]:
        indexes = SemanticEntityIndexService.get_indexes(state, dirty, dimensions={"role_class"})
        return indexes.by_role_class.get((role, class_id), ())

    @staticmethod
    def by_region(state: AuthoritativeState, dirty: Optional[DirtySet], region_id: str) -> Tuple[int, ...]:
        indexes = SemanticEntityIndexService.get_indexes(state, dirty, dimensions={"region"})
        return indexes.by_region.get(region_id, ())

    @staticmethod
    def by_faction(state: AuthoritativeState, dirty: Optional[DirtySet], faction: int) -> Tuple[int, ...]:
        indexes = SemanticEntityIndexService.get_indexes(state, dirty, dimensions={"faction"})
        return indexes.by_faction.get(faction, ())

    @staticmethod
    def by_need(state: AuthoritativeState, dirty: Optional[DirtySet], need: str) -> Tuple[int, ...]:
        indexes = SemanticEntityIndexService.get_indexes(state, dirty, dimensions={"need"})
        return indexes.by_need.get(need, ())

    @staticmethod
    def by_knowledge_domain(state: AuthoritativeState, dirty: Optional[DirtySet], domain: str) -> Tuple[int, ...]:
        indexes = SemanticEntityIndexService.get_indexes(state, dirty, dimensions={"knowledge_domain"})
        return indexes.by_knowledge_domain.get(domain, ())
