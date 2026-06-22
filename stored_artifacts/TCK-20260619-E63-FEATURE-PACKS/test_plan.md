---
ticket_id: TCK-20260619-E63-FEATURE-PACKS
phase: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E63-FEATURE-PACKS

## Scope

Epic-tier ticket. Tests owned by child tickets. This plan defines taxonomy and acceptance.

## Unit Tests (by child ticket)

### E63A
- Gate verification report exists as a stored artifact
- `docs/architecture/feature_pack_architecture.md` validates against YAML schema

### E63B — FeaturePackManifest + RuntimeProfile
- `tests/unit/feature_packs/test_manifest.py`
  - Valid manifest YAML round-trips to FeaturePackManifest and back
  - Missing `requires` field defaults to empty list
  - CompatibilityResolver returns topologically sorted order for a 3-pack dependency chain
  - CompatibilityResolver raises on circular dependency
  - CompatibilityResolver raises on missing required pack

### E63C — Registry + Loader
- `tests/unit/feature_packs/test_registry.py`
  - `FeatureRegistry.register()` + `lookup()` round-trip
  - `lookup()` raises on unknown key
  - `list_all()` returns canonical enum members + registered pack extensions
- `tests/unit/feature_packs/test_loader.py`
  - Loader discovers manifests from a fixture directory
  - Loader registers demo pack extension point into mock registry
  - Loader skips pack not in RuntimeProfile.active_pack_names

### E63D — Acceptance
- `tests/integration/feature_packs/test_demo_escort_pack.py`
  - `test_new_quest_type_via_manifest_no_engine_changes`: assert no files in
    `src/engine/` or `src/domains/` were modified to add ESCORT_DIGNITARY route
  - `test_balance_experiment_spec_evaluates_demo_pack`: BalanceExperimentRunner.run()
    returns a result within threshold for the demo pack vs baseline

## Acceptance Criterion

A new quest type (ESCORT_DIGNITARY RouteFamily) is registered and resolvable through
the pack loader without modifying any file under `src/engine/` or `src/domains/`.

## Decision Gate

ALL tests above are blocked until:
1. E53 child tickets implemented (gate condition satisfied)
2. E63A gate verification stored artifact written
