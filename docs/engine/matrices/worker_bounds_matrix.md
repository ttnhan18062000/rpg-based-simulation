---
status: active
layer: engine
authority: P1
audience: developer
---

# Worker Bounds Reference

Defines the resource boundaries for the concurrent worker pool. Every bound is sourced from the active runtime profile and enforced by the engine at runtime.

## Bound Summary

| Bound Name | Purpose | Profile Source | Overflow / Violation Behavior |
| :--- | :--- | :--- | :--- |
| **Worker Count** | Limit parallel threads. | `max_worker_count` | `ThreadPool` size ceiling. |
| **Queue Depth** | Bound the work backlog. | `max_queue_depth` | **Immediate local execution.** |
| **Payload Scale** | Prevent RAM blowup. | `max_neighborhood_size` | Truncate distant neighbors. |
| **Tick Budget** | Limit overall latency. | `max_tick_budget_ms` | `ResourceGovernor` shedding. |

## Local Fallback Triggers

Workers fall back to local execution when:
1. **Queue Saturated**: Submitting the (N+1)-th task where N = `max_queue_depth`.
2. **Resource Pressure**: Governor sets mode to DEGRADED or SURVIVAL (optimization to reduce thread context switching).
3. **Profile Disability**: `max_worker_count` set to 0.

## Forbidden Behavior

- **Authoritative Mutation**: Workers must never directly modify the `AuthoritativeState` instance.
- **Global Locking**: Workers must not take locks on global registry or world objects.
- **Side Effects**: Workers must not trigger IO, replay, or external API calls — pure logic only.

## Regression Risks

- **Payload Leak**: If a worker receives a pointer to the whole world, pickle or serialization overhead kills throughput.
- **Race Corruption**: If results are not sorted by ID, bit-identical determinism is lost.
