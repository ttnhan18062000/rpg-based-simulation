---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21B-REGEN-SERVICE
artifact_type: test_plan
tags: [resource-ecology, regeneration, event-emitter, phase-2]
---

# Test Plan — TCK-20260619-E21B-REGEN-SERVICE
## Epic 2.1B · Depletion Emitter + Charge Regen Loop

---

## Regression Surface

These tests must continue to pass after E21B changes. Scope them before touching any
source file.

### `tests/unit/resource/`
All files — covers conservation law, node charge accounting, and schema from E21A:

```bash
pytest tests/unit/resource/ -x -v -q
```

Key tests to watch:
- `test_resource_contract.py::test_law_of_availability_node_depleted` — node with 0
  charges is rejected; must not be affected by event emission path.
- `test_resource_contract.py::test_resource_node_regen_rate_field_exists` — E21A AC1.
- `test_resource_contract.py::test_resource_node_regen_rate_in_canonical_dict` — E21A AC2.
- `test_harvest_channeling.py` — full harvest progress/completion cycle.
- `test_resource_conflicts.py` — two-actor race; must not emit duplicate DEPLETED events.
- `test_resource_conservation_regression.py` — atomic conservation law.

### `tests/unit/world/`
Subset touching ecology, world dynamics, and node lifecycle:

```bash
pytest tests/unit/world/test_world_dynamics.py tests/unit/world/test_economy_contract.py -x -v -q
```

- `test_world_dynamics.py` — node cooldown/recharge via `world_dynamics.py`. Regen loop
  must not break the existing cooldown-recharge path.

### `tests/unit/core/`
```bash
pytest tests/unit/core/test_hardening_e5.py tests/unit/core/test_engine_integrity.py -x -v -q
```

---

## New Tests Required

All new tests go in `tests/unit/world/test_resource_ecology.py` (create if absent).

### Group A — `RESOURCE_DEPLETED` emitter

**`test_depleted_event_emitted_when_last_charge_harvested`**
- Setup: Node with `remaining_charges=1`, entity with inventory space.
- Action: Resolve a `ResourceTransferIntent(source_kind="NODE", source_id=node.id)` through
  `ResourceTransactionSystem.resolve_all()`.
- Assert: Returned `StateUpdate` contains a `WorldEvent` with
  `category=RESOURCE_DEPLETED` and `subject=str(node.id)`.
- Covers: AC1 ("After a harvest exhausts a node's charges: RESOURCE_DEPLETED appears").

**`test_depleted_event_not_emitted_when_charges_remain`**
- Setup: Node with `remaining_charges=3`.
- Action: Resolve one harvest (takes 1 charge → 2 remain).
- Assert: No `RESOURCE_DEPLETED` event in returned update.
- Covers: Guard — only emit on transition to 0.

**`test_depleted_event_not_emitted_twice_same_tick_two_actors`**
- Setup: Node with `remaining_charges=1`, two entities both resolve harvests in same
  `StateUpdate` (second is rejected by reservation logic).
- Assert: Exactly one `RESOURCE_DEPLETED` event in update (not two).
- Covers: Anti-drift hazard 3 — no duplicate emission.

**`test_depleted_event_not_emitted_on_failed_harvest`**
- Setup: Node with `remaining_charges=1`, entity inventory full.
- Action: Harvest attempt → `TransactionResult.accepted=False` (INVENTORY_FULL).
- Assert: No `RESOURCE_DEPLETED` event emitted.
- Covers: Anti-drift hazard 2 — only emit on accepted transactions.

### Group B — Regen loop in `ResourceEcologyService`

**`test_regen_increments_charges_per_ecology_interval`**
- Setup: `AuthoritativeState` at `tick=200` (ecology interval), node with
  `remaining_charges=2, max_charges=5, regen_rate_per_tick=1, cooldown_remaining=0`.
- Action: Call `ResourceEcologyService.process_ecology(state, generator)`.
- Assert: Returned `StateUpdate.node_updates[node.id].charges_delta == 1`.
- Covers: AC3 ("remaining_charges increases by regen_rate_per_tick per ecology interval").

**`test_regen_capped_at_max_charges`**
- Setup: Node with `remaining_charges=4, max_charges=5, regen_rate_per_tick=2`.
- Action: Call `process_ecology()` at ecology tick.
- Assert: `charges_delta == 1` (not 2 — capped at max_charges).
- Covers: AC3 cap.

**`test_regen_skipped_when_already_at_max`**
- Setup: Node with `remaining_charges=5, max_charges=5, regen_rate_per_tick=1`.
- Action: Call `process_ecology()` at ecology tick.
- Assert: Node not present in `StateUpdate.node_updates` (no-op).
- Covers: `remaining_charges >= max_charges` guard.

**`test_regen_skipped_when_rate_is_zero`**
- Setup: Node with `remaining_charges=2, max_charges=5, regen_rate_per_tick=0`.
- Action: Call `process_ecology()`.
- Assert: Node not present in `StateUpdate.node_updates`.
- Covers: `regen_rate_per_tick <= 0` guard.

**`test_regen_skipped_during_cooldown`**
- Setup: Node with `remaining_charges=0, max_charges=5, regen_rate_per_tick=1,
  cooldown_remaining=50`.
- Action: Call `process_ecology()` at ecology tick.
- Assert: Node not in `StateUpdate.node_updates` via regen path (cooldown path owns it).
- Covers: Anti-drift hazard 4 — no regen during cooldown.

**`test_regen_not_fired_on_non_ecology_tick`**
- Setup: Node with `remaining_charges=1, max_charges=5, regen_rate_per_tick=1`.
  State at `tick=201` (non-interval tick).
- Action: Call `process_ecology()`.
- Assert: Returned `StateUpdate.is_noop()` is True (or at minimum no node_updates).
- Covers: Tick-gate guard.

### Group C — `RESOURCE_RECOVERED` event emission

**`test_recovered_event_emitted_when_depleted_node_regens`**
- Setup: Node with `remaining_charges=0, max_charges=5, regen_rate_per_tick=1,
  cooldown_remaining=0`.
- Action: Call `process_ecology()` at ecology tick.
- Assert: Returned `StateUpdate` (or event list) contains `WorldEvent` with
  `category=RESOURCE_RECOVERED` and `subject=str(node.id)`.
- Covers: AC2 ("After sufficient ecology ticks: RESOURCE_RECOVERED appears").

**`test_recovered_event_not_emitted_when_node_already_has_charges`**
- Setup: Node with `remaining_charges=2, max_charges=5, regen_rate_per_tick=1`.
- Action: Call `process_ecology()`.
- Assert: No `RESOURCE_RECOVERED` event (node was not depleted).
- Covers: Guard — only emit on `was_depleted (remaining == 0) and new_charges > 0`.

**`test_recovered_event_not_emitted_twice`**
- Setup: Node partially recovered (remaining=1). Call ecology twice.
- Assert: `RESOURCE_RECOVERED` only in the first call's output.
- Covers: Idempotency of recovery event.

### Group D — Parity / integration guards

**`test_regen_charges_delta_is_positive`**
- Assert: For any regen scenario, `charges_delta >= 0` in returned `ResourceNodeUpdate`.
  Negative delta from regen would corrupt node state.

**`test_world_event_category_depleted_and_recovered_importable`**
- Assert: `WorldEventCategory.RESOURCE_DEPLETED` and `WorldEventCategory.RESOURCE_RECOVERED`
  are importable and equal their string values. (Regression guard for E21A.)

**`test_state_update_carries_world_events`** *(prerequisite: StateUpdate has world_events_add)*
- Assert: `StateUpdate(world_events_add=[...])` construction succeeds; field survives
  `StateUpdate.merge()` (events concatenate, not overwrite); `is_noop()` returns False
  when events present.

**`test_recent_world_events_on_authoritative_state`** *(prerequisite: field added)*
- Assert: `AuthoritativeState` constructed with `recent_world_events=[WorldEvent(...)]`
  stores the field; `getattr(state, "recent_world_events", [])` returns it (no longer
  falls back to default).

---

## Scoped Pytest Commands

### Before any code change — confirm baseline
```bash
pytest tests/unit/resource/ tests/unit/world/test_world_dynamics.py -x -v -q
```

### After adding `world_events_add` to `StateUpdate` and `recent_world_events` to `AuthoritativeState`
```bash
pytest tests/unit/resource/ tests/unit/core/test_engine_integrity.py -x -v -q
```

### After wiring `RESOURCE_DEPLETED` emitter
```bash
pytest tests/unit/world/test_resource_ecology.py::test_depleted_event_emitted_when_last_charge_harvested \
       tests/unit/world/test_resource_ecology.py::test_depleted_event_not_emitted_when_charges_remain \
       tests/unit/world/test_resource_ecology.py::test_depleted_event_not_emitted_twice_same_tick_two_actors \
       tests/unit/world/test_resource_ecology.py::test_depleted_event_not_emitted_on_failed_harvest \
       tests/unit/resource/ -x -v
```

### After adding regen loop to `process_ecology()`
```bash
pytest tests/unit/world/test_resource_ecology.py -x -v
```

### Full scoped suite (final verification)
```bash
pytest tests/unit/world/ tests/unit/resource/ tests/unit/core/test_hardening_e5.py \
       tests/unit/core/test_engine_integrity.py -x -v -q
```

### Regression — do not run full suite
Do NOT run `pytest tests/` or `pytest tests_v2/`. Scope strictly to domains above.

---

## Anti-Drift Test Guards

1. **Test `test_regen_skipped_during_cooldown`** — ensures `world_dynamics.py` cooldown
   path and `ecology.py` regen path never both fire on the same node in the same tick.
   Both write `charges_delta` to the same `StateUpdate.node_updates[node_id]`; without
   the guard they would sum incorrectly.

2. **Test `test_depleted_event_not_emitted_twice_same_tick_two_actors`** — prevents
   double-emission when two actors race for the last charge. The second actor is rejected
   by the reservation system (`economy.py:L84–L89`), so only one event should fire.

3. **Test `test_regen_charges_delta_is_positive`** — structural guard. The regen formula
   `delta = min(max_charges, remaining + rate) - remaining` is always ≥ 1 when the
   guards pass. A negative delta would silently drain a node.

4. **Test `test_state_update_carries_world_events`** — ensures `StateUpdate.is_noop()`
   and `merge_many()` are updated when `world_events_add` is added. Without this, events
   would silently disappear during merge or be invisible to noop checks.

5. **Test `test_world_event_category_depleted_and_recovered_importable`** — regression
   guard for E21A. If `schema.py` is accidentally reverted, this catches it immediately.
