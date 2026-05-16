# Milestone 4 — Local vs Concurrent Determinism Parity

## Goal

Prove worker optimization does not change simulation truth.

The checklist claims adaptive chunking, parallel spatial neighbor calculation, and precomputed spatial/regional caches are implemented as performance laws.  The risk is not that concurrency is slow. The risk is that concurrency changes ordering, randomness, or proposal resolution.

## Tasks

| Task                                           | Narrow implementation logic                                               | Files / area    |
| ---------------------------------------------- | ------------------------------------------------------------------------- | --------------- |
| M4.1 Build executor parity harness             | Same initial state, same seed, same profile except executor/worker count. | tests helper    |
| M4.2 Run local sequential path                 | `LocalSequentialExecutor`, worker count 0 or 1.                           | kernel/executor |
| M4.3 Run concurrent path                       | concurrent adapter, worker count 2/4/8.                                   | kernel/executor |
| M4.4 Compare canonical hashes                  | Final state hash must match.                                              | tests           |
| M4.5 Compare rejected/accepted proposal counts | Not just final hash. Proposal acceptance behavior must be stable.         | diagnostics     |
| M4.6 Stress chunk-size boundaries              | Use entity counts around chunk boundaries: 49, 50, 51, 99, 100, 101.      | worker manager  |

## New tests to add

```python
def test_local_vs_concurrent_idle_parity_100_ticks():
    ...

def test_local_vs_concurrent_movement_parity_100_ticks():
    ...

def test_local_vs_concurrent_resource_parity_100_ticks():
    ...

def test_local_vs_concurrent_combat_parity_100_ticks():
    ...

def test_local_vs_concurrent_strategic_parity_100_ticks():
    ...

@pytest.mark.parametrize("entity_count", [49, 50, 51, 99, 100, 101])
def test_worker_chunk_boundary_determinism(entity_count):
    ...
```

## Acceptance checklist

```text
[ ] Same seed produces same final canonical hash in local and concurrent modes.
[ ] Proposal ordering is deterministic before authoritative resolution.
[ ] Chunk-size boundary cases are tested.
[ ] Worker spatial/regional cache path matches main-thread lookup behavior.
[ ] No bare random source is introduced in worker code.
[ ] Concurrency changes performance only, not game semantics.
```

## Exit condition

Concurrent optimization is safe to benchmark.

---
