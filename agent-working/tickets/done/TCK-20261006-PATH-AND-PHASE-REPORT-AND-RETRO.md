---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-PATH-AND-PHASE-REPORT-AND-RETRO
phase: done
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-PATH-AND-PHASE-REPORT-AND-RETRO

## Title
A report-only path and phase-coverage reading per tier, and a Paths section in the weekly retro

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261006-EPIC-TICKET-PATH-RECORD`. Turn the path and phase fields into the weekly reading that the
direction doc's routing row is waiting for. Show how much of the reading rests on `unstated`, so nobody routes on
logging habits.

## Scope
- **A new `tools/agent-monitoring/path_report.py [--week YYYY-Www]`.** For implement-ticket runs, per tier and
  `execution_mode`:
  - run count and the `path_reason` mix, including `unstated`;
  - per phase, the counts ran / skipped / omitted / conditional-absent, with the `skip_reason` mix;
  - a line naming the phases that tier-based routing could act on: skipped or omitted in at least 80% of runs, with
    at least 10 runs and an `unstated` share of 25% or less. If no phase passes, it says so.
- **Runs that predate the new fields** are counted under "predates field" and never as `unstated`. This follows
  the session_role split made in the W41 follow-ups.
- **A "Paths" section in `generate_retro.py`**, with the same dark/zero wording rule as the Gates section.
- **Direction doc.** The path-record row moves to `shipped (code)`. The routing row's note becomes "depends on the
  Paths retro reading (≥1 full week)".

## Out of Scope
- Acting on the reading: no routing and no tier changes.

## Acceptance Criteria
1. A fixture week with 12 standard hand runs has Plan omitted in 11 and `path_reason` stated in 10 of the 12.
   The report flags Plan as a routing candidate.
2. The same fixture with only 4 reasons stated does not flag Plan, and names the `unstated` share as the reason.
3. Runs from before the fields existed land in "predates field". A real W41 run against the data shows only
   predates-field rows and no candidate.
4. The retro renders the Paths section from the fixture. With no runs it uses the dark/zero wording. Regenerating
   keeps hand-written Notes without `--force`.
5. The direction doc is updated. The scoped `path_report` and retro tests are green.

## Related Tickets
- `TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD` (depends on it)
- `TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO` (the retro section pattern to copy)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md`

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py`, `retro_provenance.py`, new `path_report.py`

## Assumptions / Open Questions
- The three thresholds (80% skipped or omitted, at least 10 runs, `unstated` at 25% or less) are starting values,
  to be changed at a retro.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

## Test Summary
`tests/tools/test_path_report.py` (10 pass) covers AC1 (Plan flagged with 10 of 12 reasons stated), AC2 (not flagged with 4 stated; the held-back line names the `unstated` 67%), AC3 (old runs are `predates`; an all-old period shows only predates rows and no candidate), AC4 (the section renders before Notes; Notes survive a regeneration without `--force`; no section when not passed). A real run, `path_report.py --week 2026-W41`, shows 84 implement-ticket runs, all predating the fields, and no candidate. `test_generate_retro.py` and `test_gate_ledger.py` stay green (221 pass together).

## Files Changed
- `tools/agent-monitoring/path_report.py` (new), `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_path_report.py` (new)
- `docs/plans/agent_infrastructure/agent_working_direction.md`

## Completion Summary
Closed 2026-10-06. All five acceptance criteria met on fixtures and on the real W41 data (every run predates the fields, so the section shows the dark wording plus a predates table, no candidate). Thresholds are the ticket's starting values. Not done: acting on the reading (no routing, out of scope); the real reading needs the first full week after the merge.
