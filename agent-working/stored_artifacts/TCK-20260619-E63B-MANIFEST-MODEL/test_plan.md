---
ticket_id: TCK-20260619-E63B-MANIFEST-MODEL
phase: test_plan
date: 2026-06-23
---

# Test Plan — TCK-20260619-E63B-MANIFEST-MODEL

## Tests Created

`tests/unit/feature_packs/test_manifest.py` (14 tests):
- test_manifest_defaults
- test_manifest_round_trip — AC: YAML round-trip
- test_manifest_frozen
- test_runtime_profile_defaults
- test_runtime_profile_with_packs
- test_scenario_runtime_profile_optional (backward compat)
- test_scenario_runtime_profile_set
- test_resolver_single_pack
- test_resolver_linear_chain — AC: 3-pack sort
- test_resolver_deterministic_within_level
- test_resolver_circular_dependency_raises — AC
- test_resolver_missing_dependency_raises — AC
- test_resolver_conflict_detection
- test_resolver_same_key_different_domains_ok

## Existing Tests

- tests/unit/scenarios/ — 49 tests pass (SimulationScenarioDefinition backward compat confirmed)

## Result: 63 passed
