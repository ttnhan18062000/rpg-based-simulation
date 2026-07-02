---
ticket_id: TCK-20260619-E62-CULTURE-DRIFT
phase: investigation
date: 2026-06-22
---

# Investigation — TCK-20260619-E62-CULTURE-DRIFT

## Summary

Culture/Myth Drift (Epic 6.2) is a Phase 6 long-horizon epic that adds region-level
cultural identity derived from accumulated narrative history. Individual entity
belief/rumor mechanics already exist; this epic lifts them to the population/region
scale and feeds cultural values back into entity motivation scoring.

**Prerequisites confirmed done:** E51 (Chronicle Compiler — all 5 child tickets done
through E51E-REST-API) and E53 (Faction & Diplomacy — all 4 child epics scoped:
E53A/B/C/D). Phase 5 is complete; this is the correct time to re-evaluate E62 scope.

---

## What Exists (Re-use Inventory)

### 1. `NarrativeLedger` / `CampaignState` (src/domains/campaigns/state.py)
- `CampaignState.narrative_ledger: List[NarrativeLedgerEntry]` — already accumulates
  cross-episode events (quest_completed, entity_death, faction_shift, calamity, etc.)
- `NarrativeLedgerEntry` carries: `event_type`, `subject_id`, `payload`, `significance`,
  `episode`, `tick`
- This is the raw material for CultureState derivation. The Chronicle Compiler already
  groups and scores these. **No new event collection is needed.**

### 2. `ChronicleCompiler` / `ChronicleHierarchy` (src/domains/chronicle/)
- `ChronicleCompiler.compile()` produces a `ChronicleHierarchy` (events → incidents →
  episodes → eras) from CampaignState.narrative_ledger
- `EventSignificanceScorer` already classifies events by type + HERO bonus
- **CultureState derivation can be driven by the same ChronicleHierarchy** — no new
  event pipeline is required. CultureDeriver reads ChronicleHierarchy, not raw events.

### 3. `RegionState` (src/core/state.py:208)
- Already has: `trauma_score`, `influence`, `hazard_level`, `population_cohorts`,
  `owner_faction_id`, `stability`, `calamity_intensity`
- Pattern for adding new fields: E52A added `population_cohorts: Dict[str, Any]` with
  a `WorldUpdate.population_cohorts_set` field. Same pattern applies for
  `culture_values: Dict[str, float]`.

### 4. `WorldUpdate` (src/core/updates.py:747)
- Frozen dataclass with set-style fields + `merge()` method
- Pattern: add `culture_values_set: Optional[Dict[str, float]] = None` and handle in
  `merge()` (prefer non-None)
- Apply path: follow same path as `population_cohorts_set` (which is applied by the
  authoritative pipeline when a `StateUpdate.world_updates` entry has it set)

### 5. `IdentityDoctrine` / `MotivationModel` (src/core/cognition.py:366)
- `MotivationModel` has: `doctrine`, `values` (ValuePreferenceProfile), `role_fit`,
  `ambition`, `moral`
- `ValuePreferenceProfile` already has per-entity value scales:
  `survival`, `reward`, `knowledge`, `loyalty`, `pride`, `curiosity`, `caution`
- **Cultural overlay attaches at ValuePreferenceProfile level** — a region's culture
  shifts these scales when an entity enters or resides in the region

### 6. `MotivationBiasService` (src/domains/motivation/service.py)
- `compute_bias_multiplier(entity, tags)` already applies doctrine + values as scoring
  biases
- **Extension point:** a `CulturalBiasApplicator` can apply regional culture_values
  as additive delta to a transient MotivationModel before `compute_bias_multiplier`
  is called (not mutating durable MotivationModel — overlaying transiently)

### 7. `DoctrineResolver` (src/domains/motivation/resolver.py)
- Maps class_id → IdentityDoctrine
- Currently class-based only. Cultural overlay is NOT put here (doctrine is identity;
  culture is environment). Culture overlays the ValuePreferenceProfile transiently.

### 8. `CampaignOrchestrator._advance_state()` (src/domains/campaigns/orchestrator.py:161)
- Runs at episode boundary, already calls: entity/faction carry-forwards, narrative
  entries, social memories
- **CultureState derivation and persistence hooks here** (same pattern as social_memories)

### 9. `DemographicCycleService` (src/domains/demographics/cohort.py)
- Runs every 200 ticks. Pattern for a periodic world-update service.
- `CultureDriftService` can run on the same cadence (e.g., every 500 ticks or once
  per episode end) via the same WorldEvent + WorldUpdate mechanism

---

## What Does NOT Exist (Gap Inventory)

| Gap | Notes |
|---|---|
| `CultureState` typed model | No code anywhere; needs fresh design |
| `RegionState.culture_values` field | Not in RegionState; must be added |
| `WorldUpdate.culture_values_set` | Not in WorldUpdate; add alongside `population_cohorts_set` |
| `CultureDeriver` | Derives CultureState from ChronicleHierarchy for a region |
| `CultureDriftService` | Periodic service that calls CultureDeriver + emits WorldUpdate |
| Cultural overlay on MotivationModel | No hook for per-region cultural bias |
| `CultureRegionCarryForward` in CampaignState | No cross-episode culture persistence |
| `docs/world/culture_drift_contract.md` | Not created |
| Parity ledger entries for culture drift | `world_dynamics.yaml` has no culture entries |

---

## Architecture Decisions

### A. CultureState representation
`CultureState` is a frozen dataclass with named cultural axes (0.0–1.0):
- `fatalism` — trauma/death history → raises entity `caution`, lowers `pride`
- `hero_veneration` — legendary hero presence → raises entity `loyalty`, `pride`
- `resource_scarcity_memory` — sustained scarcity history → raises entity `survival`
- `faction_conflict_exposure` — war history → raises entity `caution`, lowers `loyalty`

These axes are derivable from existing NarrativeLedgerEntry event types:
- calamity/trauma → `fatalism`
- entity_death where HERO + high significance → `hero_veneration`
- INFLATION_SPIRAL, resource depletion events → `resource_scarcity_memory`
- war_declared, territory_transferred, faction_destroyed → `faction_conflict_exposure`

### B. Persistence: CampaignState or RegionState?
CultureState is **durable across episodes** but **derived, not authoritatively mutated
during ticks**. Two storage options:
1. `RegionState.culture_values: Dict[str, float]` + carry-forward via `WorldUpdate`
   (tick-level persistence)
2. `CampaignState.region_cultures: Dict[str, CultureCarryForward]` (episode-boundary
   persistence, analogous to social_memories)

**Decision: Option 2 (CampaignState)**. Culture drift is a long-horizon concept —
it changes over episodes, not ticks. Deriving it at tick level is wasteful and would
require per-tick WorldUpdate pollution. The Chronicle Compiler already runs at episode
end. Culture derivation runs at episode end, stores in CampaignState, and is imported
at episode start as a RegionState overlay (read-only for the tick loop).

### C. Motivation overlay injection
Cultural bias is **not baked into entity's durable MotivationModel**. Instead,
`CulturalBiasApplicator.compute_regional_overlay(entity, region, culture_state)`
returns a transient delta dict `{value_axis: float}` that `MotivationBiasService`
adds to the base bias multiplier. This preserves determinism and durable-state purity.

The hook point is `MotivationBiasService.compute_bias_multiplier()` — a second method
`compute_bias_multiplier_with_culture(entity, tags, culture_values)` is added, or
the existing method is extended with an optional `culture_values` parameter.

### D. Import path (avoiding circular imports)
Pattern from E61C progression planner: `CulturalBiasApplicator` lives in
`src/domains/motivation/` and imports `CultureState` from `src/domains/culture/`
(new domain directory). `CultureDriftService` lives in `src/domains/culture/`.
`CampaignOrchestrator` imports from `src/domains/culture/` for the exporter/importer.
Core state (`src/core/`) does not import from `src/domains/culture/`.

### E. RegionState — minimal footprint option
To keep `RegionState` clean: do NOT add a `culture_values` field to `RegionState`.
Instead the engine query layer (MotivationBiasService) accepts `culture_values` as
an explicit parameter from the caller, which looks up the current campaign's culture
map. This avoids polluting the core frozen dataclass with long-horizon derived data.

---

## Decomposition into Child Tickets

Epic 6.2 decomposes into **4 linear standard tickets**:

| Ticket | Scope | Dependency |
|---|---|---|
| E62A-CULTURE-MODEL | `CultureState` frozen model + axes + `CampaignState.region_cultures` field + serialization | none |
| E62B-CULTURE-DERIVER | `CultureDeriver` — maps ChronicleHierarchy → Dict[region_id, CultureState] + `CultureDriftExporter`/`Importer` in CampaignOrchestrator | E62A |
| E62C-MOTIVATION-OVERLAY | `CulturalBiasApplicator` + MotivationBiasService extension + `culture_drift_contract.md` | E62B |
| E62D-PARITY-VERIFY | parity ledger entries, 5-episode acceptance test, docs/world/culture_drift_contract.md update, knowledge-index-update | E62C |

Linear dependency: E62A → E62B → E62C → E62D.

---

## Risks and Open Questions

1. **Prerequisites partially scoped but not yet implemented.** E53A-D are scoped; child
   tickets exist but are not done. E62 must remain in todos until E51 + E53 child
   tickets are complete. This is correct for a Phase 6 epic.

2. **Region-id attribution.** NarrativeLedgerEntry.subject_id is an entity or faction ID,
   not a region ID. To attribute events to regions, the deriver needs to resolve
   entity→region from the chronicle data (entity_names map or region embedded in payload).
   E62B must handle missing region attribution gracefully (fallback: global culture only).

3. **MotivationBiasService call sites.** The cultural overlay must be wired at the
   right call site in the tick loop. The call site must have access to the current
   campaign's culture map. If the tick loop has no CampaignState reference, the overlay
   must be injected via config or world context. This needs verification in E62C.

4. **Acceptance test requires 5 episodes.** Test runtime may be long. E62D acceptance
   test should use a minimal world (urban_political or similar) with 50-tick episodes
   to keep CI runtime acceptable. Behavioral distribution difference must be measurable
   (e.g., mean `caution` route tag multiplier differs between regions by >10%).
