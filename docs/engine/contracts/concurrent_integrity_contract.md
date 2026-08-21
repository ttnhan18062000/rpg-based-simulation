---
status: active
layer: engine
authority: P1
audience: developer
---

# Concurrent Integrity Contract

## Purpose
This document defines the operational lifecycle laws for the engine. It ensures that startup, persistence, runtime status, and shutdown behave as trustworthy contract paths, maintaining the non-authoritative boundary for all observational work.

See also: [`docs/architecture/kernel_concurrency_design_philosophy.md`](../../architecture/kernel_concurrency_design_philosophy.md)
Part 4/5, for how this contract's operational-lifecycle laws are a concrete instance of the
engine's broader Progressive Degradation design.

## Scope
- Hardening of the replay lifecycle (staging, rotation, manifest, pressure).
- Startup profile and operational flag validation.
- Deterministic shutdown sequencing with real timeouts.
- Runtime status truth-audit.

## Replay lifecycle law
1. **Non-Authoritative Boundary**: Replay failures (disk, memory, or logic) MUST NOT corrupt the authoritative game state or stall the kernel heart-beat.
2. **Replay Mode-Specific Retention**: 
   - `DEBUG_WINDOWED` (Default): Uses `EVICT_OLDEST` to preserve a recent window of trace context.
   - `FORENSIC_SHORT_RUN`: (Optional) May opt for `TRUNCATE_NEWEST` to guarantee early-tick integrity.
3. **Deterministic Rotation**: Chunks MUST rotate based on exact limits (`chunk_tick_limit` or `chunk_time_limit`). 
4. **Saturation Guard**: If the `ReplayBuffer` utilization exceeds a configurable threshold (default 0.9), an early rotation MUST be triggered immediately at the next tick boundary to prevent data loss.

## Manifest and sink-pressure law
1. **Atomic Manifest Updates**: All updates to `manifest.json` MUST use a temporary-write-then-rename strategy to ensure manifest integrity during crashes.
2. **Sink-Pressure Resilience**: If the `ReplaySink` (disk/IO) slows down, the `ReplayManager` MUST respond by increasing event shedding (degrading richness) or dropping events according to the buffer policy. It MUST NOT block the kernel on IO.
3. **Persistence Truth**: The manifest MUST accurately reflect the status of every chunk (In-progress, Persisted, or Failed).

## Startup validation law
1. **Profile Integrity**: All `RuntimeProfile` fields MUST be valid and internally consistent before the kernel initializes.
2. **Contradictory Rejection**: Impossible flag/profile combinations (e.g., `max_replay_buffer_kb > 0` with `REPLAY_DISABLED=True`) MUST be rejected with a `ConfigValidationError`.
3. **Required Fields**: Incomplete performance envelopes MUST be rejected.
4. **Warning-Only Feasibility**: Hardware class vs. tick budget mismatches MUST be treated as warnings, not rejections (see `extended_certification_contract.md`).

## Operational flag law
1. **Subordination**: Flags MUST remain subordinate to the resource contract. No flag may create alternate authoritative semantics.
2. **Forbidden Overrides**: Critical resource guards (e.g., `BYPASS_GOVERNOR`) remain hard-forbidden.
3. **Safe Overrides**: Only diagnostic or observational flags (e.g., `LOG_LEVEL`, `REPLAY_MODE`) are permitted at runtime.

## Shutdown timeout law
1. **Flush Budget**: Shutdown is a **5.0 second bounded non-authoritative flush budget**.
2. **Suspension**: The engine MUST first suspend new work arrival and stop producers (WorkerManager).
3. **Bounded Exit**: If sinks take longer than the budget to flush non-authoritative data, the engine MUST abort the remaining flushes and continue clean exit.
4. **Final Hash**: The terminal authoritative state hash MUST be emitted before the process terminates.

## Runtime snapshot law
1. **Truthful Source**: Every field in `RuntimeStatus` and `RuntimeSnapshot` MUST be wired to a real subsystem sensor (via `get_stats()`) or deleted. Placeholder metrics are forbidden.
2. **Boundedness**: Snapshots MUST remain typed, closed, and bounded. No open-ended telemetry dumps are permitted in the contract surface.

## Non-goals
- Deepening of the worker `TracePacket` or `WorkerResult` contracts.
- Feasibility certification scenario logic (Reserved for M9).
- New gameplay semantics or stat definitions.

## Guarantees
The engine operational lifecycle is considered "Finished Law." Any future failure in startup, persistence, or shutdown is treated as a contract violation (bug) rather than a known infrastructure gap.
