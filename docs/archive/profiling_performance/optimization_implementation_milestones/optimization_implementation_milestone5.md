# Milestone 5 — API and Replay Snapshot Optimization

## Objective

Avoid copying or serializing too much state every tick.

---

## Current likely issue

API manager currently deep-copies state every tick.

That is safe but expensive for large worlds.

---

## Target design

```text
minimal snapshot every tick
full snapshot only on request
paged/filtered inspect endpoint
compact replay deltas
bounded trace storage
```

---

## Technical tasks

### 5.1 Replace full deepcopy with snapshot DTO

Current behavior concept:

```python
self._latest_state = copy.deepcopy(state)
```

New behavior:

```python
self._latest_minimal_snapshot = StatePresenter.present_minimal(state)
```

Add:

```python
get_snapshot()
get_full_snapshot()
```

Keep `get_state()` only for internal/debug if needed.

---

### 5.2 Full inspect should be on-demand

For `/api/v1/inspect`:

```text
do not maintain full copy every tick
generate from current state under lock
or generate paged DTO
```

Better API:

```text
/api/v1/state              minimal
/api/v1/entities?offset=&limit=
/api/v1/entity/{id}
/api/v1/regions
/api/v1/groups
```

---

### 5.3 Bound replay and traces

Check these collections:

```text
transaction_trace
latest_intent_results
rejection_events
replay buffer
diagnostic history
strategic memory
```

Add limits:

```text
max_transaction_trace_per_tick
max_intent_results_per_entity
max_rejection_events_per_tick
max_replay_buffer_kb
```

---

### 5.4 Tests

Tests:

```text
API snapshot does not expose mutable AuthoritativeState
minimal snapshot update is below budget for 1000 entities
full inspect can page entities
replay buffer respects size limit
transaction trace is bounded
```

---

## Exit criteria

API and replay overhead does not grow linearly without control.

Benchmark:

```text
API snapshot for 1000 entities < target ms
API snapshot for 5000 entities still acceptable
memory_delta stable
```

---
