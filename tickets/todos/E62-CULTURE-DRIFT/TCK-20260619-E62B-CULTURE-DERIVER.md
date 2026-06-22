---
status: open
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E62B-CULTURE-DERIVER
phase: open
date: 2026-06-22
tags: [culture-drift, chronicle, deriver, exporter, importer, phase-6]
---

# TCK-20260619-E62B-CULTURE-DERIVER

## Title
Epic 6.2B · CultureDeriver + Episode-Boundary Exporter/Importer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement `CultureDeriver` which reads a `ChronicleHierarchy` and produces a
`Dict[str, CultureState]` mapping region_id → derived cultural values. Wire this
into `CampaignOrchestrator._advance_state()` via `CultureDriftExporter` (reads
hierarchy, derives, stores in CampaignState) and `CultureDriftImporter` (provides
the culture map at episode start for downstream use).

## Scope
- New `src/domains/culture/deriver.py`:
  - `CultureDeriver` stateless class, one public method:
    `derive(hierarchy: ChronicleHierarchy, entity_names: dict[int,str] | None) -> Dict[str, CultureState]`
  - Attribution logic: event `subject_id` is an entity/faction id string;
    derive region affiliation from `entry.payload.get("region_id")` if present,
    otherwise accumulate into a `"global"` fallback key
  - Axis derivation rules (all additive across entries, then normalise to [0.0, 1.0]):
    - `fatalism` += `entry.significance` for event_type in {`calamity`, `entity_death`
      where `entry.payload.get("cause") == "calamity"` or trauma-related}
    - `hero_veneration` += `entry.significance` for `entity_death` where
      `entry.payload.get("entity_role") == "HERO"`
    - `resource_scarcity_memory` += `entry.significance` for event_type in
      {`INFLATION_SPIRAL`}
    - `faction_conflict_exposure` += `entry.significance` for event_type in
      {`war_declared`, `territory_transferred`, `faction_destroyed`}
  - Normalisation: each axis = `min(1.0, raw_sum / NORMALISE_DENOMINATOR)` where
    `NORMALISE_DENOMINATOR = 3.0` (tunable constant — 3 high-significance events
    saturates an axis)
- New `src/domains/culture/exporter.py`:
  - `CultureDriftExporter.export(campaign_state, hierarchy, episode_index, entity_names)
    -> None` — calls `CultureDeriver.derive()`, wraps each entry as
    `CultureCarryForward(region_id, culture, derived_episode)`, updates
    `campaign_state.region_cultures`
- New `src/domains/culture/importer.py`:
  - `CultureDriftImporter.get_culture(campaign_state, region_id) -> CultureState | None`
    — thin lookup: `campaign_state.region_cultures.get(region_id)?.culture`
- Wire `CultureDriftExporter.export()` into `CampaignOrchestrator._advance_state()`
  after existing extractions. `ChronicleCompiler` is already called optionally by
  callers; `_advance_state()` must call `ChronicleGrouper.group(narrative_ledger)` to
  get a hierarchy without writing files (pure grouping step is side-effect-free)

## Out of Scope
- MotivationModel wiring (E62C)
- Parity ledger (E62D)
- Real-time per-tick culture derivation — culture derives only at episode boundary

## Acceptance Criteria
1. `CultureDeriver.derive()` on a ChronicleHierarchy containing one `calamity` event
   with significance=0.85 produces a CultureState with `fatalism > 0.0` and other
   axes = 0.0
2. `CultureDeriver.derive()` on a hierarchy with 3 `war_declared` events of
   significance=0.9 produces `faction_conflict_exposure >= 0.9` (saturated at 1.0
   after normalisation)
3. `CultureDriftExporter.export()` populates `campaign_state.region_cultures` after
   a 2-episode run; the map survives `to_dict()` / `from_dict()` round-trip
4. `CultureDriftImporter.get_culture()` returns `None` for a region with no events
   (does not raise)
5. `CampaignOrchestrator._advance_state()` calls `CultureDriftExporter.export()`
   without error when `narrative_ledger` is empty

## Related Tickets
- TCK-20260619-E62A-CULTURE-MODEL (prerequisite — CultureState model)
- TCK-20260619-E62C-MOTIVATION-OVERLAY (next — consumes importer output)
- TCK-20260619-E51B-GROUPER (ChronicleGrouper.group() is reused here)
- TCK-20260619-E51A-SIGNIFICANCE (EventSignificanceScorer precedent)

## Related Docs
- `docs/plans/long_term_development_roadmap.md` § Epic 6.2
- `stored_artifacts/TCK-20260619-E51B-GROUPER/` — ChronicleGrouper contract

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/investigation.md`

## Related Code Areas
- `src/domains/chronicle/grouper.py` — ChronicleGrouper.group() reused
- `src/domains/chronicle/significance.py` — EventSignificanceScorer precedent
- `src/domains/campaigns/orchestrator.py` — _advance_state() wiring point
- `src/domains/campaigns/state.py` — CampaignState.region_cultures

## Assumptions / Open Questions
- `NORMALISE_DENOMINATOR = 3.0`: three high-significance events saturate an axis.
  This constant is defined at module level for tunability.
- Region attribution falls back to `"global"` when no `region_id` in payload; the
  global entry is stored under key `"__global__"` and serves as the fallback for
  any region not explicitly found
- `ChronicleGrouper.group()` is already available and pure — calling it a second
  time at episode boundary (after it may have been called by a compile() step) is
  safe (idempotent, no side effects)
- CampaignOrchestrator imports `ChronicleGrouper` from `src.domains.chronicle.grouper`
  — this import is already valid per the dependency graph

## Implementation Notes
- `CultureDeriver` must be fully stateless (no __init__ state). One class method.
- The `_advance_state()` wiring: after `self._state.social_memories.update(...)`,
  add:
  ```python
  # E62B: derive and persist culture drift
  from src.domains.culture.exporter import CultureDriftExporter
  from src.domains.chronicle.grouper import ChronicleGrouper
  hierarchy = ChronicleGrouper().group(list(self._state.narrative_ledger))
  CultureDriftExporter.export(self._state, hierarchy, summary.episode_index)
  ```
  Import is inside the method to avoid circular import risk (matching E32D pattern).
- Do NOT call `ChronicleCompiler.compile()` here — only `ChronicleGrouper.group()`.
  File writing is a separate concern.

## Test Summary
- `tests/unit/culture/test_culture_deriver.py`:
  - `test_deriver_calamity_raises_fatalism`
  - `test_deriver_hero_death_raises_hero_veneration`
  - `test_deriver_inflation_raises_scarcity_memory`
  - `test_deriver_war_events_raise_conflict_exposure`
  - `test_deriver_saturation_clamps_at_1_0`
  - `test_deriver_empty_hierarchy_returns_zero_culture`
  - `test_deriver_unknown_event_type_no_effect`
  - `test_deriver_global_fallback_when_no_region_in_payload`
- `tests/unit/culture/test_culture_exporter.py`:
  - `test_exporter_populates_region_cultures`
  - `test_exporter_persists_across_episodes` (accumulates; later episode overwrites)
  - `test_importer_returns_none_for_unknown_region`
- Integration: `tests/unit/campaigns/test_campaign_orchestrator.py` —
  existing tests must pass; add `test_advance_state_runs_culture_exporter`

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
