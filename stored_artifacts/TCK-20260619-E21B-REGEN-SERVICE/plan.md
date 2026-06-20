---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21B-REGEN-SERVICE
artifact_type: plan
tags: [resource-ecology, regeneration, event-emitter, phase-2]
---

# Plan — TCK-20260619-E21B-REGEN-SERVICE
## Epic 2.1B · Depletion Emitter + Charge Regen Loop

---

## Dependency Map

```
Step 1 ──────────────────────────────────► Step 3
  (world_events_add on StateUpdate)          (economy.py emitter uses world_events_add)
  │
  └──────────────────────────────────────► Step 4
                                             (ecology.py regen uses world_events_add)

Step 2 ──────────────────────────────────► (required by apply.py accumulation logic)
  (recent_world_events on AuthoritativeState)

Step 5 ──────────────────────────── no dependency (seeder field, independent of events)

Step 6 ──────────────────────────── depends on Steps 1–5 all complete
  (tests exercise all wired paths)
```

**Critical ordering constraint:** Step 1 must be complete before Steps 3 and 4.
Step 2 must be complete before Step 4 (apply path reads the field).
Steps 3 and 4 are independent of each other once Step 1 is done.
Step 5 is fully independent — can be done in any order.
Step 6 must be last.

---

## Step 1 — Add `world_events_add` to `StateUpdate`

**File:** `src/core/updates.py`

**What to change:**

1. Import `WorldEvent` from `src/domains/world_emergence/schema.py` (or the module that
   exports it). Check existing imports at the top of `updates.py` first; it may already
   import from that namespace.

2. Add field to `StateUpdate` (around L862, after the last existing field):
   ```python
   world_events_add: list[WorldEvent] = field(default_factory=list)
   ```

3. Update `is_noop()` — find the existing `is_noop()` method and add:
   ```python
   and not self.world_events_add
   ```
   to the conjunction. Must return `False` if `world_events_add` is non-empty.

4. Update `merge_many()` (or `merge()`) — find the class method that combines multiple
   `StateUpdate` instances. For `world_events_add`, use list concatenation (extend), not
   overwrite:
   ```python
   world_events_add=[e for u in updates for e in u.world_events_add]
   ```

**Scope guard:** Do NOT add `charges_set` to `ResourceNodeUpdate`. Do NOT rename any
existing fields. Touch only `StateUpdate`.

**Verification checkpoint:**
```bash
python3 -c "from src.core.updates import StateUpdate; s = StateUpdate(); print(s.is_noop()); print(s.world_events_add)"
```
Expected: `True`, `[]`.

---

## Step 2 — Add `recent_world_events` to `AuthoritativeState` and wire in `apply.py`

**Files:**
- `src/core/state.py` (add field to `AuthoritativeState`)
- `src/engine/apply.py` (populate the field in `apply_generation()`)

### 2a — `src/core/state.py`

Locate `AuthoritativeState` (around L984–L1051). Add field:
```python
recent_world_events: list[WorldEvent] = field(default_factory=list)
```
Place it near the end of the dataclass fields, before any methods. Import `WorldEvent`
at the top of `state.py` if not already present.

### 2b — `src/engine/apply.py`

Locate `ApplyPath.apply_generation()` (around L310–L355). The method constructs a new
`AuthoritativeState(...)` with explicit keyword arguments.

1. Before the constructor call, compute the new event window:
   ```python
   WORLD_EVENT_WINDOW = 500
   prior_events = getattr(state, "recent_world_events", [])
   new_events = state_update.world_events_add  # list[WorldEvent]
   merged_events = prior_events + new_events
   # Rolling window: keep only the most recent WORLD_EVENT_WINDOW events
   recent_world_events = merged_events[-WORLD_EVENT_WINDOW:]
   ```

2. Pass it in the constructor call:
   ```python
   AuthoritativeState(
       ...,  # all existing fields unchanged
       recent_world_events=recent_world_events,
   )
   ```

**Scope guard:** Do NOT change how any other field is computed. Do NOT alter the
`getattr(state, "recent_world_events", [])` call in `pipeline.py:L212` — it will
naturally start returning the real field once it exists on `AuthoritativeState`.

**Verification checkpoint:**
```bash
python3 -c "
from src.core.state import AuthoritativeState
s = AuthoritativeState.__new__(AuthoritativeState)
print(hasattr(AuthoritativeState, '__dataclass_fields__'))
print('recent_world_events' in AuthoritativeState.__dataclass_fields__)
"
```
Expected: `True`, `True`.

---

## Step 3 — Emit `RESOURCE_DEPLETED` in `economy.py`

**File:** `src/engine/economy.py`

**Injection point:** `ResourceTransactionSystem._apply_world_effects()` at L278–L284.

The method currently accumulates `node_update.charges_delta` into `new_node_updates`. After
this accumulation loop (or inside it, after each accepted transaction), compute
`new_charges = node.remaining_charges + accumulated_delta` and fire the event when
`node.remaining_charges > 0 and new_charges <= 0`.

**Precise change:**

1. At the top of `_apply_world_effects()` (or in the caller `resolve_all()`), initialize:
   ```python
   world_events: list[WorldEvent] = []
   ```

2. Inside the loop where `charges_delta` is accumulated, after updating the running total
   for a node, add:
   ```python
   # node_remaining is the pre-tick remaining_charges; accumulated_delta is the
   # running total for this node_id including this transaction's delta.
   new_charges = node.remaining_charges + accumulated_delta
   if node.remaining_charges > 0 and new_charges <= 0:
       world_events.append(WorldEvent(
           category=WorldEventCategory.RESOURCE_DEPLETED,
           tick=state.tick,
           region_id=None,
           subject=str(node_id),
           severity=1.0,
       ))
   ```
   The guard `node.remaining_charges > 0 and new_charges <= 0` fires at most once
   per node per `resolve_all()` call: once the accumulated delta crosses zero,
   subsequent rejected transactions (second actor) do not change the accumulated delta.

3. In the `StateUpdate(...)` returned from `_apply_world_effects()` (or assembled in
   `resolve_all()`), include:
   ```python
   world_events_add=world_events,
   ```

**Import:** Add `WorldEvent` and `WorldEventCategory` imports from
`src/domains/world_emergence/schema.py` at the top of `economy.py` if not already present.

**Scope guard:** Do NOT emit the event from `InteractionSystem`, `conservation.py`, or
`apply_plan.py`. Do NOT change how `node_updates` are merged or applied. Emit only when
`TransactionResult.accepted=True` (which is already the filter that updates `new_node_updates`).

**Anti-drift guards enforced by this step:**
- Emit only on `old_charges > 0 and new_charges <= 0` — prevents double-emission.
- Emit only inside the accepted-transaction path — prevents emission on rejected harvests.

**Verification checkpoint (manual):**
- After Step 6 tests pass for Group A, this step is verified.

---

## Step 4 — Add regen loop to `ResourceEcologyService.process_ecology()`

**File:** `src/world/ecology.py`

**Position:** Before the density seeding block (before the `_seed_density_nodes()` call
or equivalent loop around L19–L76).

**Algorithm:**

```python
regen_node_updates: dict = {}
regen_events: list[WorldEvent] = []

for node_id, node in state.resource_nodes.items():
    # Guard 1: rate must be positive
    if node.regen_rate_per_tick <= 0:
        continue
    # Guard 2: not already at max
    if node.remaining_charges >= node.max_charges:
        continue
    # Guard 3: not in cooldown (cooldown path owns that node)
    if node.cooldown_remaining > 0:
        continue

    was_depleted = (node.remaining_charges == 0)
    new_charges = min(node.max_charges, node.remaining_charges + node.regen_rate_per_tick)
    delta = new_charges - node.remaining_charges  # always >= 1 when guards pass

    regen_node_updates[node_id] = ResourceNodeUpdate(
        node_id=node_id,
        charges_delta=delta,
    )

    if was_depleted and delta > 0:
        regen_events.append(WorldEvent(
            category=WorldEventCategory.RESOURCE_RECOVERED,
            tick=state.tick,
            region_id=None,  # cheap path; region lookup not required for E21B
            subject=str(node_id),
            severity=1.0,
        ))
```

Merge `regen_node_updates` and `regen_events` into the `StateUpdate` returned from
`process_ecology()`. If the method already builds a `StateUpdate(nodes_add=...,
next_node_id_set=...)`, extend it to also pass:
```python
node_updates=regen_node_updates,
world_events_add=regen_events,
```

**Note on tick-gating:** `process_ecology()` is called by `WorldDynamicsSystem` only
when `state.tick % ECOLOGY_INTERVAL == 0` (L16 guard in `ecology.py` or the caller).
Confirm this gate is in place before adding the regen loop. If the gate is inside
`process_ecology()` itself, the regen loop must be inside the same gate block.

**Import:** Add `WorldEvent`, `WorldEventCategory`, `ResourceNodeUpdate` imports at the
top of `ecology.py` if not already present.

**Scope guard:** Do NOT touch `world_dynamics.py`. Do NOT add `charges_set` to
`ResourceNodeUpdate`. Region lookup via `LegalityServiceV2.get_region_for_position()`
is NOT required for `RESOURCE_RECOVERED` in this ticket (`region_id=None` is accepted).

**Anti-drift guards enforced:**
- Skip nodes with `cooldown_remaining > 0` — prevents conflict with `world_dynamics.py`.
- `was_depleted` guard on `RESOURCE_RECOVERED` — fires only on first recovery ecology tick.

---

## Step 5 — Set `regen_rate_per_tick=1` on ecology-seeded nodes

**File:** `src/world/ecology.py`

**Scope:** Only nodes seeded by `_seed_density_nodes()` (or equivalent method inside
`ecology.py` at L62–L70). Do NOT change `src/worldbuilding/compiler.py` — compiler-seeded
nodes retain `regen_rate_per_tick=0` (static/permanent nodes).

**Change:** When constructing new `ResourceNodeState` instances in the seeder, add the
field:
```python
ResourceNodeState(
    ...,  # all existing fields
    regen_rate_per_tick=1,
)
```
This applies to all harvestable nodes created by the ecology seeder (IRON, WOOD, STONE
and any other ecology-seeded kinds). If the seeder uses a conditional by `kind`, set
`regen_rate_per_tick=1` for all ecology-seeded nodes uniformly (not just IRON/WOOD/STONE)
unless the existing code already distinguishes.

**Verification:** A newly seeded node returned in `StateUpdate.nodes_add` has
`regen_rate_per_tick=1`.

---

## Step 6 — Write tests in `tests/unit/world/test_resource_ecology.py`

**File:** `tests/unit/world/test_resource_ecology.py` (create if absent)

**Required test groups and test names:**

### Group A — `RESOURCE_DEPLETED` emitter (4 tests)

| Test name | Asserts | Covers |
|---|---|---|
| `test_depleted_event_emitted_when_last_charge_harvested` | `StateUpdate.world_events_add` contains `WorldEvent(category=RESOURCE_DEPLETED, subject=str(node_id))` | AC1 |
| `test_depleted_event_not_emitted_when_charges_remain` | No `RESOURCE_DEPLETED` event when `remaining_charges` goes from 3 → 2 | Transition guard |
| `test_depleted_event_not_emitted_twice_same_tick_two_actors` | Exactly one `RESOURCE_DEPLETED` event when second actor's harvest is rejected | Anti-drift 3 |
| `test_depleted_event_not_emitted_on_failed_harvest` | No event when `TransactionResult.accepted=False` | Anti-drift 2 |

### Group B — Regen loop (6 tests)

| Test name | Asserts | Covers |
|---|---|---|
| `test_regen_increments_charges_per_ecology_interval` | `StateUpdate.node_updates[node_id].charges_delta == 1` for node with `remaining=2, max=5, rate=1` | AC3 |
| `test_regen_capped_at_max_charges` | `charges_delta == 1` (not 2) for `remaining=4, max=5, rate=2` | AC3 cap |
| `test_regen_skipped_when_already_at_max` | Node absent from `StateUpdate.node_updates` when `remaining == max` | `>= max` guard |
| `test_regen_skipped_when_rate_is_zero` | Node absent from `StateUpdate.node_updates` when `rate=0` | `rate <= 0` guard |
| `test_regen_skipped_during_cooldown` | Node absent from regen path when `cooldown_remaining=50` | Anti-drift 4 |
| `test_regen_not_fired_on_non_ecology_tick` | `StateUpdate.is_noop()` True (or no `node_updates`) when `tick=201` | Tick-gate guard |

### Group C — `RESOURCE_RECOVERED` event (3 tests)

| Test name | Asserts | Covers |
|---|---|---|
| `test_recovered_event_emitted_when_depleted_node_regens` | `world_events_add` contains `WorldEvent(category=RESOURCE_RECOVERED)` for `remaining=0, rate=1` | AC2 |
| `test_recovered_event_not_emitted_when_node_already_has_charges` | No `RESOURCE_RECOVERED` when `remaining=2` | `was_depleted` guard |
| `test_recovered_event_not_emitted_twice` | `RESOURCE_RECOVERED` only in first ecology call output, not second | Idempotency |

### Group D — Parity / structural guards (4 tests)

| Test name | Asserts | Covers |
|---|---|---|
| `test_regen_charges_delta_is_positive` | `charges_delta >= 1` for all valid regen scenarios | Anti-drift — no accidental drain |
| `test_world_event_category_depleted_and_recovered_importable` | Both enum values importable from `schema.py` | E21A regression |
| `test_state_update_carries_world_events` | `StateUpdate(world_events_add=[...])` constructs; `merge_many()` concatenates; `is_noop()` False when events present | Step 1 completeness |
| `test_recent_world_events_on_authoritative_state` | `AuthoritativeState` stores `recent_world_events`; `getattr` no longer falls back | Step 2 completeness |

**Test scoped run commands:**

After Step 3 (DEPLETED emitter):
```bash
pytest tests/unit/world/test_resource_ecology.py -k "depleted" -x -v
pytest tests/unit/resource/ -x -v -q
```

After Step 4 (regen loop):
```bash
pytest tests/unit/world/test_resource_ecology.py -x -v
```

Final verification:
```bash
pytest tests/unit/world/ tests/unit/resource/ tests/unit/core/test_hardening_e5.py \
       tests/unit/core/test_engine_integrity.py -x -v -q
```

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion | Step(s) that satisfy it |
|---|---|
| AC1: After harvest exhausts node: `RESOURCE_DEPLETED` in event log | Step 1 (field), Step 3 (emitter), Step 6 (test) |
| AC2: After sufficient ecology ticks: `RESOURCE_RECOVERED` appears | Step 1 (field), Step 4 (emitter), Step 6 (test) |
| AC3: `remaining_charges` increases by `regen_rate_per_tick` per ecology interval (capped at `max_charges`) | Step 4 (regen loop), Step 5 (rate field set), Step 6 (test) |
| Tests in `tests/unit/world/test_resource_ecology.py` pass | Step 6 (all 17 tests) |

---

## Parity Ledger Updates Required (post-implementation)

After implementation, update `docs/parity_ledger/town_resource.yaml`:

- **TOWN-137** (`resource-node recharge behavior is deterministic`): Add `v2_evidence`
  pointing to the regen loop in `ecology.py` and the new test
  `test_regen_increments_charges_per_ecology_interval`.

- **Add TOWN-173**: `RESOURCE_DEPLETED` event emitted when node charges reach 0 after
  accepted harvest. Status: `verified`. `test_path`:
  `tests/unit/world/test_resource_ecology.py::test_depleted_event_emitted_when_last_charge_harvested`.

- **Add TOWN-174**: `RESOURCE_RECOVERED` event emitted when depleted node gains charges
  via regen loop. Status: `verified`. `test_path`:
  `tests/unit/world/test_resource_ecology.py::test_recovered_event_emitted_when_depleted_node_regens`.

- **Add TOWN-175**: `remaining_charges` increases by `regen_rate_per_tick` per ecology
  interval, capped at `max_charges`, only when `cooldown_remaining == 0`. Status:
  `verified`. `test_path`:
  `tests/unit/world/test_resource_ecology.py::test_regen_increments_charges_per_ecology_interval`.

---

## Scope Guards (consolidated)

**Do NOT touch:**
- `src/worldbuilding/compiler.py` — compiler-seeded nodes keep `regen_rate_per_tick=0`
- `src/engine/interaction.py` — not the injection point for DEPLETED emission
- `src/core/conservation.py` — not the injection point; emitter goes in economy.py
- `src/engine/apply_plan.py` — do not add event emission here (Step 3 uses economy.py)
- `src/engine/world_dynamics.py` — cooldown recharge path is untouched; regen loop guards against it
- `seasonal` / `ecology_linked` regen models — out of scope (post-E21)
- `ECOLOGY_INTERVAL` value — do not change
- `ResourceNodeUpdate.charges_set` — do not add this field; use `charges_delta` only
- `E21C` depletion-aware scoring — not in this ticket

---

## Deviations

1. **Ticket pseudocode used `charges_set` — corrected to `charges_delta`.**
   `ResourceNodeUpdate` has no `charges_set` field (confirmed by investigation §4). The regen loop uses `charges_delta = min(max_charges, remaining + rate) - remaining` as specified in the plan. The ticket body pseudocode was stale and the plan correctly overrode it.

2. **`region_id=None` used for both events (plan matched, ticket pseudocode didn't).**
   Both `RESOURCE_DEPLETED` and `RESOURCE_RECOVERED` emit with `region_id=None`. This was a plan decision (OPEN-3 resolved). The ticket pseudocode implied `<node's region>` but region lookup via `LegalityServiceV2` was explicitly ruled out as out of scope for E21B.

3. **Test fixtures required `kind="WOOD"` not `kind="STONE"`.**
   The test helper `_make_node()` was written with `kind="STONE"` initially. At test runtime, the item registry bootstraps only catalog items; `stone` is not registered. Fixed to use `kind="WOOD"` (registered catalog item). Also: full-inventory sentinel needed `quantity=20` (full stack size) not `quantity=1`. These are test-only corrections; no implementation changed.

4. **Two emission sites in `economy.py` (L127 and L214), not one.**
   The economy module has two separate code paths for resource node interactions. Both were instrumented with the `RESOURCE_DEPLETED` guard. This is consistent with the plan's intent (emit at all accepted-harvest sites) but the plan described one location.
