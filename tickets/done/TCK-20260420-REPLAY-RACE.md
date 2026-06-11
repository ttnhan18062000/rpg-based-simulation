---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260420-REPLAY-RACE
phase: done
date: 2026-04-20
tags: [replay, race]
---

# TCK-20260420-REPLAY-RACE

## Title
Resolve Replay Manager Thread-Safety

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Resolve race conditions in ReplayManager where background persistence relied on shared state that could change before disk IO.

## Scope
- Implement `threading.Lock` for manifest updates.
- Capture chunk metadata snapshots in `_rotate_chunk`.
- Pass immutable snapshots to background threads.

## Acceptance Criteria
- [x] Disk IO uses the ID and tick range captured at rotation time.
- [x] Manifest updates are atomic.
- [x] 100% pass on determinism chaos tests.

## Completion Summary
Implemented thread-safe manifest management and snapshot-based persistence. Verified via `test_determinism_suite.py`.
