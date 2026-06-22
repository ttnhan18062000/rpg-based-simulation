---
ticket_id: TCK-20260619-E62-CULTURE-DRIFT
phase: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E62-CULTURE-DRIFT

## Scope

This is an epic-tier ticket. Tests are owned by child tickets. This plan defines
the acceptance criterion and test taxonomy for the full epic.

## Unit Test Coverage (by child ticket)

### E62A — CultureState Model
- `tests/unit/culture/test_culture_model.py`
  - `CultureState` axis clamping [0.0, 1.0]
  - `CultureCarryForward` serialization round-trip (to_dict / from_dict)
  - Blank / zero-valued state is valid

### E62B — CultureDeriver + Wiring
- `tests/unit/culture/test_culture_deriver.py`
  - Calamity event → fatalism axis increases
  - HERO entity death → hero_veneration increases
  - INFLATION_SPIRAL → resource_scarcity_memory increases
  - war_declared → faction_conflict_exposure increases
  - Events without region_id → attributed to `"__global__"` fallback key
  - Normalisation clamps at 1.0 after 3+ identical events (NORMALISE_DENOMINATOR=3.0)
  - Empty ChronicleHierarchy → all axes 0.0

### E62C — Motivation Overlay
- `tests/unit/culture/test_culture_applicator.py`
  - `compute_culture_delta` returns 0.0 when all axes below CULTURE_ACTIVATION_THRESHOLD (0.3)
  - fatalism > 0.3 → positive delta for "caution"/"recovery" tags
  - hero_veneration > 0.3 → positive delta for "loyalty"/"combat" tags
  - Delta is bounded [-0.5, 1.0]
  - `MotivationBiasService.compute_bias_multiplier` unchanged when `culture_values=None`

## Integration Acceptance Test (E62D)

**File:** `tests/integration/culture/test_culture_drift_acceptance.py`

**Test:** `test_two_regions_diverge_after_5_episodes`

**Setup:**
- Create a synthetic `CampaignState` with 5 episodes of NarrativeLedgerEntries
- Region A ("calamity region"): 5 calamity events → high fatalism
- Region B ("hero region"): 5 hero-death events → high hero_veneration
- Run `CultureDeriver.derive()` + `CulturalBiasApplicator.compute_culture_delta()`
- Compute mean `caution` tag multiplier for 10 synthetic entities per region

**Pass criterion:**
- `mean_caution_multiplier(region_A) - mean_caution_multiplier(region_B) > 0.1`
- Test must run in < 5 seconds (pure in-memory, no engine run)

## Regression Protection

- E62A model changes: any change to CultureState axes must update E62D acceptance test
- E62C bias mappings: any axis→tag mapping change must be reflected in unit tests
- E53 war event types (war_declared, territory_transferred) must remain in NarrativeLedger
  for E62B derivation to work correctly
