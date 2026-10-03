---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E62A-CULTURE-MODEL
phase: done
date: 2026-06-22
tags: [culture-drift, model, campaign-state, phase-6]
---

# TCK-20260619-E62A-CULTURE-MODEL

## Title
Epic 6.2A · CultureState Model + CampaignState Field

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Define `CultureState` as a frozen dataclass encoding the four regional cultural axes
(fatalism, hero_veneration, resource_scarcity_memory, faction_conflict_exposure) and
add `region_cultures: Dict[str, CultureCarryForward]` to `CampaignState` with full
serialization/deserialization support.

## Scope
- New file `src/domains/culture/__init__.py` and `src/domains/culture/model.py`
- `CultureState` frozen dataclass with four float axes (0.0–1.0):
  - `fatalism` — derived from calamity + high-trauma history
  - `hero_veneration` — derived from HERO entity deaths of high significance
  - `resource_scarcity_memory` — derived from INFLATION_SPIRAL + sustained depletion events
  - `faction_conflict_exposure` — derived from war_declared + territory_transferred + faction_destroyed
- `CultureCarryForward` frozen dataclass: `region_id: str`, `culture: CultureState`,
  `derived_episode: int` (which episode this was last derived in)
- `CultureCarryForward.to_dict()` / `from_dict()` following the pattern of
  `SocialMemoryRecord` / `FactionSocialMemory` in `src/domains/campaigns/social_memory.py`
- Add `region_cultures: Dict[str, CultureCarryForward]` field to `CampaignState`
  (default `field(default_factory=dict)`)
- Extend `CampaignState.to_dict()` and `CampaignState.from_dict()` to serialize/
  deserialize `region_cultures` (str key → CultureCarryForward dict, sorted for determinism)

## Out of Scope
- Derivation logic (E62B)
- Any MotivationModel integration (E62C)
- Parity ledger updates (E62D)
- Adding `culture_values` field to `RegionState` or `WorldUpdate` — culture
  persistence is in CampaignState, not in the tick-level state

## Acceptance Criteria
1. `CultureState` is importable from `src.domains.culture.model` with all four axes
2. `CultureCarryForward.to_dict()` round-trips through `from_dict()` without data loss
3. `CampaignState` with `region_cultures` populated serializes and deserializes
   correctly via `to_dict()` / `from_dict()`
4. All existing campaign state tests pass unmodified (backward-compatible: missing
   `region_cultures` key in `from_dict()` defaults to empty dict)

## Related Tickets
- TCK-20260619-E62-CULTURE-DRIFT (parent epic)
- TCK-20260619-E62B-CULTURE-DERIVER (next — depends on this)
- TCK-20260619-E51-CHRONICLE (prerequisite — chronicle pipeline this builds on)
- TCK-20260619-E53-FACTION-DIPLOMACY (prerequisite — provides faction event types)

## Related Docs
- `docs/plans/long_term_development_roadmap.md` § Epic 6.2
- `docs/plans/engine_future_epics_roadmap.md` § A (Culture/Myth Drift)
- `docs/simulation/domains/belief_and_detour_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/investigation.md`

## Related Code Areas
- `src/domains/campaigns/state.py` — CampaignState, add `region_cultures` field
- `src/domains/campaigns/social_memory.py` — reference pattern for CultureCarryForward
- `src/core/strategic.py` — MotivationModel/ValuePreferenceProfile (read-only for context)

## Assumptions / Open Questions
- Four axes chosen based on existing NarrativeLedgerEntry event types; additional axes
  can be added in future without breaking serialization (just add new optional fields)
- Float axes clamped to [0.0, 1.0]; default 0.0 means "no cultural signal yet"
- `derived_episode` tracks staleness; if a region has no events in an episode the
  carry-forward entry from the previous episode persists unchanged

## Implementation Notes
- Place in `src/domains/culture/` (new domain); avoid circular imports — model.py
  must NOT import from `src/engine/` or `src/core/state.py`
- `CultureState` is frozen + slots=True for consistency with other domain models
- Follow exact pattern of `SocialMemoryRecord.to_dict()` / `from_dict()` for
  `CultureCarryForward` serialization
- `CampaignState.from_dict()` must tolerate missing `region_cultures` key
  (backward-compat for checkpoints written before E62A)

## Test Summary
- `tests/unit/culture/test_culture_model.py` (new file):
  - `test_culture_state_default_axes` — all four axes default to 0.0
  - `test_culture_carry_forward_round_trip` — to_dict → from_dict identity
  - `test_campaign_state_region_cultures_serialization` — CampaignState with
    two populated CultureCarryForward entries round-trips
  - `test_campaign_state_backward_compat` — `from_dict()` with no `region_cultures`
    key produces empty dict (not KeyError)
- Existing `tests/unit/campaigns/test_campaign_state.py` must pass unmodified

## Files Changed
- `src/domains/culture/__init__.py` (new)
- `src/domains/culture/model.py` (new — CultureState, CultureCarryForward)
- `src/domains/campaigns/state.py` (modified — import + region_cultures field + serialization)
- `tests/unit/culture/__init__.py` (new)
- `tests/unit/culture/test_culture_model.py` (new — 5 tests)

## Completion Summary
CultureState (4 axes, frozen+slots) and CultureCarryForward defined in new
src/domains/culture/ domain. CampaignState.region_cultures field added with
full to_dict/from_dict round-trip. 22 tests pass (5 new + 17 existing).
