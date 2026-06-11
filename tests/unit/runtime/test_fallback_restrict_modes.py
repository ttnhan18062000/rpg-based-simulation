"""
Tests for FallbackRestrictedError mode guard in seed_phase1_content.

Verifies that calling seed_phase1_content (the lower-level seeding entrypoint)
with a forbidden mode raises FallbackRestrictedError instead of silently
falling back to hardcoded content.

Distinct from test_registry_bootstrap_modes.py which tests bootstrap_registries
(the higher-level pipeline that already had the guard).
"""

from __future__ import annotations

import pytest

from src.core.modes import FallbackRestrictedError, RuntimeContentMode
from src.runtime.bootstrap import FallbackRestrictedError as BootstrapFallbackRestrictedError
from src.runtime.bootstrap import HardcodedFallbackError
from src.core.registries import seed_phase1_content

pytestmark = pytest.mark.registry_projection


# ---------------------------------------------------------------------------
# Error class hierarchy
# ---------------------------------------------------------------------------

def test_fallback_restricted_error_importable_from_bootstrap():
    """FallbackRestrictedError must be importable from bootstrap for consumers."""
    assert BootstrapFallbackRestrictedError is FallbackRestrictedError


def test_hardcoded_fallback_error_is_subtype_of_fallback_restricted_error():
    """HardcodedFallbackError must remain a subtype for backward compat."""
    assert issubclass(HardcodedFallbackError, FallbackRestrictedError)


def test_fallback_restricted_error_carries_mode():
    err = FallbackRestrictedError(RuntimeContentMode.CATALOG_STRICT)
    assert err.mode is RuntimeContentMode.CATALOG_STRICT


def test_fallback_restricted_error_message_names_mode():
    err = FallbackRestrictedError(RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
    assert "catalog_with_compatibility" in str(err)


def test_fallback_restricted_error_message_suggests_catalog_path():
    err = FallbackRestrictedError(RuntimeContentMode.CATALOG_STRICT)
    assert "data/content" in str(err)


# ---------------------------------------------------------------------------
# seed_phase1_content mode guard
# ---------------------------------------------------------------------------

def test_seed_phase1_content_catalog_strict_no_catalog_raises():
    """CATALOG_STRICT mode must raise FallbackRestrictedError when catalog absent."""
    with pytest.raises(FallbackRestrictedError) as exc_info:
        seed_phase1_content(catalog_repo=None, mode=RuntimeContentMode.CATALOG_STRICT)
    assert exc_info.value.mode is RuntimeContentMode.CATALOG_STRICT
    assert "catalog_strict" in str(exc_info.value)
    assert "data/content" in str(exc_info.value)


def test_seed_phase1_content_compat_mode_no_catalog_raises():
    """CATALOG_WITH_COMPATIBILITY mode must raise FallbackRestrictedError when catalog absent."""
    with pytest.raises(FallbackRestrictedError) as exc_info:
        seed_phase1_content(catalog_repo=None, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
    assert exc_info.value.mode is RuntimeContentMode.CATALOG_WITH_COMPATIBILITY
    assert "catalog_with_compatibility" in str(exc_info.value)


def test_seed_phase1_content_legacy_fallback_no_catalog_succeeds():
    """LEGACY_FALLBACK mode must succeed even without a catalog (fallback is allowed)."""
    result = seed_phase1_content(catalog_repo=None, mode=RuntimeContentMode.LEGACY_FALLBACK)
    # Returns None (no AdapterProjectionResult for hardcoded path) — just must not raise
    assert result is None


def test_hardcoded_fallback_error_raised_as_fallback_restricted_error():
    """Errors raised by bootstrap_registries are also FallbackRestrictedError instances."""
    from src.runtime.bootstrap import bootstrap_registries
    with pytest.raises(FallbackRestrictedError):
        bootstrap_registries(RuntimeContentMode.CATALOG_STRICT, catalog_repo=None)
