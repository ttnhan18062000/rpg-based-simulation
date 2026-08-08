---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL
artifact_type: test_plan
tags: [observability, engine, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL

## Regression Surface

- `tests/unit/observability/` (full directory), `tests/unit/kernel/`, `tests/integration/kernel/`.

## New Tests Required

`tests/unit/observability/test_event_shapers_social.py` (new, 20 tests): registry membership (1),
group events (3, including the `-1` sentinel), reputation (2), social memory (4, including dedup),
contract lifecycle (6, status-transition + reap path),
`test_contract_expired_offer_not_double_fired_when_both_signals_present` (the real-bug regression
test), contract milestones (3).

## Scoped Pytest Commands

```
pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q
```

## Anti-Drift Test Guards

- `_reset_shaper_state` autouse fixture, same pattern as Children 2-3.
- `test_contract_expired_offer_not_double_fired_when_both_signals_present` directly regression-
  guards the real double-firing bug found via kernel verification — constructs an update with
  BOTH `contracts_add_or_update` (status=EXPIRED) and `contracts_remove` for the same contract ID,
  asserting exactly 1 event, not 2.

## Results (this session)

- `pytest tests/unit/observability/test_event_shapers_social.py -q`: 20 passed.
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  1031 passed, 6 skipped, 3 deselected (was 1011/6/3 after Child 4 — +20 matches exactly, no
  cross-shaper isolation issue).
- Real kernel run (`urban_political_seed42_500t`, `ENABLE_SOCIAL_COOPERATION=ON`): before fix,
  `contract_expired_offer` showed `event_extractor=996` vs `event_shapers=1991` (~2x mismatch);
  after fix, `1022` vs `1019` (within normal run-to-run noise). `contract_offer_created` matched
  exactly both times (1049/1049 post-fix). `SHADOW` mode confirmed 0 SOCIAL-specific deliveries.
