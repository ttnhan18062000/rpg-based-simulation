---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21B-REGEN-SERVICE
artifact_type: investigation
tags: [resource-ecology, regeneration, event-emitter, phase-2]
---

# Investigation — TCK-20260619-E21B-REGEN-SERVICE
## Epic 2.1B · Depletion Emitter + Charge Regen Loop

---

## Current Behavior

### 1. `RESOURCE_DEPLETED` emitter — absent

**Where charges are decremented:**
- `src/core/conservation.py:L91–L95` — `ResourceTransactionResolver.resolve()` handles
  `intent.source_kind == "NODE"`. On success it returns:
  ```python
  delta = -node.remaining_charges if node.kind == "LOOT" else -1
  return TransactionResult(accepted=True, ...,
      node_update=ResourceNodeUpdate(node_id=intent.source_id, charges_delta=delta))
  ```
  This is where the charge is subtracted. No depletion event is emitted here.

- `src/engine/economy.py:L278–L284` — `ResourceTransactionSystem._apply_world_effects()`
  accumulates `node_update.charges_delta` into `new_node_updates` dict. No depletion
  event is emitted here either.

- `src/engine/apply_plan.py:L141–L161` — Applies `n_upd.charges_delta` to produce
  `new_charges = node.remaining_charges + n_upd.charges_delta` and calls
  `replace(node, remaining_charges=new_charges, ...)`. Transition from `> 0` to `== 0`
  is detected for active-node-grid purposes (L144–L160) but **no WorldEvent is emitted**.

**Summary:** The full call chain is
`InteractionSystem.enforce()` (L132–L173) → `ResourceTransferIntent` with `source_kind="NODE"` →
`ResourceTransactionSystem.resolve_all()` → `ResourceTransactionResolver.resolve()` →
`_apply_world_effects()` (accumulates `node_updates`) → `ApplyPath` (applies charges_delta).
`RESOURCE_DEPLETED` is never constructed or appended at any point in this chain.

### 2. `WorldEvent` / `recent_world_events` — storage mechanism absent

- `StateUpdate` (`src/core/updates.py:L820–L862`) has **no `world_events` field**.
  There is no bucket on `StateUpdate` for carrying `WorldEvent` objects out of
  any phase.

- `AuthoritativeState` (`src/core/state.py:L984–L1051`) has **no `recent_world_events`
  field**. The pipeline at `src/engine/pipeline.py:L212` reads it via:
  ```python
  recent_world_events = getattr(state, "recent_world_events", [])
  ```
  The `getattr(..., [])` fallback confirms the field does not exist. `WorldEmergencePhase`
  always receives an empty list.

- `src/engine/apply.py:L310–L355` — `AuthoritativeState(...)` constructor call lists
  every field explicitly. `recent_world_events` is not passed.

### 3. `ResourceEcologyService.process_ecology()` — regen loop absent

- `src/world/ecology.py:L19–L76` — The method only seeds **new** nodes (nodes_add path).
  It never iterates existing `state.resource_nodes` to apply `regen_rate_per_tick`.
  Return is `StateUpdate(nodes_add=..., next_node_id_set=...)` — no `node_updates`,
  no events.

### 4. `ResourceNodeUpdate` — delta-only, no `charges_set`

- `src/core/updates.py:L699–L712` — `ResourceNodeUpdate` has `charges_delta: int = 0`
  and `cooldown_set: Optional[int] = None`. There is **no `charges_set` field** (absolute
  assignment). The ticket scope pseudocode uses `charges_set=new_charges` — this field
  does not exist. The regen loop must use `charges_delta` instead:
  ```python
  charges_delta = new_charges - node.remaining_charges  # always positive
  ```

### 5. Cooldown-recharge path (world_dynamics) — must not conflict

- `src/engine/world_dynamics.py:L162–L174` — On every tick, for nodes with
  `cooldown_remaining > 0`, `WorldDynamicsSystem` either decrements cooldown or
  (when `cooldown_remaining == 1`) sets `cooldown_set=0, charges_delta=node.max_charges`.
  This is a full-recharge-from-cooldown path, distinct from the regen-rate path.
  **Both paths write to `StateUpdate.node_updates` via `charges_delta`**, so they can
  coexist without conflict as long as regen only fires when `cooldown_remaining == 0`
  (node is not in cooldown). The guard must be: skip regen if `node.cooldown_remaining > 0`.

### 6. `RESOURCE_RECOVERED` / `RESOURCE_DEPLETED` enum — already present (E21A done)

- `src/domains/world_emergence/schema.py:L12–L17` — Both `RESOURCE_DEPLETED` and
  `RESOURCE_RECOVERED` exist in `WorldEventCategory`. `WorldEvent` dataclass at L31
  is fully defined. E21A is confirmed done.

- `src/core/state.py:L820` — `regen_rate_per_tick: int = 0` field exists on
  `ResourceNodeState`. `to_canonical_dict()` at L840 includes it. E21A confirmed.

### 7. `ecology.py` — `ResourceNodeState` constructor call

- `src/world/ecology.py:L62–L70` — New nodes are constructed without `regen_rate_per_tick`
  (falls back to default `0`). Per ticket scope §3, harvestable nodes (IRON, WOOD, STONE)
  should set `regen_rate_per_tick=1` here.

### 8. World emergence consumers already handle `RESOURCE_DEPLETED`

- `src/domains/world_emergence/models.py:L100, L164` — `WorldPressureEvaluator` and
  `ResourceScarcityEvaluator` both branch on `WorldEventCategory.RESOURCE_DEPLETED`.
  These are consumers awaiting events that never arrive. They will work correctly once
  events are emitted.

---

## Mechanics/Engine Constraints

- **Ecology cadence:** `ECOLOGY_INTERVAL = 200` ticks (`src/world/ecology.py:L16`).
  `docs/world/ecology_and_calamity_contract.md §Tick cadence`. Regen fires every 200
  ticks, not every tick. A node with `max_charges=5` and `regen_rate_per_tick=1` takes
  1000 ticks (5 ecology intervals) to fully recover.

- **Atomic Conservation Law (`docs/mechanics/03_economic_laws.md`):** Source depletion
  and inventory receipt are atomic. `RESOURCE_DEPLETED` must only emit when the
  `charges_delta` actually commits — i.e. when `TransactionResult.accepted=True` and the
  final `new_charges == 0`. The safe injection point is after `_apply_world_effects()`
  accumulates the node update into `new_node_updates` in `economy.py`, where the
  accepted state and final delta are both known.

- **Durable state rule:** `WorldEvent` objects survive beyond the current tick only if
  stored on `AuthoritativeState.recent_world_events`. This field must be added to both
  `StateUpdate` (as `world_events_add: List[WorldEvent]`) and `AuthoritativeState` (as
  `recent_world_events: List[WorldEvent]`) with a rolling window (e.g. last 500 events,
  or last N ticks).

- **No `charges_set` on `ResourceNodeUpdate`** — regen must use
  `charges_delta = min(max_charges, remaining + rate) - remaining`.

- **Authoritative pipeline rule:** Events emitted in `economy.py` (Phase 6) are too late
  for `WorldEmergencePhase` (Phase 8, runs _after_ economy in pipeline.py). Events emitted
  in ecology (inside `WorldDynamicsSystem`, Phase 5) arrive before Phase 8. The DEPLETED
  event from economy.py will appear in `recent_world_events` on the _next_ tick only, which
  is correct — emergence analysis is retrospective.

---

## Parity Ledger Overlap

Checked `docs/parity_ledger/town_resource.yaml`. Relevant entries:

| ID | Text | Status | Relevance |
|---|---|---|---|
| TOWN-114 | Harvest completion emits both inventory addition and node depletion atomically. | `verified` | Covers atomic delta — DEPLETED event is additive, does not break this |
| TOWN-136 | Resource-node cooldown behavior is deterministic. | `verified` | Regen loop must not interfere with cooldown path in world_dynamics |
| TOWN-137 | Resource-node recharge behavior is deterministic. | `verified` | Will need `v2_evidence` update to reference regen loop |
| TOWN-138 | Resource-node depletion state survives serialization. | `verified` | Depletion event itself doesn't need serialization (ephemeral WorldEvent) |

**New entries required** (no existing entry covers these behaviors):
- `TOWN-173`: `RESOURCE_DEPLETED` event is emitted when node charges reach 0 after a
  successful harvest. Status: `missing` → will be `verified` after E21B.
- `TOWN-174`: `RESOURCE_RECOVERED` event is emitted when a depleted node gains charges
  via the regen loop. Status: `missing` → will be `verified` after E21B.
- `TOWN-175`: `remaining_charges` increases by `regen_rate_per_tick` per ecology interval,
  capped at `max_charges`, and only when `cooldown_remaining == 0`. Status: `missing` →
  will be `verified` after E21B.

---

## Prior Work

### E21A (TCK-20260619-E21A-NODE-SCHEMA) — DONE
- Added `regen_rate_per_tick: int = 0` to `ResourceNodeState` (`src/core/state.py:L820`).
- Added `regen_rate_per_tick` to `to_canonical_dict()` (`src/core/state.py:L840`).
- Added `RESOURCE_RECOVERED` to `WorldEventCategory` (`src/domains/world_emergence/schema.py:L17`).
- Tests in `tests/unit/resource/test_resource_contract.py:L126–L145` (AC1–AC4 verified).
- No regen logic, no event emission added (correctly deferred to E21B).

### Parent Epic (TCK-20260619-E21-RESOURCE-ECOLOGY) — DONE (scoped)
- Defined 4 child tickets: E21A (schema), E21B (this), E21C (scoring), E21D (verification).
- Confirmed ecology runs every 200 ticks; ecology service is wired in pipeline Phase 5.

### Audit Finding 5 (`docs/audits/D02_foundation_features.md:L867`)
- Score 19/50. Gap: "regeneration cycles not implemented."
- Downstream risk rated 7/10: "Economy stagnates without regeneration."
- Test shield rated 2/10: "nothing to test" — confirms no ecology regen tests exist yet.

---

## Risks and Open Questions

### OPEN-1 — RESOLVED: Where to inject `RESOURCE_DEPLETED` emission

**Decision: Option A — `src/engine/economy.py:_apply_world_effects()`.**
Rationale: closest to the acceptance decision; consistent with "emitter at resolution site" pattern. Implemented at `src/engine/economy.py:L127` and `L214`. Guard: `old_charges > 0 and new_charges <= 0`.

### OPEN-2 — RESOLVED: `recent_world_events` rolling window

**Decision: window = 500 events (tail slice, not tick-filtered).**
`ApplyPath.apply_generation()` computes: `merged[-WORLD_EVENT_WINDOW:]` (constant `WORLD_EVENT_WINDOW = 500`). Implemented at `src/engine/apply.py:L311–L313`.

### OPEN-3 — RESOLVED: `region_id` for `WorldEvent`

**Decision: `region_id=None` (cheap path).**
Region lookup via `LegalityServiceV2.get_region_for_position()` not required for E21B. Both `RESOURCE_DEPLETED` (economy.py) and `RESOURCE_RECOVERED` (ecology.py) emit with `region_id=None`. WorldEmergence consumers do not require `region_id` for DEPLETED/RECOVERED branching.

### OPEN-4 — RESOLVED: Cooldown vs regen guard

**Decision: skip regen if `node.cooldown_remaining > 0`.**
Implemented in `src/world/ecology.py:L35`. Nodes in cooldown are exclusively owned by the `world_dynamics.py` path. Test: `test_regen_skipped_during_cooldown`.

### OPEN-5 — RESOLVED: `regen_rate_per_tick=1` scope

**Decision: ecology-seeded nodes only** (`src/world/ecology.py:L96`).
`src/worldbuilding/compiler.py` is NOT updated — compiler-seeded (pre-placed) nodes retain `regen_rate_per_tick=0` as static/permanent nodes. This matches the ticket scope guard explicitly.

---

## Anti-Drift Hazards

1. **Do not add `charges_set` to `ResourceNodeUpdate`** — it is not in the ticket scope
   and would require updating `merge()` and `apply_plan.py`. Use `charges_delta` only.

2. **Do not emit `RESOURCE_DEPLETED` in the `InteractionSystem`** — that runs before
   `ResourceTransactionResolver` and does not have confirmation that the transaction was
   accepted. Only emit after `TransactionResult.accepted=True` is confirmed.

3. **Do not emit `RESOURCE_DEPLETED` more than once per depletion** — guard:
   `old_charges > 0 and new_charges <= 0`. Without the guard, multi-entity harvests on
   the last charge in the same tick could fire multiple events.

4. **Do not let regen fire during cooldown** — guard: `node.cooldown_remaining == 0`.
   Nodes in cooldown are managed by `world_dynamics.py`; regen-path overlap would set
   charges on a node that is supposed to be regenerating via cooldown only.

5. **Do not break `StateUpdate.is_noop()`** — if `world_events_add` is added to
   `StateUpdate`, update `is_noop()` to include `not self.world_events_add`.

6. **Do not break `StateUpdate.merge_many()`** — `world_events_add` must be
   concatenated (list extend), not overwritten.

7. **`ecology.py` calls `LegalityServiceV2.get_region_for_position()` inside a loop** —
   this is already the pattern for existing code in that method. Do not introduce a
   spatial index dependency that is unavailable in test contexts.
