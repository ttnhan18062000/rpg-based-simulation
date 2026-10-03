---
ticket_id: TCK-20260619-E63-FEATURE-PACKS
phase: plan
date: 2026-06-22
---

# Plan — TCK-20260619-E63-FEATURE-PACKS

## Decision Gate

**GATE NOT FULLY CLEARED.** Do not begin E63A–D implementation until:
1. E53A–D child tickets are implemented (faction extension pattern proven at scale)
2. Explicit re-evaluation confirms ≥3 independent code-level extension additions
3. E61 and E62 are implemented (Phase 6 sequencing — E63 is XL effort, last)

## Epic Goal

Generalize the `enum → generator → scorer → mapper → tests` extension pattern into a
self-describing manifest system so new quest types / world behaviors can be added by
dropping in a YAML manifest + Python module without touching `src/engine/` or `src/domains/`.

## Architecture Overview

```
FeaturePackManifest (YAML + Python module entry points)
  └─► CompatibilityResolver.resolve(active_packs)
        └─► sorted load order (dependency-aware)
              └─► pack module registered into:
                    ├─ RouteFamily registry (dict-based, replaces enum for new entries)
                    ├─ WorldEventCategory registry
                    ├─ GoalKind registry
                    └─ (other registries as discovered)

RuntimeProfile
  └─► selects which packs are active per simulation run
        └─► stored in SimulationScenarioDefinition

BalanceExperimentSpec (YAML)
  └─► declarative: which metric, which baseline, which threshold
        └─► CI-runnable without engine changes
```

## Child Ticket Sequence

### E63A — Gate Verify + Registry Architecture (S effort)
**BLOCKED:** Must not start until gate condition is re-evaluated.

**New files:** `docs/architecture/feature_pack_architecture.md`
**Modified:** `docs/simulation/domains/adventure_routing_contract.md` (add registry note)

Deliverables:
- Formal decision gate verification report (written to stored_artifacts)
- Registry pattern design: `FeatureRegistry[T]` — dict-based, replaces closed enums
  for packs. Existing enum members remain as canonical IDs.
- `docs/architecture/feature_pack_architecture.md` — FeaturePackManifest YAML schema,
  RuntimeProfile contract, CompatibilityResolver contract

### E63B — FeaturePackManifest + RuntimeProfile Models (M effort)
**Prerequisite:** E63A

**New files:** `src/domains/feature_packs/__init__.py`, `src/domains/feature_packs/manifest.py`,
  `src/domains/feature_packs/profile.py`

Deliverables:
- `FeaturePackManifest` Pydantic model: name, version, requires (list), extension_points
  (list of domain+class pairs), balance_specs (list)
- `RuntimeProfile` dataclass: active_pack_names: List[str]
- `CompatibilityResolver.resolve(manifests)` → sorted list (topological sort on dependencies)
- `SimulationScenarioDefinition` extended with `runtime_profile: Optional[RuntimeProfile]`

### E63C — Registry Integration + First Feature Pack (L effort)
**Prerequisite:** E63B

**New files:** `src/domains/feature_packs/registry.py`, `src/domains/feature_packs/loader.py`,
  example pack `content/packs/demo_escort_pack/`

Deliverables:
- `FeatureRegistry[T]` generic dict-based registry with `register()` / `lookup()` / `list_all()`
- `FeaturePackLoader.load(profile, manifest_dir)` — discovers manifests, calls CompatibilityResolver,
  imports Python module entry points, registers extensions
- Demo: `demo_escort_pack` adds a new RouteFamily (ESCORT_DIGNITARY) via manifest without
  modifying RouteFamily enum in src/
- Acceptance criterion: new quest type added without touching any file in `src/engine/` or `src/domains/`

### E63D — BalanceExperimentSpec + Parity + Docs (M effort)
**Prerequisite:** E63C

**New files:** `src/domains/feature_packs/balance_spec.py`,
  `tests/integration/feature_packs/test_demo_escort_pack.py`,
  `docs/parity_ledger/infrastructure.yaml` additions

Deliverables:
- `BalanceExperimentSpec` Pydantic model: metric_path, baseline_pack, threshold, tolerance
- `BalanceExperimentRunner.run(spec, scenario)` — pure evaluation (no new test framework)
- Parity entries INFRA-PACK-001/002/003 in infrastructure.yaml
- Section "Feature Pack Loading" in `docs/architecture/feature_pack_architecture.md`
- `make knowledge-index-update`

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Registry pattern | Dict-based (not enum extension) | Python enums are closed; dict allows dynamic registration by packs |
| Manifest discovery | Directory scan at boot | Simple, no runtime overhead; packs declared at scenario definition time |
| Existing enum members | Stay as canonical IDs in core | Avoids breaking all existing code; packs add on top |
| BalanceExperimentSpec | Pure declarative YAML | Keeps it simple — no new test framework, just a data spec for the runner |
| New domain dir | `src/domains/feature_packs/` | Clean separation, no circular imports with engine |

## Dependency Constraints

- E63A requires: gate verification (E53 implemented, ≥3 extension additions confirmed)
- E63B requires E63A (architecture doc defines the contracts)
- E63C requires E63B (models defined before loader can reference them)
- E63D requires E63C (demo pack must exist for the acceptance test)
- Linear: E63A → E63B → E63C → E63D
