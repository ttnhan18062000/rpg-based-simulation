---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260419-MC-TASK2-HARDEN-REPLAY-STAGING
phase: done
date: 2026-04-19
tags: [mc, task2, harden, replay, staging]
---

# TCK-20260419-MC-TASK2-HARDEN-REPLAY-STAGING

## Title
Milestone C - Task 2: Harden Replay Staging and Chunk Rotation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Ensure replay behavior is fully exact and bounded under normal and pressured conditions.

## Scope
- Verify `ReplayBuffer` capacity enforcement.
- Harden deterministic chunk rotation and saturation guards.
- Prove sink-pressure resilience.

## Acceptance Criteria
- [x] `ReplayBuffer` capacity is strictly enforced via `BoundedBuffer`.
- [x] Saturation guard (0.9 threshold) triggers rotation.
- [x] Replay emission is non-authoritative and non-blocking.

## Implementation Notes
- Verified `ReplayManager.on_tick_end` correctly triggers rotation on 90% buffer utilization.
- Verified `ReplayBuffer` correctly drops oldest events on overflow.

## Test Summary
- `tests/engine/test_replay_overflow.py` PASS
- `tests/engine/test_replay_pressure.py` PASS

## Files Changed
- `src/engine/replay_buffer.py`
- `src/engine/replay_manager.py`

## Completion Summary
Replay staging hardened and verified under pressure.
