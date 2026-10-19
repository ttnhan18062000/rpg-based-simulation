---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261018-REPLAY-NON-AUTHORITATIVE-TEST-INDEPENDENT-OF-HOST-MEMORY
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-REPLAY-NON-AUTHORITATIVE-TEST-INDEPENDENT-OF-HOST-MEMORY

## Title
Make test_replay_is_non_authoritative independent of host memory

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
rpg-planner dispatch: the test failed (persist_chunk never called) in long processes. Root cause: it builds a Kernel with the default governor, which reads host RSS against the test profile's 512 MB cap; above it the kernel drops to SURVIVAL, replay_allowed is False, no TICK_END is emitted, no chunk rotates. Pre-existing on origin/main (reproduced on 01296562a with a 700 MB ballast).

## Scope
tests/unit/kernel/test_replay_contract.py: build the Kernel with the established PinnedNormalGovernor (tests/helpers/kernel_pinning.py) and LocalSequentialExecutor. The assertion is unchanged.

## Out of Scope
Fixing the other tests with the same exposure (listed in Implementation Notes); any src change.

## Acceptance Criteria
The test passes at 0, 100, 400, 700 and 1500 MB ballast; tests/unit/kernel passes.

## Related Tickets
None.

## Related Docs
docs/performance/phase_inventory.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
tests/unit/kernel/test_replay_contract.py

## Assumptions / Open Questions
None.

## Implementation Notes
Reproduced before the fix: 700 MB ballast fails, 100 and 400 MB pass. After: 0/100/400/700/1500 MB all pass (2 tests). Same exposure, found by running 14 candidate files (bare Kernel, no pin or audit_mode, asserting on replay or mode) under a 1500 MB ballast: tests/unit/resource/test_resource_governor_contract.py::test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure and tests/unit/core/test_operational_flags.py::test_no_replay_stops_the_replay_sink fail; the other 52 pass. Listed only, not fixed.

## Test Summary
tests/unit/kernel: 82 passed before and after; ballast matrix above.

## Files Changed
tests/unit/kernel/test_replay_contract.py

## Completion Summary
Test pinned; assertion unchanged.
