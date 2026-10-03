---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-HARD-LAW
artifact_type: investigation
tags: [sim, obs, hard, law]
---

# Investigation - HardLawMonitor V1 & Observability Config

This document records the architectural findings and research conducted for the HardLawMonitor implementation.

## Key Findings

### 1. Authoritative Phase Hooks
The Kernel runs in sequential phases. State advancement commits all refined pipeline updates into the `self._state` field in `Kernel._phase_advancement()`.
The ideal place to hook the `HardLawMonitor` check is immediately following `self._phase_advancement()`, before replay events are finalized and before persistence commits the state.
This prevents corrupted states from being written to durable logs in fail-fast modes (`DEBUG`, `CERTIFICATION`).

### 2. Efficient O(1) Checks
To avoid expensive full-world O(N) loops over all entities every tick:
- We check only the entities marked dirty in `dirty_set`.
- For occupancy collisions, we only check dirty moving entities (`dirty_set.movement_entities`) against the authoritative `entities_by_tile` spatial index, which is rebuilt efficiently inside `WorldIndexService.get_indexes` only when movement or lifecycle updates occur. This guarantees `O(1)` tile lookups per dirty mover.

### 3. Metric Exporters
`V2EngineManager` acts as the collector registry wrapper and regularly snapshots state and pressure variables inside `_update_latest_state`.
By tracking the cumulative count of violations in a dictionary on `RuntimeStatus`, `PrometheusMetricsCollector` can safely scrape these metrics from the manager's recent snapshot with zero runtime concurrency overhead.
