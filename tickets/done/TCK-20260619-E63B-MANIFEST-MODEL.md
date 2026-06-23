---
status: open
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E63B-MANIFEST-MODEL
phase: open
date: 2026-06-22
tags: [feature-packs, manifest, runtime-profile, compatibility-resolver, phase-6]
---

# TCK-20260619-E63B-MANIFEST-MODEL

## Title
Epic 6.3B · FeaturePackManifest + RuntimeProfile + CompatibilityResolver Models

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement the core data models for the pluggable feature pack system:
`FeaturePackManifest` (Pydantic), `RuntimeProfile` (dataclass), and
`CompatibilityResolver` (topological sort + conflict detection).

## Scope
- `src/domains/feature_packs/__init__.py`
- `src/domains/feature_packs/manifest.py`: `FeaturePackManifest` Pydantic model
  (name: str, version: str, requires: List[str], extension_points: List[ExtensionPoint],
  balance_specs: List[str])
- `src/domains/feature_packs/profile.py`: `RuntimeProfile` frozen dataclass
  (active_pack_names: List[str])
- `src/domains/feature_packs/resolver.py`: `CompatibilityResolver.resolve(manifests)`
  → sorted list; raises on circular dependency or missing required pack
- Extend `src/scenarios/schema.py`: `SimulationScenarioDefinition.runtime_profile:
  Optional[RuntimeProfile] = None`
- Unit tests in `tests/unit/feature_packs/test_manifest.py`

## Out of Scope
- Pack loading / registry (E63C)
- Balance experiment runner (E63D)

## Acceptance Criteria
- Valid manifest YAML round-trips to FeaturePackManifest and back
- CompatibilityResolver sorts a 3-pack chain correctly
- CompatibilityResolver raises on circular dependency and missing required pack
- All tests pass

## Related Tickets
- TCK-20260619-E63A-GATE-VERIFY (prerequisite)
- TCK-20260619-E63C-REGISTRY-LOADER (next)

## Related Docs
- `docs/architecture/feature_pack_architecture.md` (created by E63A)

## Assumptions / Open Questions
- `ExtensionPoint` schema: `{domain: str, class_path: str}` — sufficient for loader

## Implementation Notes
- New domain: `src/domains/feature_packs/`. No circular imports with engine.
- CompatibilityResolver uses Kahn's algorithm for topological sort (deterministic).

## Test Summary
- `tests/unit/feature_packs/test_manifest.py`: round-trip, defaults, resolver sorting,
  resolver circular dependency error, resolver missing-pack error

## Files Changed
- `src/domains/feature_packs/__init__.py` (new)
- `src/domains/feature_packs/manifest.py` (new — FeaturePackManifest, ExtensionPoint, CompatibilityResolver)
- `src/domains/feature_packs/profile.py` (new — RuntimeProfile)
- `src/scenarios/schema.py` (modified — runtime_profile Optional[RuntimeProfile] field)
- `tests/unit/feature_packs/__init__.py` (new)
- `tests/unit/feature_packs/test_manifest.py` (new — 14 tests)

## Completion Summary
FeaturePackManifest Pydantic model with YAML round-trip. RuntimeProfile for active pack
selection. CompatibilityResolver with Kahn's BFS topological sort, conflict detection, and
cycle detection. SimulationScenarioDefinition extended with optional runtime_profile.
63 tests pass (14 new + 49 existing scenario tests).
