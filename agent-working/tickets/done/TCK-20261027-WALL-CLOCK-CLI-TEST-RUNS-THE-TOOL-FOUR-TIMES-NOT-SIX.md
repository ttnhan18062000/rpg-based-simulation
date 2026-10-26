---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261027-WALL-CLOCK-CLI-TEST-RUNS-THE-TOOL-FOUR-TIMES-NOT-SIX
phase: done
date: 2026-10-27
tags: [testing, determinism]
---

# TCK-20261027-WALL-CLOCK-CLI-TEST-RUNS-THE-TOOL-FOUR-TIMES-NOT-SIX

## Title
The wall-clock inventory CLI test runs the tool over the real source four times instead of six, so it stops hitting the 60 s per-test budget under load

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by agent-working-implementer in the full `tests/tools` run for PR #754 (2026-10-26/27). The question of whether it
needed a ticket came from lead-planner, and agent-working-planner decided yes.
`tests/tools/test_wall_clock_inventory.py::test_cli_runs_are_byte_identical_and_do_not_import_src` fails the 60 s per-test
budget under modest load: 60.02 s on origin/main 3533fde71 and 60.05 s on the #754 branch, back to back; an earlier branch
run passed at 62 s. It runs `tools/perf/wall_clock_inventory.py` over the real `src/` six times: json x3 (the third only
for `json.loads`), md x2, and once more in-process in the probe that checks that no `src` module is imported. This is the
third load-sensitive test in `tests/tools` in a week, after TCK-20261025-HANGING-GH-TEST-BOUND-RELATIVE-TO-BASELINE and
TCK-20261026-VALIDATE-SPLIT-GLOBS-EXPANDED-ONCE.

## Scope
1. Test-only change in `tests/tools/test_wall_clock_inventory.py`. Keep all three assertions (json byte-identical, md
   byte-identical, no `src` import) and cut the tool runs over the real `src/` from 6 to 4:
   - Parse the `json.loads` check from one of the two json runs already made; no third json run.
   - Have the probe print the tool's captured stdout as well as the import flag, and compare that captured json with a
     subprocess json run. The probe is then one of the two json runs, which keeps the cross-process byte-identity check.
2. Measure it alone and under the same back-to-back load as the original evidence, before and after, and record the
   numbers in Test Summary.
3. Don't change `tools/perf/wall_clock_inventory.py` (perf-owned). If 4 runs still sit near the budget, stop and report:
   speeding up the tool is a perf-planner request, not this ticket.

## Out of Scope
- The tool itself; the 60 s per-test budget; marking the test `slow` (that would hide it from the default run).

## Acceptance Criteria
1. The test still fails if json or md output differs between runs, or if running the tool imports `src` (show this by
   mutating a copy locally; record that it was done; don't commit the mutation).
2. The test makes 4 full tool runs over the real `src/`, not 6.
3. The before/after timings are recorded, and the after time is well under 60 s under the same load.

## Related Tickets
- TCK-20261025-HANGING-GH-TEST-BOUND-RELATIVE-TO-BASELINE
- TCK-20261026-VALIDATE-SPLIT-GLOBS-EXPANDED-ONCE
- TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION (batch PR #754, where the failure was seen)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tests/tools/test_wall_clock_inventory.py
- tools/perf/wall_clock_inventory.py (read only)

## Assumptions / Open Questions
- The probe can print both the captured output and the flag on separate lines without changing what the tool does.

## Implementation Notes
Separate PR after #754 (u24 sequencing; planner decision 2026-10-27), not folded into #754. Opened from origin/main after #754 merges.

The probe now writes the tool's captured json to stdout followed by a marker line with the `src`-import flag; the probe's json is compared with one subprocess json run (cross-process byte identity), `json.loads` reads that same run, and md is still run twice: 4 tool runs over the real src/.

## Test Summary
Timings, 2026-10-27, quiet host (loadavg1 0.5-0.9), MemoryMax 3G, back to back, the CLI test alone: before (origin/main version) 52.1 s; after (4 tool runs) 31.7 s. The whole file after: 16 passed in 38.8 s. Even idle, the old test used 52 s of its 60 s budget.
Mutation checks on a throwaway copy (a wrapper in place of the tool that perturbs its output; not committed, files removed): json output nondeterministic -> the test fails; md output nondeterministic -> fails; the tool importing `src` -> fails (`'True' == 'False'`); no mutation (control) -> passes. The assertions are all kept.

## Files Changed
tests/tools/test_wall_clock_inventory.py

## Completion Summary
The wall-clock CLI test makes 4 tool runs over the real src/ instead of 6 and takes 31.7 s instead of 52.1 s on an idle host, with the same three assertions. The tool is untouched. Separate PR after #754.

