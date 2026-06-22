# E62 — Culture / Myth Drift

**Parent epic:** TCK-20260619-E62-CULTURE-DRIFT (EPIC_SCOPED)
**Inter-epic prerequisites:**
- E51 (Chronicle Compiler) — complete (E51A–E51E all done)
- E53 (Faction Diplomacy) — all child epics must be implemented (war/diplomacy events needed by E62B)
- E61 (Progression Planner) — recommended complete before E62 starts (Phase 6 sequencing)

## Sequence (linear)

1. **TCK-20260619-E62A-CULTURE-MODEL** — `CultureState` frozen dataclass with 4 axes (fatalism, hero_veneration, resource_scarcity_memory, faction_conflict_exposure), all float [0.0, 1.0]; `CultureCarryForward` (region_id, culture, derived_episode) with round-trip serialization; `CampaignState.region_cultures: Dict[str, CultureCarryForward]` field
2. **TCK-20260619-E62B-CULTURE-DERIVER** — `CultureDeriver.derive(hierarchy) -> Dict[str, CultureState]` pure stateless; event→axis mapping (calamity→fatalism, HERO death→hero_veneration, INFLATION_SPIRAL→resource_scarcity_memory, war events→faction_conflict_exposure); normalisation `min(1.0, raw / 3.0)`; `"__global__"` fallback for events lacking region_id; `CultureDriftExporter`/`Importer` wired into `CampaignOrchestrator._advance_state()`
3. **TCK-20260619-E62C-MOTIVATION-OVERLAY** — `CulturalBiasApplicator.compute_culture_delta(culture, tags) -> float` (additive, bounded [-0.5, 1.0]); axis→tag mappings thresholded at 0.3; `MotivationBiasService.compute_bias_multiplier(entity, tags, culture_values=None)` backward-compat extension; `docs/world/culture_drift_contract.md`
4. **TCK-20260619-E62D-PARITY-VERIFY** — parity entries WORLD-CULT-001/002/003 in `world_dynamics.yaml`; `test_two_regions_diverge_after_5_episodes` integration test (synthetic ledger, <5s); Section 7 "Cultural Drift" in `docs/mechanics/05_world_evolution.md`; `make knowledge-index-update`

## Key Notes

- `CultureState` lives in `CampaignState` (episode-boundary), NOT in `RegionState` (tick-level). Culture changes over episodes, not ticks.
- Cultural overlay is **transient** — never baked into the durable `MotivationModel`. Determinism and durable-state purity preserved.
- New domain: `src/domains/culture/` — no circular imports with `src/core/` or `src/engine/`.
- Tuning constants: `NORMALISE_DENOMINATOR = 3.0`, `CULTURE_ACTIVATION_THRESHOLD = 0.3`.
