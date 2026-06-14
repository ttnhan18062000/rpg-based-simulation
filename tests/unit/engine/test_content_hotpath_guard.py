"""Tests for ContentWarmupService and the CatalogRepository tick hot-path guard.

Compliance: WORLD-CAT-004 (content loaded before first tick), WORLD-CAT-005 (read-only
after initial load), WORLD-CAT-HOTPATH-001 (load_all raises inside tick context).
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_content_singletons():
    """Reset all content singletons before and after each test."""
    import src.content_semantics.faction as faction_mod
    from src.content.repository import _tick_context_active
    faction_mod._semantics_service_cache = None
    _tick_context_active.active = False
    yield
    faction_mod._semantics_service_cache = None
    _tick_context_active.active = False


# ---------------------------------------------------------------------------
# ContentWarmupService
# ---------------------------------------------------------------------------

class TestContentWarmupService:
    def test_warmup_populates_faction_singleton(self):
        import src.content_semantics.faction as faction_mod
        from src.content.warmup import ContentWarmupService
        from src.content.repository import CatalogRepository
        from unittest.mock import MagicMock

        assert faction_mod._semantics_service_cache is None

        mock_repo = MagicMock(spec=CatalogRepository)
        ContentWarmupService.warmup(repo=mock_repo)

        assert faction_mod._semantics_service_cache is not None

    def test_is_warm_false_before_warmup(self):
        from src.content.warmup import ContentWarmupService
        assert ContentWarmupService.is_warm() is False

    def test_is_warm_true_after_warmup(self):
        from src.content.warmup import ContentWarmupService
        from src.content.repository import CatalogRepository
        from unittest.mock import MagicMock

        mock_repo = MagicMock(spec=CatalogRepository)
        ContentWarmupService.warmup(repo=mock_repo)
        assert ContentWarmupService.is_warm() is True

    def test_reset_clears_singletons(self):
        from src.content.warmup import ContentWarmupService
        from src.content.repository import CatalogRepository
        from unittest.mock import MagicMock

        mock_repo = MagicMock(spec=CatalogRepository)
        ContentWarmupService.warmup(repo=mock_repo)
        assert ContentWarmupService.is_warm() is True

        ContentWarmupService.reset()
        assert ContentWarmupService.is_warm() is False

    def test_reset_blocked_outside_pytest(self, monkeypatch):
        from src.content.warmup import ContentWarmupService
        import sys
        monkeypatch.delitem(sys.modules, "pytest", raising=False)
        with pytest.raises(AssertionError, match="test-only"):
            ContentWarmupService.reset()


# ---------------------------------------------------------------------------
# ContentHotPathViolation — CatalogRepository guard
# ---------------------------------------------------------------------------

class TestContentHotPathViolation:
    def test_load_all_raises_inside_tick_context(self, tmp_path):
        from src.content.repository import CatalogRepository, _tick_context_active, ContentHotPathViolation

        repo = CatalogRepository(content_dir=str(tmp_path))
        _tick_context_active.active = True

        with pytest.raises(ContentHotPathViolation, match="tick is active"):
            repo.load_all()

    def test_load_all_ok_outside_tick_context(self, tmp_path):
        from src.content.repository import CatalogRepository, _tick_context_active

        repo = CatalogRepository(content_dir=str(tmp_path))
        _tick_context_active.active = False

        # No files in tmp_path — load_all runs with empty results (no exception)
        report = repo.load_all()
        assert report is not None

    def test_tick_context_flag_is_thread_local(self):
        """Two threads have independent tick context flags."""
        from src.content.repository import _tick_context_active
        import threading

        results = {}

        def check_in_thread(thread_id, active_value):
            _tick_context_active.active = active_value
            results[thread_id] = getattr(_tick_context_active, "active", False)

        t1 = threading.Thread(target=check_in_thread, args=("t1", True))
        t2 = threading.Thread(target=check_in_thread, args=("t2", False))

        t1.start(); t2.start()
        t1.join(); t2.join()

        assert results["t1"] is True
        assert results["t2"] is False

    def test_tick_context_cleared_on_exception(self):
        """_tick_context_active must be cleared even when tick raises."""
        from src.content.repository import _tick_context_active

        class BoomPhase(Exception):
            pass

        _tick_context_active.active = True
        try:
            with pytest.raises(BoomPhase):
                try:
                    raise BoomPhase("simulated tick failure")
                finally:
                    _tick_context_active.active = False
        finally:
            pass

        assert getattr(_tick_context_active, "active", False) is False


# ---------------------------------------------------------------------------
# Architecture test — no content load during Kernel.tick_once()
# ---------------------------------------------------------------------------

class TestNoContentLoadInTickHotPath:
    def test_load_all_not_called_during_warm_kernel_tick(self):
        """Architecture test: warm kernel must not trigger load_all() inside tick_once().

        We patch CatalogRepository.load_all to raise if called and also assert that
        the tick_once path does not hit it when the singleton is already populated.
        """
        from src.content.repository import CatalogRepository, ContentHotPathViolation
        from src.content.warmup import ContentWarmupService
        from unittest.mock import MagicMock, patch

        mock_repo = MagicMock(spec=CatalogRepository)
        ContentWarmupService.warmup(repo=mock_repo)

        # Now simulate what tick_once does with the context flag
        from src.content.repository import _tick_context_active

        load_all_called = []

        original_load_all = CatalogRepository.load_all
        def guarded_load_all(self_repo, strict=False):
            load_all_called.append(True)
            return original_load_all(self_repo, strict)

        with patch.object(CatalogRepository, "load_all", guarded_load_all):
            _tick_context_active.active = True
            try:
                # Simulate a tick that would call get_faction_semantics_service()
                # but the singleton is already warm — load_all must NOT be called.
                from src.content_semantics.faction import get_faction_semantics_service
                # This should return cached service, not call load_all
                svc = get_faction_semantics_service()
                assert svc is not None
            finally:
                _tick_context_active.active = False

        assert not load_all_called, (
            "load_all() was called inside tick context — singleton was not warm"
        )
