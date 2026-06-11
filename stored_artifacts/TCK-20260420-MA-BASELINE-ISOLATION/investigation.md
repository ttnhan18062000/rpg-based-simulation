---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260420-MA-BASELINE-ISOLATION
artifact_type: investigation
tags: [ma, baseline, isolation]
---

# Investigation - Milestone A Isolation (TCK-20260420-MA-BASELINE-ISOLATION)

## Problem
The `Kernel` is currently dependent on the `WorkerPacket` and `WorkerManager` structures for all simulation execution, even in single-process mode. This makes the "semantic baseline" dependent on the "concurrency plumbing," which is against the Milestone A core-law intent.

## Current State
- `Kernel._phase_collection` manual loop (lines 161-235) builds packets for every item.
- `WorkerManager` is always used, even if local fallback is triggered.
- No abstraction exists to swap out execution strategies.

## Target State
- `Kernel` delegates to a strategy-injected `IWorkExecutor`.
- `LocalSequentialExecutor` handles local runs without packets.
- `ConcurrentExecutionAdapter` handles worker-based runs.
