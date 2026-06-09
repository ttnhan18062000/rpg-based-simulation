---
ticket: TCK-20260609-REGISTRY-BOOTSTRAP-MODES
phase: plan
---

# Plan

## New module: src/runtime/bootstrap.py

Defines:
- `HardcodedFallbackError(RuntimeError)` — carries `.mode` attribute
- `ContentSourceReport` — frozen dataclass with catalog_counts, compat_counts, fallback_counts (per-family tuples), heuristic_count, fallback_used
- `bootstrap_registries(mode, catalog_repo=_AUTO) -> ContentSourceReport` — explicit mode routing

Mode routing:
  TEST_MANUAL      → _bootstrap_empty (no catalog needed)
  catalog provided → _bootstrap_from_catalog (adapters)
  no catalog + CATALOG_STRICT or CATALOG_WITH_COMPATIBILITY → HardcodedFallbackError
  no catalog + LEGACY_FALLBACK → _bootstrap_from_hardcoded (calls seed_phase1_content)

No changes to src/core/registries.py — additive only.

## New test: tests/unit/runtime/test_registry_bootstrap_modes.py

9 tests, all passing.
