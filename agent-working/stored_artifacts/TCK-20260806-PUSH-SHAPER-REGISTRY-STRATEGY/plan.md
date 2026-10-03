---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY
artifact_type: plan
tags: [observability, engine, simulation-quality]
---

# plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY

## Ordered Steps

1. Add `_current_leads()` module helper + `StrategyShaper` class to `src/observability/
   event_shapers.py`, implementing all 14 events per investigation.md's field-mapping table.
   - Files: `src/observability/event_shapers.py`
2. Add `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` flag (default `OFF`) to `feature_flags.py`.
   - Files: `src/domains/optimization/feature_flags.py`
3. Split `SHAPER_REGISTRY`/`run_shadow_shapers()`: new `PHASE2_SHAPER_REGISTRY`, gated internally
   by the new flag (OFF/SHADOW/ON semantics), independent of the Phase 1 flag/registry.
   - Files: `src/observability/event_shapers.py`
4. Verify via real, non-mocked kernel runs: default (no double-fire), `SHADOW` (constructs,
   0 delivered), `ON` (expected double-fire against unguarded old branches, confirming this is
   Cutover's job, not this ticket's).
   - No file changes.
5. Add unit tests per event (fire + non-fire cases) in `tests/unit/observability/
   test_event_shapers_strategy.py`.
   - Files: `tests/unit/observability/test_event_shapers_strategy.py`
6. Update `docs/parity_ledger/strategic_cognition.yaml`, `social_narrative.yaml`,
   `docs/guides/feature_flags.md`.
   - Files: as listed.

## Files to Change

- `src/observability/event_shapers.py`
- `src/domains/optimization/feature_flags.py`
- `tests/unit/observability/test_event_shapers_strategy.py` (new)
- `docs/parity_ledger/strategic_cognition.yaml`, `social_narrative.yaml`
- `docs/guides/feature_flags.md`

## Scope Guards

- Do NOT touch `event_extractor.py`'s old branches for these 14 events — flag-gating them is
  Cutover's (child 8) job, not this ticket's.
- Do NOT merge `PHASE2_SHAPER_REGISTRY` into `SHAPER_REGISTRY`.
- Do NOT touch `CombatShaper`/`EconomyShaper`/`FactionShaper` or Phase 1's own flag.

## Dependency Map

Steps 1-3 are tightly coupled (the flag split only makes sense alongside the shaper class) and
were implemented together. Step 4 depends on 1-3. Step 5 depends on 1. Step 6 depends on all
prior steps' real findings.

## Acceptance Criteria Map

- AC "field-mapping confirmed with file:line citations" → investigation.md's table
- AC "StrategyShaper implements all 14 events, SHADOW-registered" → steps 1-3
- AC "unit tests cover every event's fire + non-fire case" → step 5
- AC "real kernel run confirms correctly-shaped SHADOW output" → step 4
- AC "parity ledger updated" → step 6
