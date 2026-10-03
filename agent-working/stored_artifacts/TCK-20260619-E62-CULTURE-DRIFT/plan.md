---
ticket_id: TCK-20260619-E62-CULTURE-DRIFT
phase: plan
date: 2026-06-22
---

# Plan — TCK-20260619-E62-CULTURE-DRIFT

## Epic Goal

Over long campaigns, regional cultures develop distinct values, taboos, and myths based on
their narrative history. A region that suffered calamities develops fatalistic cultural values;
a region with legendary heroes develops a hero-cult. Cultural values influence entity behavior
through the existing motivation/doctrine system.

## Architecture Overview

```
NarrativeLedger (CampaignState)
  └─► ChronicleGrouper.group()        [reuse — E51B]
        └─► ChronicleHierarchy
              └─► CultureDeriver.derive()   [new — E62B]
                    └─► Dict[region_id, CultureState]  [new model — E62A]
                          └─► CultureDriftExporter.export()  [new — E62B]
                                └─► CampaignState.region_cultures  [new field — E62A]
                                      └─► CultureDriftImporter.get_culture()  [new — E62B]
                                            └─► CulturalBiasApplicator  [new — E62C]
                                                  └─► MotivationBiasService.compute_bias_multiplier()
                                                        [extended — E62C]
```

## Child Ticket Sequence

### E62A — CultureState Model (S effort)
**New files:** `src/domains/culture/__init__.py`, `src/domains/culture/model.py`
**Modified:** `src/domains/campaigns/state.py` (add `region_cultures` field)

Deliverables:
- `CultureState` frozen dataclass with 4 axes (fatalism, hero_veneration,
  resource_scarcity_memory, faction_conflict_exposure), all float [0.0, 1.0]
- `CultureCarryForward` (region_id, culture, derived_episode) with round-trip serialization
- `CampaignState.region_cultures: Dict[str, CultureCarryForward]` backward-compat field

### E62B — CultureDeriver + Episode Boundary Wiring (M effort)
**New files:** `src/domains/culture/deriver.py`, `src/domains/culture/exporter.py`,
  `src/domains/culture/importer.py`
**Modified:** `src/domains/campaigns/orchestrator.py` (`_advance_state()` hook)

Deliverables:
- `CultureDeriver.derive(hierarchy) -> Dict[str, CultureState]` pure stateless function
- Event→axis mapping: calamity/entity_death(trauma)→fatalism; entity_death(HERO)→hero_veneration;
  INFLATION_SPIRAL→resource_scarcity_memory; war_declared/territory_transferred/faction_destroyed→
  faction_conflict_exposure
- Normalisation: `min(1.0, raw_sum / 3.0)` per axis per region
- Global fallback key `"__global__"` when no region_id in payload
- `CultureDriftExporter.export()` called in `_advance_state()` after social_memories
- `CultureDriftImporter.get_culture(campaign_state, region_id)` thin lookup

### E62C — Cultural Bias Overlay (M effort)
**New files:** `src/domains/culture/applicator.py`,
  `docs/world/culture_drift_contract.md`
**Modified:** `src/domains/motivation/service.py`

Deliverables:
- `CulturalBiasApplicator.compute_culture_delta(culture, tags) -> float`
  — additive bounded delta [-0.5, 1.0] per tag
- Axis→tag mappings (thresholded at 0.3 activation):
  - fatalism → +caution/recovery/flee, -pride/combat/aggressive
  - hero_veneration → +loyalty/party/combat
  - resource_scarcity_memory → +survival/recovery/caution
  - faction_conflict_exposure → +caution, -loyalty
- `MotivationBiasService.compute_bias_multiplier(entity, tags, culture_values=None)`
  backward-compat extension
- `docs/world/culture_drift_contract.md` stub finalized here

### E62D — Parity + Acceptance Test + Docs (S effort)
**New files:** `tests/integration/culture/test_culture_drift_acceptance.py`
**Modified:** `docs/parity_ledger/world_dynamics.yaml`,
  `docs/mechanics/05_world_evolution.md`,
  `docs/world/culture_drift_contract.md`

Deliverables:
- WORLD-CULT-001/002/003 parity entries (all P1, status: verified)
- `test_two_regions_diverge_after_5_episodes` integration test (synthetic data, <5s)
- Section 7 "Cultural Drift" in 05_world_evolution.md
- `make knowledge-index-update`

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| CultureState storage | CampaignState (episode boundary) | Culture changes over episodes, not ticks; avoids WorldUpdate pollution |
| Overlay mechanism | Transient additive delta | Preserves durable-state purity; MotivationModel not mutated |
| Derivation source | ChronicleHierarchy (reuse ChronicleGrouper) | No new event pipeline needed; already scored and grouped |
| Region attribution | `payload.get("region_id")` with `"__global__"` fallback | Graceful degradation when events lack region context |
| New domain dir | `src/domains/culture/` | Avoids circular imports; pure domain logic |

## Dependency Constraints

- E62A has no code prerequisites (pure data model + CampaignState field)
- E62B requires E62A (CultureState/CultureCarryForward types)
- E62C requires E62B (CultureState available via Importer)
- E62D requires E62A+B+C complete
- ALL E62 tickets require E53 child tickets to be implemented (war_declared etc. in NarrativeLedger)

## Tuning Constants (module-level, adjustable)

| Constant | Value | Location | Meaning |
|---|---|---|---|
| `NORMALISE_DENOMINATOR` | 3.0 | `deriver.py` | 3 high-sig events saturate an axis |
| `CULTURE_ACTIVATION_THRESHOLD` | 0.3 | `applicator.py` | Axis must exceed 0.3 to apply bias |

## Risk Register

| Risk | Mitigation |
|---|---|
| Region attribution missing from NarrativeLedgerEntry payload | `"__global__"` fallback; E62B handles gracefully |
| MotivationBiasService call site lacks CampaignState in scope | Optional `culture_values=None` param; overlay skipped if unavailable |
| Acceptance test runtime too slow | Synthetic ledger (no engine run); 50-tick episodes if live run needed |
| E53 child tickets not yet implemented when E62 starts | E62A can start (data model only); E62B/C/D must wait for E53 war events |
