---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Deterministic Execution Contract

**Source:** `src/engine/kernel.py`, `src/engine/checkpoint.py` (CanonicalStateHasher), `src/core/determinism.py` (DeterministicRNG), `src/engine/pipeline.py`
**Related docs:** [kernel.md](kernel.md) (6-phase loop), [candidate_selection.md](candidate_selection.md) (ordering guarantees), [dirty_state_and_dependency.md](../core/dirty_state_and_dependency.md) (audit_dirty_set)

---

## Purpose

The determinism guarantee is: **same world seed + same initial `AuthoritativeState` → same `CanonicalStateHasher.get_hash()` after every tick.**

This guarantee is the foundation for replay fidelity, regression testing, and parity verification. Any code that violates it is a critical bug.

---

## Scope of the guarantee

**In scope:** Sequential execution mode. Every tick in a single-threaded simulation run is bit-identical given the same seed.

**Out of scope:** Concurrent execution mode. When multiple worker threads run in parallel, message delivery order is non-deterministic at the OS level. Known-limitations.md documents that bit-identical parity is ratified for sequential mode only. Concurrent mode is designed for throughput, not bit-exact determinism.

---

## The canonical hash

`CanonicalStateHasher.get_hash()` produces a SHA-256 of the world state after each tick. The hash input is a canonical sorted JSON representation:
- All dict keys sorted lexicographically
- All entity collections sorted by entity ID
- All floating-point values rounded to a fixed precision

This means the hash is independent of Python dict insertion order or object identity. Two `AuthoritativeState` objects that are semantically identical produce the same hash.

The hash is emitted in the `TICK_END` event in the warehouse (field: `tick_hash`). Replay divergence is detected by comparing `tick_hash` sequences.

---

## The four enforcement rules

### Rule 1: Stateless random numbers — `DeterministicRNG`

**Location:** `src/core/determinism.py`

```
DeterministicRNG.get_float(domain, tick, entity_id, sub_id) -> float
DeterministicRNG.get_int(domain, tick, entity_id, sub_id) -> int
```

Each call computes a composite seed: `base_seed ^ domain ^ tick ^ entity_id ^ sub_id`, then creates a **fresh** `random.Random(composite_seed)` and draws one value. This is **order-independent** — any domain can call `get_float()` in any order and always gets the same value for the same arguments.

**Forbidden:** `DeterministicRNG.next_float()` and `next_int()` — these are stateful sequential draws. They are deprecated and forbidden in concurrent contexts. Using them in a pipeline phase that may run out-of-order causes divergence.

Other forbidden operations in tick-path code:
- `random.random()` (global mutable state)
- `time.time()` or any wall-clock read
- `os.getpid()` or process/thread ID reads
- Reading external files or network during tick resolution

### Rule 2: Deterministic worker result ordering

**Location:** `src/engine/kernel.py:449`

After all workers complete, their results are sorted before resolution:

```python
sorted(results, key=lambda r: (r.class_priority, -r.local_priority, r.entity_id))
```

`entity_id` is the tiebreaker — no two entities have the same ID, so the ordering is always stable and total.

### Rule 3: Read-only worker state

Workers receive `AuthoritativeState.readonly_view()` — a frozen snapshot. Any attempt to mutate durable state from a worker (outside the authoritative apply path) is a protocol violation caught by audit mode.

### Rule 4: Deterministic candidate sets

All entity selection operations produce `tuple(sorted(...))` results. See [candidate_selection.md](candidate_selection.md) for the three-tier selection system.

---

## Divergence detection tools

### `audit_mode`

When `kernel.audit_mode = True`, the engine fires `ProtocolViolationError` if `CanonicalStateHasher.get_hash()` changes during a non-mutating phase. This catches accidental mutations in read-only phases (e.g. a domain service writing directly to entity state rather than producing an intent).

### `audit_dirty_set=True`

Enables `DirtySetLeakError` — raised when a phase marks a dirty flag that it should not have access to. See [dirty_state_and_dependency.md](../core/dirty_state_and_dependency.md) for the 9-entity / 8-world-object flag taxonomy and which flags each phase may set.

### Replay tick_hash comparison

A reference run stores the `tick_hash` sequence from the `TICK_END` warehouse events. A regression run replays the same seed and compares tick_hash at each step. First hash mismatch identifies the exact tick where divergence began.

### Checkpoint files

`checkpoint.py` supports writing and loading `AuthoritativeState` snapshots. A checkpoint captures the full state at a given tick — loading it and continuing the simulation must produce the same downstream tick_hash sequence as an uninterrupted run.

---

## Known non-determinism sources (pre-existing, out of scope to fix)

1. **Concurrent execution mode** — OS thread scheduling is non-deterministic. Only sequential mode is guaranteed.
2. **External I/O during live simulation** — if a campaign reads from a live file or socket during tick resolution, the read is non-deterministic (pre-existing: campaigns are analysis-only and run in isolation).
3. **Python float precision edge cases** — `CanonicalStateHasher` rounds floats to a fixed precision to mitigate this, but edge cases near rounding boundaries remain a known risk area.

---

## Regression tests

- `tests/integration/kernel/test_determinism.py` — same seed → same tick_hash for N ticks
- `tests/integration/kernel/test_replay.py` — checkpoint load → resume → same hash sequence
- `tests/certification/test_determinism_certification.py` — P0 hard gate; must pass for release

---

## Extension rules

1. Any new tick-path code that needs a random value MUST use `DeterministicRNG.get_float()/get_int()` with all four parameters. Never use stateful draws.
2. Any new pipeline phase MUST produce a candidate set via `tuple(sorted(...))`.
3. Any new worker that might mutate state must go through the authoritative apply path — never mutate `AuthoritativeState` directly in a worker.
4. If a new source of non-determinism is intentionally introduced (e.g., a live-data feature), it must be documented in known_limitations.md with its scope and rationale.
5. `audit_mode` should be enabled in all CI runs that verify the determinism guarantee.
