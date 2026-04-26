# Milestone 8 Test Matrix

| Test Group | Input Condition | Expected Result | Regression Caught |
| :--- | :--- | :--- | :--- |
| **Worker Determinism** | Same Seed, Local vs Concurrent | Bit-identical `AuthoritativeState` | Race conditions / drift. |
| **Worker Bounds** | `max_worker_count=2` | No more than 2 threads active | Profile violation. |
| **Queue Fallback** | `max_queue_depth=1` + 2 tasks | 1 task in pool, 1 executed locally | Queue blowup / stall. |
| **Packet Discipline** | Entity A action | Packet contains A + neighbors (subset) | World-clone leakage. |
| **Shutdown** | Call `shutdown()` while work inflight | All threads terminated, data captured | Hang or data loss on exit. |

## Verification Command
```bash
pytest tests/engine/test_worker_determinism.py
pytest tests/engine/test_worker_bounds.py
pytest tests/engine/test_worker_fallback.py
```
