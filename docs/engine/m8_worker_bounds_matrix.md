# Worker Bounds Matrix (Milestone 8)

| Bound Name | Purpose | Profile Source | Overflow/Violation Behavior |
| :--- | :--- | :--- | :--- |
| **Worker Count** | Limit parallel threads. | `max_worker_count` | `ThreadPool` size ceiling. |
| **Queue Depth** | Bound the work backlog. | `max_queue_depth` | **Immediate Local Execution**. |
| **Payload Scale** | Prevent RAM blowup. | `max_neighborhood_size`| Truncate distant neighbors. |
| **Tick Budget** | Limit overall latency. | `max_tick_budget_ms` | `ResourceGovernor` shedding. |

## 1. Local Fallback Triggers
1.  **Queue Saturated**: Submitting the $N+1$-th task where $N = max\_queue\_depth$.
2.  **Resource Pressure**: Governor sets mode to `DEGRADED` or `SURVIVAL`. (Optimization to save thread context switching).
3.  **Profile Disability**: `max_worker_count` set to 0.

## 2. Forbidden Behavior
- **Authoritative Mutation**: Workers must never directly modify the `AuthoritativeState` instance.
- **Global Locking**: Workers must not take locks on global registry or world objects.
- **Side Effects**: Workers must not trigger IO, Replay, or external API calls. (Pure logic only).

## 3. Regression Risk
- **Payload Leak**: If a worker receives a pointer to the whole world, `pickle` or serialization overhead will kill throughput.
- **Race Corruption**: If results are not sorted by ID, bit-identical determinism is lost.
