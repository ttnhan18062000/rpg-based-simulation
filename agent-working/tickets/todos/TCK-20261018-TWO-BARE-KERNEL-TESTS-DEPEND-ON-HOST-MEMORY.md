---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261018-TWO-BARE-KERNEL-TESTS-DEPEND-ON-HOST-MEMORY
phase: open
date: 2026-10-18
tags: []
---

# TCK-20261018-TWO-BARE-KERNEL-TESTS-DEPEND-ON-HOST-MEMORY

## Title
Two tests that build a bare Kernel fail when the pytest process is large

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found while fixing TCK-20261018-REPLAY-NON-AUTHORITATIVE-TEST-INDEPENDENT-OF-HOST-MEMORY. A Kernel built with the default governor reads host RSS against the profile's memory cap. Above it (about 512 MB for the test profile in that case) the kernel drops to SURVIVAL, replay is switched off, and anything asserting on replay or on the mode goes red. A whole-red-list run reaches that size late in the process.

## Scope
Make these two tests independent of host memory:
- tests/unit/resource/test_resource_governor_contract.py::test_real_kernel_with_workers_disabled_stays_normal_absent_real_pressure
- tests/unit/core/test_operational_flags.py::test_no_replay_stops_the_replay_sink

Reproduction: run either file inside a process holding a 1500 MB ballast (allocate and touch a bytearray, then call pytest.main with --resource-budget off). Both pass with no ballast and fail with it; the other 52 tests in the 14 candidate files pass in both cases.

Judgement left to this ticket: the governor-contract test asserts the kernel "stays normal ABSENT real pressure", so the right fix may be zeroed signals (audit_mode, or a governor with zeroes_signals) rather than PinnedNormalGovernor, which would hide the very mode it checks. The test may also legitimately read the host, in which case it should say so and not be pinned. Decide per test; the established pin is tests/helpers/kernel_pinning.py.

## Out of Scope
Any src change. Bare-Kernel files outside the 14 candidates I ran were not checked and may share the exposure (candidates: bare Kernel, no PinnedNormalGovernor/audit_mode, asserting on replay or mode); a sweep is a separate decision.

## Acceptance Criteria
Both tests pass at 0, 100, 400, 700 and 1500 MB ballast with their assertions still meaning what they say; tests/unit/kernel and the two files pass with --resource-budget off.

## Related Tickets
TCK-20261018-REPLAY-NON-AUTHORITATIVE-TEST-INDEPENDENT-OF-HOST-MEMORY

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
tests/unit/resource/test_resource_governor_contract.py; tests/unit/core/test_operational_flags.py; tests/helpers/kernel_pinning.py

## Assumptions / Open Questions
Whether the governor-contract test should be pinned, zeroed, or keep reading the host.

## Implementation Notes
Not started.

## Test Summary
Not run.

## Files Changed
This ticket file only.

## Completion Summary
Open.
