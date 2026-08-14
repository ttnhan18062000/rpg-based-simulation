---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP
artifact_type: plan
tags: [observability, world]
---

# Plan — TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP

## Steps

1. `src/observability/event_extractor.py`: four new diff-based events — `entity_role_changed`,
   `entity_faction_changed`, `recipe_learned`, `skill_cooldown_started` — inserted in the same
   vitals/attributes/equipment block. No `TaskUpdate` event (documented deliberate skip).
2. `tests/unit/observability/test_event_extractor_identity.py`: the 8 tests from test_plan.md.
3. `docs/simulation_quality/event_type_coverage.md`: register the 4 new events in §5 Unscored
   Intentional; add a note under an appropriate section recording the `TaskUpdate` deliberate-skip
   verdict (not an event registration, a documented non-coverage decision).
4. `docs/event_ledger/entity.yaml`: flip `ENTITY-007` `partial` → `observed`; update `ENTITY-015`'s
   notes with the deliberate-skip verdict (stays `silent` — no event exists, on purpose).
5. Parity: entity-core state — new entry in `docs/parity_ledger/substrate.yaml`, next ID after
   `SUB-377`.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies every real trigger | Done |
| Clear TaskUpdate verdict | Done |
| New event(s) wired and confirmed | Step 2 |
| event_type_coverage.md and entity.yaml updated | Steps 3-4 |
| Scoped pytest passes | Step 2 |
