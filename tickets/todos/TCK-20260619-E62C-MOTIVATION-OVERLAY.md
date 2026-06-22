---
status: open
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E62C-MOTIVATION-OVERLAY
phase: open
date: 2026-06-22
tags: [culture-drift, motivation, doctrine, bias, phase-6]
---

# TCK-20260619-E62C-MOTIVATION-OVERLAY

## Title
Epic 6.2C · Cultural Bias Overlay on MotivationBiasService

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement `CulturalBiasApplicator` that translates a `CultureState` into additive
tag-level bias deltas, and extend `MotivationBiasService.compute_bias_multiplier()`
to accept an optional `culture_values` parameter that applies those deltas. Wire the
applicator into the adventure scoring call site so entities in culturally distinct
regions receive measurably different motivation multipliers.

## Scope
- New `src/domains/culture/applicator.py`:
  - `CulturalBiasApplicator` stateless class
  - `compute_culture_delta(culture: CultureState, tags: Iterable[str]) -> float`
    — additive delta to layered onto `compute_bias_multiplier` result:
      - `fatalism` > 0.3 → `+culture.fatalism * 0.4` for tags in {`caution`, `recovery`, `flee`}
      - `fatalism` > 0.3 → `-culture.fatalism * 0.3` for tags in {`pride`, `combat`, `aggressive`}
      - `hero_veneration` > 0.3 → `+culture.hero_veneration * 0.4` for tags in {`loyalty`, `party`, `combat`}
      - `resource_scarcity_memory` > 0.3 → `+culture.resource_scarcity_memory * 0.4`
        for tags in {`survival`, `recovery`, `caution`}
      - `faction_conflict_exposure` > 0.3 → `+culture.faction_conflict_exposure * 0.3`
        for tags in {`caution`}; `-0.2` for tags in {`loyalty`}
    - Final: `max(-0.5, min(1.0, delta))` (bounded additive delta, not a replacement)
- Extend `MotivationBiasService.compute_bias_multiplier()` with optional third arg
  `culture_values: CultureState | None = None`:
  - If provided: compute `culture_delta = CulturalBiasApplicator.compute_culture_delta(culture_values, tags)`
    and add to the base multiplier before returning
  - Signature: `compute_bias_multiplier(entity, tags, culture_values=None) -> float`
  - All existing call sites (no `culture_values` arg) continue to work unmodified
- Wire in the adventure route scoring path:
  - Locate call site for `MotivationBiasService.compute_bias_multiplier()` in
    `src/systems/` or `src/domains/adventure/` (verify actual call site in E62C)
  - At that call site, look up `CultureDriftImporter.get_culture(campaign_state, entity_region_id)`
    and pass result as `culture_values`; if no campaign_state available in scope,
    pass `None` (overlay is optional, not required for base function)
- Create `docs/world/culture_drift_contract.md` — design contract for Culture/Myth
  Drift system (axes, derivation rules, overlay mechanism, acceptance signal)

## Out of Scope
- Changing durable `MotivationModel` or `ValuePreferenceProfile` on entities
  (overlay is transient per route scoring call, not stored)
- Adding `culture_values` to `RegionState` or `WorldUpdate`
- Parity ledger (E62D)

## Acceptance Criteria
1. `CulturalBiasApplicator.compute_culture_delta()` returns a positive delta for
   `caution` tag when `culture.fatalism = 0.8`
2. `CulturalBiasApplicator.compute_culture_delta()` returns zero delta for any tag
   when all culture axes are 0.0 (no cultural signal)
3. `MotivationBiasService.compute_bias_multiplier(entity, tags)` (no culture_values)
   produces identical result to pre-E62C behaviour (regression-safe)
4. `MotivationBiasService.compute_bias_multiplier(entity, tags, culture_values)` with
   `culture_values.fatalism=0.8` produces a strictly higher multiplier for `caution`
   tag than the same call with `culture_values=None`
5. `docs/world/culture_drift_contract.md` exists and covers all four axes plus
   the overlay mechanism

## Related Tickets
- TCK-20260619-E62B-CULTURE-DERIVER (prerequisite — CultureState + Importer)
- TCK-20260619-E62D-PARITY-VERIFY (next — parity + acceptance test)
- TCK-20260619-E62A-CULTURE-MODEL (prerequisite — CultureState model)

## Related Docs
- `docs/plans/long_term_development_roadmap.md` § Epic 6.2
- `docs/mechanics/04_strategic_cognition.md` — motivation scoring context
- `docs/simulation/domains/belief_and_detour_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/investigation.md`

## Related Code Areas
- `src/domains/motivation/service.py` — MotivationBiasService (extend here)
- `src/domains/motivation/resolver.py` — DoctrineResolver (read-only, no change)
- `src/core/cognition.py` — MotivationModel / ValuePreferenceProfile (read-only)
- `src/domains/culture/applicator.py` (new)
- `docs/world/culture_drift_contract.md` (new)

## Assumptions / Open Questions
- Wiring call site must be identified during E62C implementation by tracing
  `MotivationBiasService.compute_bias_multiplier` call sites via grep. If call site
  is inside `src/engine/` kernel phases, passing `campaign_state` may require a
  context injection pattern (see how `CognitionProfile` is passed in strategic.py).
- If no call site exists in the current tick loop that has access to both entity
  region and campaign state simultaneously, the overlay can be deferred to a
  thin wrapper called from `AdventureRouteScorer` (which already scores per-entity
  per-tick with entity context)
- Threshold 0.3 for axis activation is a tuning parameter; defined as a module-level
  constant `CULTURE_ACTIVATION_THRESHOLD = 0.3` for easy adjustment

## Implementation Notes
- `CulturalBiasApplicator` must NOT import from `src.engine.*` or `src.core.state`
  (same purity constraint as `MotivationBiasService`)
- `compute_bias_multiplier()` signature change is backward-compatible (optional param)
- The culture delta is additive to the final multiplier (not multiplicative) to avoid
  exponential compounding with existing doctrine + values biases
- `docs/world/culture_drift_contract.md` should document:
  - Four axes and their derivation sources
  - Overlay mechanism (additive delta, bounded, transient)
  - Acceptance signal (two regions measurably different in episode 5)
  - Integration points (CultureDeriver, CultureDriftExporter, CulturalBiasApplicator)
  - Run `make knowledge-index-update` after creating the doc

## Test Summary
- `tests/unit/culture/test_culture_applicator.py`:
  - `test_zero_culture_produces_zero_delta`
  - `test_high_fatalism_increases_caution_delta`
  - `test_high_fatalism_decreases_combat_delta`
  - `test_high_hero_veneration_increases_loyalty_delta`
  - `test_high_scarcity_memory_increases_survival_delta`
  - `test_high_conflict_exposure_increases_caution_delta`
  - `test_delta_bounded_between_minus_0_5_and_1_0`
- `tests/unit/world/test_motivation_pressure_resolver.py` or a new
  `tests/unit/motivation/test_motivation_bias_service.py`:
  - `test_compute_bias_multiplier_no_culture_unchanged` (regression)
  - `test_compute_bias_multiplier_with_culture_fatalism`
  - `test_compute_bias_multiplier_with_culture_zero_axes_unchanged`

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
