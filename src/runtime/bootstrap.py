"""
Explicit mode-governed registry bootstrap pipeline.

Modes:
  CATALOG_STRICT             - catalog required; no heuristic inferences; no hardcoded fallback
  CATALOG_WITH_COMPATIBILITY - catalog preferred; heuristics allowed; no hardcoded fallback
  LEGACY_FALLBACK            - hardcoded fallback maps explicitly allowed; catalog optional
  TEST_MANUAL                - no catalog required; registries seeded empty
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from src.core.modes import RuntimeContentMode
from src.core.registries import (
    ArchetypeToEnemyRegistryAdapter,
    CatalogToItemRegistryAdapter,
    CatalogToRecipeRegistryAdapter,
    CatalogToRegionRegistryAdapter,
    CatalogToResourceRegistryAdapter,
    CatalogToServiceRegistryAdapter,
    EnemyRegistry,
    ItemRegistry,
    RecipeRegistry,
    RegionRegistry,
    ResourceRegistry,
    ServiceRegistry,
)

_log = logging.getLogger(__name__)

_AUTO = object()


class HardcodedFallbackError(RuntimeError):
    """Raised when a mode that forbids hardcoded fallback encounters a missing catalog."""

    def __init__(self, mode: RuntimeContentMode, detail: str = "") -> None:
        self.mode = mode
        suffix = f" {detail}" if detail else ""
        super().__init__(f"[mode={mode.value}] Hardcoded fallback is not permitted.{suffix}")


@dataclass(frozen=True)
class ContentSourceReport:
    """Summary of how many records came from each source per family."""

    mode: RuntimeContentMode
    catalog_counts: Tuple[Tuple[str, int], ...]
    compat_counts: Tuple[Tuple[str, int], ...]
    fallback_counts: Tuple[Tuple[str, int], ...]
    heuristic_count: int = 0
    fallback_used: bool = False

    @property
    def total_catalog(self) -> int:
        return sum(c for _, c in self.catalog_counts)

    @property
    def total_compat(self) -> int:
        return sum(c for _, c in self.compat_counts)

    @property
    def total_fallback(self) -> int:
        return sum(c for _, c in self.fallback_counts)


def bootstrap_registries(
    mode: RuntimeContentMode,
    catalog_repo: Any = _AUTO,
) -> ContentSourceReport:
    """Bootstrap all registries according to the given mode.

    Pass catalog_repo=None to explicitly suppress catalog loading (useful in tests).
    The default _AUTO sentinel attempts to load from the default catalog path.
    """
    if catalog_repo is _AUTO:
        catalog_repo = _try_load_default_catalog()

    if mode == RuntimeContentMode.TEST_MANUAL:
        return _bootstrap_empty(mode)

    if catalog_repo is not None:
        return _bootstrap_from_catalog(catalog_repo, mode)

    if mode in (
        RuntimeContentMode.CATALOG_STRICT,
        RuntimeContentMode.CATALOG_WITH_COMPATIBILITY,
    ):
        raise HardcodedFallbackError(
            mode,
            "Catalog not found; hardcoded fallback is not permitted in this mode.",
        )

    return _bootstrap_from_hardcoded(mode)


def _try_load_default_catalog() -> Optional[Any]:
    default_path = "data/content"
    if not os.path.exists(default_path):
        return None
    try:
        from src.content.repository import CatalogRepository

        repo = CatalogRepository(default_path)
        repo.load_all()
        return repo
    except Exception:
        return None


def _bootstrap_empty(mode: RuntimeContentMode) -> ContentSourceReport:
    ItemRegistry.bootstrap({})
    RecipeRegistry.bootstrap({})
    ServiceRegistry.bootstrap({})
    RegionRegistry.bootstrap({})
    ResourceRegistry.bootstrap({})
    EnemyRegistry.bootstrap({})
    return ContentSourceReport(
        mode=mode,
        catalog_counts=(),
        compat_counts=(),
        fallback_counts=(),
        heuristic_count=0,
        fallback_used=False,
    )


def _bootstrap_from_catalog(
    catalog_repo: Any,
    mode: RuntimeContentMode,
) -> ContentSourceReport:
    from src.core.registries import AdapterError

    items, items_heuristic = CatalogToItemRegistryAdapter(catalog_repo, mode=mode).adapt()
    recipes = CatalogToRecipeRegistryAdapter(catalog_repo).adapt()
    services, services_heuristic = CatalogToServiceRegistryAdapter(
        catalog_repo, catalog_mode=True, mode=mode
    ).adapt()
    regions = CatalogToRegionRegistryAdapter(catalog_repo).adapt()
    resources, resources_heuristic = CatalogToResourceRegistryAdapter(
        catalog_repo, mode=mode
    ).adapt()
    enemies = ArchetypeToEnemyRegistryAdapter(catalog_repo, catalog_mode=True).adapt()

    all_heuristic = items_heuristic + services_heuristic + resources_heuristic

    if mode == RuntimeContentMode.CATALOG_STRICT and all_heuristic:
        raise AdapterError(
            all_heuristic[0].record_id,
            f"CATALOG_STRICT mode: {len(all_heuristic)} heuristic inference(s); "
            f"first: {all_heuristic[0].heuristic_type}",
        )

    ItemRegistry.bootstrap(items)
    RecipeRegistry.bootstrap(recipes)
    ServiceRegistry.bootstrap(services)
    RegionRegistry.bootstrap(regions)
    ResourceRegistry.bootstrap(resources)
    EnemyRegistry.bootstrap(enemies)

    return ContentSourceReport(
        mode=mode,
        catalog_counts=(
            ("item", len(items)),
            ("recipe", len(recipes)),
            ("service", len(services)),
            ("region", len(regions)),
            ("resource", len(resources)),
        ),
        compat_counts=(("enemy", len(enemies)),),
        fallback_counts=(),
        heuristic_count=len(all_heuristic),
        fallback_used=False,
    )


def _bootstrap_from_hardcoded(mode: RuntimeContentMode) -> ContentSourceReport:
    _log.warning("[mode=%s] Using legacy hardcoded registry content. No catalog found.", mode.value)
    from src.core.registries import seed_phase1_content

    seed_phase1_content(catalog_repo=None, mode=mode)

    return ContentSourceReport(
        mode=mode,
        catalog_counts=(),
        compat_counts=(),
        fallback_counts=(
            ("item", len(ItemRegistry.all())),
            ("resource", len(ResourceRegistry.all())),
            ("enemy", len(EnemyRegistry.all())),
            ("recipe", len(RecipeRegistry.all())),
            ("service", len(ServiceRegistry.all())),
            ("region", len(RegionRegistry.all())),
        ),
        heuristic_count=0,
        fallback_used=True,
    )
