---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE
date: 2026-09-07
---

# Test Plan: TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE

## Regression Surface
- `tests/unit/social/` (party lifecycle, relationships, defection threshold pure-function tests —
  must stay green, since `effective_defection_threshold()`/`check_defection()`'s public signature is
  unchanged, only their one live caller's own argument now varies).
- `tests/integration/campaigns/` (CampaignOrchestrator/episode-boundary tests).
- `tests/unit/world/`, `tests/integration/world/` (Kernel/GroupPhase-adjacent tests — `Kernel`
  itself is untouched, but `groups.py` gained a new import).

## New Tests Required (per AC)
- AC2: `tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py` —
  `test_bridged_loyalty_pressure_lowers_the_real_defection_threshold_through_group_phase_resolve`
  (positive: bridged high pressure defects earlier; negative: no bridged signal reproduces exact
  pre-bridge behavior, same grievance count).
  `test_group_anchored_outside_any_region_defaults_to_zero_pressure_none_safely` (a group anchored
  outside any region falls back to 0.0, doesn't raise or misapply another region's signal).

## Scoped Pytest Commands
```
python3 -m pytest tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py -v
python3 -m pytest tests/unit/social/ tests/integration/campaigns/ -q
python3 -m pytest tests/integration/world/ tests/unit/world/ -q -m "not extra_slow"
```

## Anti-Drift Test Guards
- The new test targets `GroupPhase.resolve()` itself, not the already-covered pure functions
  (`test_party_lifecycle.py::test_check_defection_fires_earlier_with_loyalty_pressure` already
  proves those) — duplicating that coverage would add no value.
- The negative-path assertion (no bridged signal → no defection at the same grievance count) is a
  real regression-catching case, not a tautology — it would fail if the bridge accidentally supplied
  a nonzero default.

## Results
`tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py` — 2 passed.
`tests/unit/social/ tests/integration/campaigns/` — 296 passed.
`tests/integration/world/ tests/unit/world/` (excluding `-m extra_slow`, one real
`@pytest.mark.extra_slow`-marked, CI-skipped long-run test hit an unrelated resource-time-limit
timeout under this shell's own 100s bash timeout, not this ticket's change) — 340 passed, 0 failed.
