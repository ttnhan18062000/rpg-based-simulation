# Investigation Notes - Phase Dependency Graph

## Current State
`AuthoritativeApplyPipeline.refine` currently executes 17 distinct phases grouped into 7 macro blocks. Some phases like `BuildingSabotage` and `TownResolution` are cadence-gated, but most optional phases run unconditionally even when their corresponding dirty domains are entirely empty.

## Opportunity
By checking `update.dirty_set` against each phase's required input domains, we can safely short-circuit optional phases when no relevant dirty entities exist. This reduces overhead from function calls, iteration setups, and intermediate object allocations.

## Determinism Guard
Phases that process external events or time-sensitive state transitions (e.g., Compactor, Trust Boundary, Actor Validity, Lifecycle) must remain marked as `must_run_every_tick` to ensure that spontaneous events (like aging or starvation) are never missed.
