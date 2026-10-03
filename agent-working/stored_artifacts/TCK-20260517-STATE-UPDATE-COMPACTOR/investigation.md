---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260517-STATE-UPDATE-COMPACTOR
artifact_type: investigation
tags: [state, update, compactor]
---

# Investigation Notes: StateUpdateCompactor

## Hotspot Analysis
Profiling results in `perf_test_plan.md` show that `apply_generation` in `ApplyPath` is a top consumer of CPU time (`~54s` in movement/resource benchmarks). Specifically, dataclass `replace()` calls and dictionary mutations inside `_apply_entity_update_to_dict` dominate this cost.

During high-concurrency ticks or large-scale multi-agent simulations, systems frequently emit `EntityUpdate` records that contain no-op deltas (e.g., `hp_delta=0`, progress deltas of 0, attribute changes equal to current entity state). 

## Compaction Strategy
By intercepting `StateUpdate` before `ApplyPath` processes it:
1. We iterate over `update.entity_updates`.
2. For each `EntityUpdate`, we compare its property updates against existing entity fields (`getattr(entity, key)` and `entity.identity.properties.get(key)`). If they match, we strip them.
3. We inspect all 15 subcomponent update objects (`combat`, `inventory`, `navigation`, `biological`, etc.). If `sub.is_noop()` is True, we replace the subcomponent with `None`.
4. If the resulting `EntityUpdate.is_noop()` is True, we drop the entity from `entity_updates` entirely.

This guarantees fewer iterations and fewer dataclass `replace()` allocations in `ApplyPath`, ensuring faster tick resolution without any loss of authoritative accuracy.
