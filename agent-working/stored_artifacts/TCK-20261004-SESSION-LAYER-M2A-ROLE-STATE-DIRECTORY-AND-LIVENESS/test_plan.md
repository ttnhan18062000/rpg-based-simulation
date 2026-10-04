---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-SESSION-LAYER-M2A-ROLE-STATE-DIRECTORY-AND-LIVENESS
phase: open
date: 2026-10-04
tags: [ai]
---

# test_plan — TCK-20261004-SESSION-LAYER-M2A-ROLE-STATE-DIRECTORY-AND-LIVENESS

`tests/tools/test_session_state.py` (19): two worktrees share state and survive removal of one; live child reads live then orphaned after a real `kill -9` with no SessionEnd; forged pid-reuse start/cmdline reads orphaned; leftover socket file never makes live; released explicit and survives; lease retake/refuse/stale/key-by-physical-path; 240 parallel appends from 6 processes are 240 valid lines; typed errors; writes stay inside the state root.

## Proof Plan
- level: unit and integration with real git worktrees, real child processes, a real kill -9
- proof kind: automated tests
- oracle source: git, /proc and the real manifest
- expected effect: as stated in the ticket's acceptance criteria
- selected commands: `pytest tests/tools/test_session_state.py tests/tools/test_session_resolve_and_hook.py tests/tools/test_session_launch.py`
