---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261020-PERF-PYSPY-TOOLKIT-TEST-MEASURED-WINDOW
phase: done
date: 2026-10-20
tags: [performance, testing]
---

# TCK-20261020-PERF-PYSPY-TOOLKIT-TEST-MEASURED-WINDOW

## Title
The py-spy end-to-end toolkit test measures too few ticks to be sampled reliably on a loaded host

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`tests/tools/test_profiling_toolkit.py::test_end_to_end_tiny_profile_with_py_spy` failed once on 2026-10-20 in the tests/tools heavy slot under I/O load: `No sampled stack contained the measured-ticks frame; raise --ticks or --rate. Total samples: 210`. The test ran `profile_tick` with `--ticks 4`; four ticks of a 20-entity idle world take a few ms, so on a loaded host every sample can land in startup or imports. Re-run alone at load 1.7: 27/27 passed.

## Scope
- Raise `--ticks` in that one test (4 -> 40) so the measured window is long enough to be sampled.

## Out of Scope
- `profile_tick.py` and its "no measured-ticks frame" refusal (correct behaviour, unchanged).
- Catching the error in the test, retry loops, changing the 240 s timeout.

## Acceptance Criteria
1. The test passes 10 of 10 consecutive solo runs and each run stays within a few seconds.
2. `profile_tick.py` is unchanged; the test still asserts the PROVISIONAL marker in all four outputs.

## Related Tickets
- TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP (unrelated; its branch is untouched)

## Related Docs
- `docs/performance/` (profiling toolkit)

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tests/tools/test_profiling_toolkit.py`
- `tools/perf/profile_tick.py` (unchanged)

## Assumptions / Open Questions
- Cause is inferred from the error text and the sample count, not reproduced under load; the failure is intermittent.

## Implementation Notes
`--ticks 4` -> `--ticks 40` in the end-to-end test. `--rate` left alone: ten runs passed without it.

## Test Summary
Ten consecutive solo runs: 10/10 passed, 2.61-3.34 s each (pytest wall). Load average 1.4-1.6 for runs 1-5, 3.1-3.5 for runs 6-10 (other sessions' load; I created none), all passed.

## Files Changed
- `tests/tools/test_profiling_toolkit.py`

## Completion Summary
The end-to-end test now measures 40 ticks instead of 4, which gives the sampler a window it can hit on a loaded host. The tool's refusal is untouched. 10/10 solo runs passed; the original failure was not reproduced under load, so the cause rests on the error text and sample count.
