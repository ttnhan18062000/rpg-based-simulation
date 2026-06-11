---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260608-REGISTRY-PARITY-SPLIT
artifact_type: investigation
tags: [registry, parity, split]
---

# Investigation — TCK-20260608-REGISTRY-PARITY-SPLIT

## Current Behavior
tests/integration/content/test_registry_projection_parity.py had 5 tests, all seeded under CATALOG_WITH_COMPATIBILITY. No strict-mode or legacy-fallback parity tests existed. No heuristic detail assertions (only implicit via registry state).

## Change
Added 3 new test functions:
- test_compatibility_mode_heuristic_usages_are_detailed: asserts typed AdapterHeuristicUsage records
- test_strict_mode_produces_zero_heuristic_usages: uses a minimal fully-explicit temp catalog
- test_legacy_fallback_seeds_only_hardcoded_records: asserts hardcoded records seeded with no catalog

## No production code changed.
