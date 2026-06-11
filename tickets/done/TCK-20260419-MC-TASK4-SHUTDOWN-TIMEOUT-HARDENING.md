---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260419-MC-TASK4-SHUTDOWN-TIMEOUT-HARDENING
phase: done
date: 2026-04-19
tags: [mc, task4, shutdown, timeout, hardening]
---

# TCK-20260419-MC-TASK4-SHUTDOWN-TIMEOUT-HARDENING

## Title
Milestone C - Task 4: Implement Shutdown Timeout and Manifest Integrity

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Ensure replay shutdown is bounded by a real timeout and final manifest integrity is prioritize.

## Scope
- Implement real shutdown budget check (5.0s).
- Ensure atomic `manifest.json` write-renaming.
- Verify background thread pool join/shutdown behavior.

## Acceptance Criteria
- [x] `ReplayManager.finalize` respects the `timeout_s` parameter accurately.
- [x] Manifest updates are atomic via `os.replace`.
- [x] Shutdown skips slow non-authoritative flushes to protect the manifest budget.
- [x] Non-blocking IO integration verified across all engine sinks.
- [x] Test matrix coverage includes high-concurrency stress tests.

## Implementation Notes
- Verify `ReplayBuffer` capacity enforcement.
- Harden deterministic chunk rotation and saturation guards.
- Implement Non-Blocking IO via background thread pool.
- Verified `ReplayManager.finalize` budget check using `perf_counter` and 0.5s safety margin.
- Implemented `tests/engine/test_manifest_integrity.py` to prove atomic write-rename behavior.

## Test Summary
- `tests/engine/test_non_blocking_io.py` PASS
- `tests/engine/test_manifest_integrity.py` PASS
- `tests/engine/test_replay_shutdown_budget.py` PASS
- `tests/engine/test_graceful_shutdown.py` PASS
- `tests/engine/test_io_matrix.py` PASS

## Files Changed
- `src/engine/replay_manager.py`
- `src/engine/replay_sink.py`
- `tests/engine/test_manifest_integrity.py`

## Completion Summary
Shutdown is now a bounded, trustworthy contract path.
