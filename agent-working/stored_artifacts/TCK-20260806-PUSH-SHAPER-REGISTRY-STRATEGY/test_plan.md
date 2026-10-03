---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY
artifact_type: test_plan
tags: [observability, engine, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY

## Regression Surface

- `tests/unit/observability/` (full directory) — must stay green.
- `tests/unit/kernel/`, `tests/integration/kernel/`, `tests/unit/config/test_phase10_feature_flags.py`
  — touched `kernel.py`/`feature_flags.py`, scoped in for safety.

## New Tests Required

`tests/unit/observability/test_event_shapers_strategy.py` (new, 26 tests):
- Registry/flag-split mechanism (3): `PHASE2_SHAPER_REGISTRY` membership, default-OFF exclusion,
  `SHADOW` construct-without-deliver, `ON` inclusion.
- `property_updates`-driven events (14 tests): fire + non-fire case per event
  (route_selected/action_executed/route_family_first_use, defer_with_reason, self_model_updated,
  belief_assimilated/belief_updated, route_new_query, cooperation_event).
- Reconstructed-current-view events (9 tests): lead_certainty_changed/updated (fire + no-change
  case), belief_stale (fire, dedup, not-yet-stale), decision_diverged_by_belief (fire +
  information-project exclusion), decision_divergence_detected (fire + below-threshold).

## Scoped Pytest Commands

```
pytest tests/unit/observability/ -m "not slow" -q
pytest tests/unit/kernel/ tests/integration/kernel/ tests/unit/config/test_phase10_feature_flags.py -m "not slow" -q
```

## Anti-Drift Test Guards

- `_reset_shaper_state` autouse fixture resets `StrategyShaper`'s class-level dedup caches before
  AND after every test — without it, `test_route_family_first_use_not_repeated_same_family` and
  `test_belief_stale_not_repeated_for_same_lead` would leak into unrelated tests' entity/lead IDs
  colliding by coincidence (low probability but real, given class-level state persists across the
  whole pytest process).
- `_entity_update()` explicitly sets `combat=None`/`intent_results=[]` so the registry-level tests
  (which exercise `run_shadow_shapers()`, invoking ALL Phase 1 shapers too) don't crash on
  MagicMock auto-attributes being mistaken for real combat/economy data by `CombatShaper`/
  `EconomyShaper`.

## Results (this session)

- `pytest tests/unit/observability/test_event_shapers_strategy.py -q`: 26 passed.
- `pytest tests/unit/observability/ -m "not slow" -q`: 824 passed, 6 skipped (was 798/6 before this
  ticket — +26 matches exactly).
- `pytest tests/unit/kernel/ tests/integration/kernel/ tests/unit/config/test_phase10_feature_flags.py -m "not slow" -q`:
  149 passed, 3 deselected, **1 pre-existing failure** —
  `test_all_enhancement_flags_default_to_off_or_shadow`. Confirmed NOT caused by this ticket: the
  only flag violating the assertion is `ENABLE_PUSH_EVENT_SHAPERS` (Phase 1's deliberate `ON`
  default), not this ticket's new `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (correctly defaults `OFF`).
  Filed `TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE` rather than silently absorbing or
  ignoring it.
