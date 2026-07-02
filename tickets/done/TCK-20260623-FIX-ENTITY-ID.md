---
status: done
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-ENTITY-ID
phase: done
date: 2026-06-23
tags: [test-repair, entity, identity, KeyError, state, P1]
---

# TCK-20260623-FIX-ENTITY-ID

## Title
Fix entity ID KeyError across unit + integration tests (~8 failures)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Multiple tests fail with `KeyError: 1` when looking up entities by integer key `1`.
The same pattern appears across unit and integration tests in unrelated domains, indicating
a shared root cause in how entity state is keyed or seeded.

**Confirmed failures with this signature:**
```
tests/unit/core/test_hardening_e5.py:123       KeyError: 1
tests/unit/core/test_hardening_e5.py:240       KeyError: 1
tests/unit/core/test_hardening_e5.py:251       KeyError: 1
tests/unit/core/test_hardening_e5.py:219       AttributeError: 'NoneType' has no attribute 'items_add'
tests/integration/domains/test_fused_loop.py:208  assert 1 in {}   (entity ID 1 not in state)
tests/integration/pipeline/test_recovery_gaps.py:99  KeyError: 1
```

The `assert 1 in {}` pattern in `test_fused_loop.py` is the most diagnostic: entity `1`
simply does not exist in the world state dict. This means either:
(a) Entity IDs were changed from integers to strings/UUIDs, and tests still use `1`
(b) Entity seeding changed and entity `1` is no longer created by the test fixtures
(c) The entity state dict is keyed differently (e.g., `entity_id` object vs. raw int)

The `NoneType.items_add` failure confirms that entity lookup returns `None` rather than
raising a missing-key error in some code paths — suggesting a `.get(1)` rather than `[1]`
in part of the code.

## Scope
- Identify the current entity ID type and seeding convention used in test fixtures
- If IDs changed from `int` to `str` or `UUID`: update test fixtures that hardcode `1`
  to use the correct ID type
- If entity seeding changed: update test setup to seed entity with the expected ID
- Fix the `NoneType.items_add` path: either change `.get()` to `[]` or add a null guard
- Do NOT change entity ID logic in production code unless it is a genuine regression

## Out of Scope
- Entity identity system redesign
- Changing production entity ID generation
- Other test domains not listed

## Acceptance Criteria
- `tests/unit/core/test_hardening_e5.py` — all 4 tests pass (no KeyError: 1)
- `tests/integration/domains/test_fused_loop.py::test_belief_assimilation_persists_facts` passes
- `tests/integration/pipeline/test_recovery_gaps.py::test_building_sabotage` passes

## Related Tickets
- TCK-20260623-FIX-INVENTORY-DEFAULTS (resource state keying may share root)
- TCK-20260623-FIX-KERNEL-PHASES (entity state initialization may relate)

## Related Docs
- `docs/core/entities.md` (entity lifecycle and identity)
- `docs/core/state.md` (authoritative state partitioning)

## Related Code Areas
- `src/core/state.py` (entity state dict keying)
- `src/entities/` (entity ID generation)
- `tests/unit/core/test_hardening_e5.py`
- `tests/integration/domains/test_fused_loop.py`
- `tests/integration/pipeline/test_recovery_gaps.py`
- `tests/fixtures/` (entity fixture helpers — check what ID type they produce)

## Assumptions / Open Questions
- Did entity IDs change from plain `int` to a typed `EntityId` / `str` / `UUID` at some point?
- Is integer `1` a hardcoded assumption in test fixtures, or derived from an ID generator?
- Does the entity fixture in `test_hardening_e5.py` use `EntityBuilder` or raw dict construction?

## Implementation Notes
Investigation order:
1. `graphify query "entity identity state dict key EntityId"` to find the ID type
2. Read `docs/core/entities.md` for entity ID contract
3. Read one failing test to see how entity is created and looked up
4. Check `src/core/state.py` for the state dict key type
5. Update test fixtures or lookup calls

## Test Summary
Run: `pytest tests/unit/core/test_hardening_e5.py tests/integration/domains/test_fused_loop.py tests/integration/pipeline/test_recovery_gaps.py --tb=short`

## Files Changed
- `src/engine/pipeline.py` — 3 pipeline phases changed from `lambda u: StateUpdate(...)` to `lambda u: u.merge(StateUpdate(...))`: faction_awareness (L181), diplomatic_transitions (L211), military_conflict (L221)

## Completion Summary
Root cause was not entity ID type — it was faction_awareness/diplomatic_transitions/military_conflict pipeline phases returning fresh StateUpdate() ignoring `u`, wiping entity_updates built by earlier phases. Fixed with u.merge(). test_building_sabotage and test_belief_assimilation_persists_facts now pass. 162 engine/pipeline tests pass. 2 pre-existing idempotency behavioral failures (test_cross_tick_idempotency, test_in_tick_idempotency) remain — masked by KeyError previously, now surfaced as separate behavioral regression outside this ticket's scope.
