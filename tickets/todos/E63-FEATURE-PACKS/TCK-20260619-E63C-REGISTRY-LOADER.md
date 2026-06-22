---
status: open
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E63C-REGISTRY-LOADER
phase: open
date: 2026-06-22
tags: [feature-packs, registry, loader, demo-pack, phase-6]
---

# TCK-20260619-E63C-REGISTRY-LOADER

## Title
Epic 6.3C · FeatureRegistry + FeaturePackLoader + Demo Pack

## Status
OPEN

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
_To be filled on completion._

## Completion Summary
_To be filled on completion._
