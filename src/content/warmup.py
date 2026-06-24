# Compliance IDs: WORLD-CAT-004, WORLD-CAT-005, WORLD-CAT-HOTPATH-001
"""ContentWarmupService — eagerly loads all content singletons before the first tick.

WORLD-CAT-004: Content must be fully loaded before any simulation tick begins.
WORLD-CAT-005: Content is read-only after initial load.

Call warmup() once during Kernel.__init__() after world assembly. Do not call
reset() in production — it is provided exclusively for test isolation.
"""
from __future__ import annotations

import sys
from typing import Optional

from src.content.repository import CatalogRepository
from src.content.paths import ContentPathConfig


class ContentWarmupService:
    """Eagerly forces all lazy content singletons to load before the tick pipeline starts.

    Satisfies WORLD-CAT-004 by ensuring CatalogRepository.load_all() is never
    triggered from inside tick_once().
    """

    @staticmethod
    def warmup(repo: Optional[CatalogRepository] = None) -> None:
        """Force-load all content singletons.

        If *repo* is provided it is installed into all consumer singletons directly
        (useful when the caller already holds a loaded repo). Otherwise a catalog is
        loaded once and shared across all consumers so that no load_all() call can
        occur from inside tick_once() (WORLD-CAT-004).
        """
        from src.content_semantics.faction import (
            configure_faction_semantics_service,
        )
        from src.engine.behavior_consumers import configure_behavior_consumers

        if repo is not None:
            configure_faction_semantics_service(repo)
            configure_behavior_consumers(repo)
        else:
            # Load content once and share across all consumers (WORLD-CAT-004).
            _repo = CatalogRepository(ContentPathConfig().content_root)
            _repo.load_all()
            configure_faction_semantics_service(_repo)
            configure_behavior_consumers(_repo)

    @staticmethod
    def is_warm() -> bool:
        """Return True if all known content singletons are loaded (non-None)."""
        from src.content_semantics import faction as _faction_mod
        return _faction_mod._semantics_service_cache is not None

    @staticmethod
    def reset() -> None:
        """Clear all content singletons. FOR TEST USE ONLY.

        Raises AssertionError if called outside a pytest session to prevent
        accidental production use.
        """
        assert "pytest" in sys.modules, (
            "ContentWarmupService.reset() is test-only. "
            "Do not call it in production code."
        )
        from src.content_semantics.faction import reset_faction_semantics_service
        from src.engine.behavior_consumers import reset_behavior_consumers
        reset_faction_semantics_service()
        reset_behavior_consumers()
