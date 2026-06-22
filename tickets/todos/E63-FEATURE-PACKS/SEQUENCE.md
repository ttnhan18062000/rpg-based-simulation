# E63 — Pluggable Feature Pack Architecture

**Parent epic:** TCK-20260619-E63-FEATURE-PACKS (EPIC_SCOPED)
**Inter-epic prerequisites:**
- E53 fully implemented (faction extension pattern proven at scale)
- E61 + E62 implemented (Phase 6 sequencing — E63 is XL effort, last)
- Decision gate: ≥3 independent features proven via `adventure_routing_contract.md` and `world_emergence_contract.md` extension patterns

## Sequence (linear, gate-blocked)

1. **TCK-20260619-E63A-GATE-VERIFY** ⚠️ **BLOCKED** — Formally verify the decision gate; write gate memo to stored_artifacts; create `docs/architecture/feature_pack_architecture.md` (FeaturePackManifest YAML schema, RuntimeProfile contract, CompatibilityResolver contract, FeatureRegistry dict-based pattern rationale)
   - **Do not start until E53 child tickets are implemented and gate is re-evaluated**
2. **TCK-20260619-E63B-MANIFEST-MODEL** — `FeaturePackManifest` Pydantic model + `RuntimeProfile` frozen dataclass + `CompatibilityResolver.resolve()` (topological sort, circular dep detection, missing-pack error); `SimulationScenarioDefinition.runtime_profile` extension
3. **TCK-20260619-E63C-REGISTRY-LOADER** — `FeatureRegistry[T]` generic dict-based (register/lookup/list_all); `FeaturePackLoader.load(profile, manifest_dir)`; `demo_escort_pack` adds ESCORT_DIGNITARY RouteFamily without modifying any file in `src/engine/` or `src/domains/`
4. **TCK-20260619-E63D-BALANCE-PARITY** — `BalanceExperimentSpec` Pydantic model + `BalanceExperimentRunner.run()`; integration acceptance test; INFRA-PACK-001/002/003 parity entries; finalize `docs/architecture/feature_pack_architecture.md`; `make knowledge-index-update`

## Key Notes

- Python enums are closed — `FeatureRegistry[T]` is a **dict-based** registry. Existing canonical enum members (RouteFamily, WorldEventCategory etc.) remain as IDs; packs register additional entries alongside them.
- New domain: `src/domains/feature_packs/` — no circular imports with engine.
- `CompatibilityResolver` uses Kahn's algorithm for deterministic topological sort.
- `BalanceExperimentRunner` is pure — accepts a precomputed metric snapshot dict, not live engine state.

## Decision Gate Assessment (at scoping time)

- Adventure routing: 4 route families proven (EXPLORE, TRADE, PROTECT_TARGET, OWN_SURVIVAL)
- World emergence: 3 event types proven (POPULATION_BIRTH, POPULATION_DEATH, POPULATION_MIGRATION)
- Numerically satisfied, but E53 faction directive/diplomacy extensions must also be complete before generalizing.
