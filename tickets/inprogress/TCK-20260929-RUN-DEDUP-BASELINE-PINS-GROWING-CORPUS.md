---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS
phase: open
date: 2026-09-29
tags: [testing, agent-monitoring, root-cause]
---

# TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS

## Title
`test_real_corpus_duplicate_classification_matches_measured_baseline` asserts an exact count over a
corpus that keeps growing, so any ticket re-dispatch breaks CI

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tests/tools/test_run_dedup.py::test_real_corpus_duplicate_classification_matches_measured_baseline`
failed CI on PR #254 (`API / tools / logging`, step `Run: tests/tools`):

```
AssertionError: expected 66 duplicate groups (measured 2026-09-15), got 67
```

The count is not wrong and the fix under test is not at fault. `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`
was legitimately dispatched twice — once ending `TESTS_FAILED`, then re-dispatched after an
owner-directed test-scope correction — and those two runs form one **progressive** duplicate group,
making 67.

**The real defect is the assertion's shape, not the pinned number.** The test's own docstring
justifies exact equality by asserting the population is closed:

> "All-time counts on `runs.jsonl`'s own history **before this date** are a closed, non-growing count
> (unlike a live ratchet) -- an exact match is the correct assertion here, not a >= ceiling."

That reasoning is sound, but the code does not implement it. `classify_duplicate_groups(all_runs)`
receives **every** run `_load_runs_and_events()` returns, including runs recorded after 2026-09-15.
So the assertion is an exact match against a **growing** population, and **every future re-dispatch
of any ticket breaks it.** We are the first to trip this, not the last.

## Scope
- Make the test measure what its docstring already claims: restrict the corpus to runs whose
  `start_ts` falls on or before the 2026-09-15 measurement date, which genuinely is closed and
  non-growing, then keep the exact-equality assertions against it.
- Keep all three pinned numbers meaningful for that window (`total_duplicate_groups == 66`,
  `progressive == 63`, `same_status_diff_end == 2`, `identical_outcome == 1`) — re-measure them
  against the scoped window and record the measured values with evidence rather than assuming the
  existing numbers still describe it.
- Update the docstring so the stated reasoning and the implemented behaviour match.

## Out of Scope
- **Blindly bumping the pin to 67.** The test's own failure message says "don't just raise it
  blindly", and doing so would leave the trap armed for the next re-dispatched ticket.
- Changing `classify_duplicate_groups()` itself, or any production monitoring code. This is a test
  scoping defect.
- Deduplicating or editing the actual run records. The two runs are legitimate history and must stay.
- Any change to `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s own fix, which is unrelated and
  correct.

## Acceptance Criteria
1. The test scopes its corpus to runs at or before the 2026-09-15 measurement date, so the asserted
   population is genuinely closed.
2. All pinned counts are **re-measured against the scoped window** and the measured values recorded
   in the ticket, not carried over on assumption.
3. The docstring's stated reasoning matches what the code does.
4. A new run added after the measurement date **does not** change the test's result — demonstrated,
   not asserted. The simplest demonstration: the test passes on this branch, which already contains
   the two post-date runs that currently break it.
5. `tests/tools/` passes in full, matching CI's own invocation for that step.
6. No production monitoring code changed, and no run records edited.

## Related Tickets
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — whose legitimate double dispatch surfaced
  this. Folded into the same PR #254; not a defect in that fix.

## Related Docs
- `docs/agent-monitoring/README.md` — monitoring data scope.
- `docs/testing/regression_policy.md` — baseline-drift handling.
- `CLAUDE.md` "CI Failure Triage" — the drift category this falls under: a hardcoded baseline moved
  by this session's own legitimate change gets a ticket with fresh evidence, never a silent edit.

## Related Stored Artifacts
- None. Hotfix tier; intent is self-evident from the failure message.

## Related Code Areas
- `tests/tools/test_run_dedup.py:109-125` — the failing test, its docstring, and the three pins.
- `tools/agent-monitoring/generate_retro.py::_load_runs_and_events` — returns the unscoped corpus.
- `agent-monitoring/data/*/runs.jsonl` — records carry `start_ts`, which is the field to scope on.

## Assumptions / Open Questions
- Scoping by `start_ts` is assumed sufficient; every run record inspected carries it
  (`run_id`, `execution_id`, `provider`, `ticket_id`, `start_ts`, `end_ts`, `workflow`, `tier`,
  `final_status`, `agent_count`, `duration_s`). **If any historical run lacks `start_ts`, do not
  silently drop it** — report how many and decide explicitly, since dropping records would change
  the very baseline being pinned.
- The exact boundary semantics (inclusive end-of-day 2026-09-15 vs. strictly before) may shift a
  count by one. Pick one, state it in the docstring, and re-measure — do not tune the boundary to
  make a pre-existing number fit.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
