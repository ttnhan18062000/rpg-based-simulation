---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E63C-REGISTRY-LOADER
phase: done
date: 2026-06-22
tags: [feature-packs, registry, loader, demo-pack, phase-6]
---

# TCK-20260619-E63C-REGISTRY-LOADER

## Title
Epic 6.3C · FeatureRegistry + FeaturePackLoader + Demo Pack

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement the dict-based `FeatureRegistry[T]` generic, `FeaturePackLoader` that discovers
and loads pack manifests, and a `demo_escort_pack` that adds a new RouteFamily via manifest
without modifying any file in `src/engine/` or `src/domains/`.

## Scope
- `src/domains/feature_packs/registry.py`: `FeatureRegistry[T]` generic
  (register(), lookup(), list_all() including canonical enum members)
- `src/domains/feature_packs/loader.py`: `FeaturePackLoader.load(profile, manifest_dir)`
  — discovers manifests, resolves order, imports entry point modules, calls register()
- Demo pack `content/packs/demo_escort_pack/`:
  - `manifest.yaml`: name=demo_escort_pack, extension_points=[{domain: adventure_routing,
    class_path: content.packs.demo_escort_pack.generator:EscortDignitaryGenerator}]
  - `generator.py`: `EscortDignitaryGenerator` implementing RouteGenerator interface
- Unit tests in `tests/unit/feature_packs/test_registry.py` and `test_loader.py`

## Out of Scope
- BalanceExperimentSpec (E63D)
- Any engine-side changes to process the new route type in the tick loop

## Acceptance Criteria
- ESCORT_DIGNITARY route type registered without modifying `src/engine/` or `src/domains/`
- Loader skips packs not in RuntimeProfile.active_pack_names
- list_all() returns canonical + pack-registered entries
- All unit tests pass

## Related Tickets
- TCK-20260619-E63B-MANIFEST-MODEL (prerequisite)
- TCK-20260619-E63D-BALANCE-PARITY (next)

## Related Docs
- `docs/architecture/feature_pack_architecture.md` (registry pattern section)

## Assumptions / Open Questions
- RouteGenerator interface must be importable from `src/domains/adventure/` without
  circular import — verify import path in E63B

## Implementation Notes
- `FeatureRegistry[T]` is generic; one instance per extension point type
- `list_all()` merges canonical enum members (via `iter(EnumClass)`) with registered pack entries
- Determinism: loader processes packs in CompatibilityResolver-sorted order only

## Test Summary
- `tests/unit/feature_packs/test_registry.py`: register/lookup/list_all round-trip, unknown key error
- `tests/unit/feature_packs/test_loader.py`: discover/load fixture, skip-inactive-pack, register-extension

## Files Changed
- `src/domains/feature_packs/registry.py` (new) — FeatureRegistry[T] generic
- `src/domains/feature_packs/loader.py` (new) — FeaturePackLoader
- `content/__init__.py` (new) — package marker
- `content/packs/__init__.py` (new) — package marker
- `content/packs/demo_escort_pack/__init__.py` (new) — package marker
- `content/packs/demo_escort_pack/manifest.yaml` (new) — demo pack manifest
- `content/packs/demo_escort_pack/generator.py` (new) — EscortDignitaryGenerator
- `tests/unit/feature_packs/test_registry.py` (new) — 9 registry tests
- `tests/unit/feature_packs/test_loader.py` (new) — 7 loader tests
- `docs/parity_ledger/infrastructure.yaml` (modified) — INFRA-PACK-001/002/003 added

## Completion Summary
FeatureRegistry[T] and FeaturePackLoader implemented. demo_escort_pack registers
ESCORT_DIGNITARY in the adventure_routing domain via manifest without touching
src/engine/ or src/domains/. list_all() merges canonical RouteFamily values with
pack-registered keys. All 30 tests pass (14 from E63B + 16 new).
