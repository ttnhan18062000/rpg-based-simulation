---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260905-DRIFTING-LOYALTY-SIGNAL
artifact_type: test_plan
date: 2026-09-05
tags: [world, faction]
---

# Test Plan — TCK-20260905-DRIFTING-LOYALTY-SIGNAL

## Regression Surface (existing tests that must pass)

- `tests/unit/social/test_party_lifecycle.py` (existing `effective_defection_threshold`/`check_defection`
  tests — must still pass with the new optional parameter defaulting to no-op).
- `tests/unit/domains/culture/test_culture_exporter.py` (existing `CultureDriftImporter.get_culture()`
  tests — untouched, but re-run to confirm no accidental coupling).
- `tests/architecture/` (existing write-path guard tests — confirm no new violation).

## New Tests Required (per AC)

1. `LoyaltyDriftService.compute_loyalty_pressure()` returns the region's real
   `faction_conflict_exposure` when `region_cultures` has an entry for that region.
2. `compute_loyalty_pressure()` returns `0.0` (not an exception) when the region has no
   `region_cultures` entry — the `None`-safe contract.
3. `effective_defection_threshold(group, loyalty_pressure=X)` lowers the threshold as
   `loyalty_pressure` rises, and is identical to the old (pre-ticket) result at `loyalty_pressure=0.0`
   (backward-compatible default).
4. Determinism guard: calling `compute_loyalty_pressure()` twice with the same inputs returns bit-
   identical output (cheap explicit guard, per this ticket's own AC).
5. Integration test against `config/simulation_quality/profiles/campaign_life_arc.yaml`'s real
   Campaign path: run (or load a fixture equivalent to) that profile's multi-episode Campaign,
   confirm `region_cultures` is genuinely populated, and confirm `compute_loyalty_pressure()` derives
   a real, non-default value from it for at least one populated region.
6. Architecture guard: `LoyaltyDriftService` never mutates `CampaignState`/`AuthoritativeState` —
   read-only, matching the "no new write path" constraint.

## Scoped Pytest Commands

```
pytest tests/unit/social/test_party_lifecycle.py \
       tests/unit/social/test_loyalty_drift.py \
       tests/unit/domains/culture/ \
       tests/integration/culture/ \
       tests/architecture/test_social_write_paths.py \
       -m "not slow"
```

## Anti-Drift Test Guards

- A guard test confirming `GroupPhase.resolve()`'s one live call site to
  `effective_defection_threshold()` still passes no `loyalty_pressure` argument (or passes the
  explicit default) — proving the disclosed live-wiring gap is real and intentional, not an
  oversight silently left untested.
