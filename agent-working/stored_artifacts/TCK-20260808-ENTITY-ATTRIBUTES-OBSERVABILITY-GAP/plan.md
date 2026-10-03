---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP
artifact_type: plan
tags: [observability, world]
---

# Plan — TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP

## Steps

1. `src/observability/event_extractor.py`: one new diff-based event, `attribute_changed`,
   inserted in the same vitals block added by `TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP`
   (same `mode not in (LIGHT, LONG_RUN)` guard, same `_is_real_number` defensive pattern —
   `AttributeComponent` fields are plain `int` on a real `EntityState`, but the vitals ticket's
   own MagicMock-fixture regression is the reason to guard proactively rather than reactively).
2. `tests/unit/observability/test_event_extractor_attributes.py`: the 6 tests from test_plan.md.
3. `docs/simulation_quality/event_type_coverage.md`: register `attribute_changed` in §5
   Unscored Intentional.
4. `docs/event_ledger/entity.yaml`: flip `ENTITY-008` from `silent` to `observed`.
5. Parity: `src/observability/event_extractor.py` maps to the same subsystem set as the vitals
   ticket found. Attribute mutation is entity-core state (not combat-specific) — new entry goes
   in `docs/parity_ledger/substrate.yaml` (same `SUB-` domain as biological/stamina), next ID
   after `SUB-375`.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies every real mutation source | Done |
| New event wired and confirmed via real Kernel.tick_once() loop | Step 2, Test 1 |
| event_type_coverage.md and entity.yaml updated | Steps 3-4 |
| Scoped pytest passes | Step 2 |
