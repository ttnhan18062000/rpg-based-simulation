---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261007-RETRO-FAILURES-SECTION
phase: done
date: 2026-10-07
tags: [agent-monitoring]
---

# TCK-20261007-RETRO-FAILURES-SECTION

## Title
Retro Failures section: non-DONE runs, failed/blocked events, recurring failures

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add a section to the retro listing every non-DONE run and every failed/blocked event with its one-line summary, grouped by agent and by recurring cause, plus a count of the same test failing across tickets so recurring pre-existing failures are visible. W40 needed two throwaway scripts to get this. The known-failing-test baseline is an owner decision and out of scope.

## Scope
- New sibling module (like gate_ledger/path_report) rendering the Failures section, wired into generate_retro main() via a try/except returning None
- List non-DONE runs using the existing _is_gate_fail definition on deduped latest-per-execution runs
- List every failed/blocked event with its summary, grouped by agent (_normalize_agent) then reason_code (unspecified bucket for older events)
- Count same-named tests failing across N>=2 distinct tickets, with ticket IDs, parsed from event summaries
- Read-only: no shard mutation or folding

## Out of Scope
- Defining or enforcing a known-failing-test baseline (owner decision)
- Classifying or suppressing known-failing tests
- Adding a structured per-test failure field to the event schema
- Duplicating the Gates section (unresolved gate verdicts)

## Acceptance Criteria
- [x] A week containing a run with final_status BLOCKED renders a Failures section listing that run_id and status
- [x] Every failed/blocked event appears with its one-line summary, grouped by agent then reason_code, with a per-group count
- [x] A test failing in 2 or more distinct tickets is listed once with count N and the ticket IDs; a single occurrence is not flagged recurring
- [x] A week with no non-DONE runs or failed/blocked events renders an explicit zero line or is omitted, consistent with sibling sections
- [x] An exception while building the section returns None and the retro still writes
- [x] Retro generation leaves shard files unchanged (test)
- [x] Tests added alongside tests/tools/test_generate_retro.py pattern

## Related Tickets
- TCK-20260706-MONITORING-REASON-CODE
- TCK-20260705-RETRO-METRIC-ACCURACY
- TCK-20260708-RETRO-TAG-BREAKDOWN
- TCK-20260718-RETRO-STATS-REFACTOR
- TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER
- TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED

## Related Docs
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/gate_ledger.py
- tools/agent-monitoring/path_report.py
- tools/agent-monitoring/query.py
- tools/agent-monitoring/run_dedup.py
- tests/tools/test_generate_retro.py
- tests/tools/test_path_report.py
- tests/tools/test_retro_provenance.py

## Assumptions / Open Questions
- No structured per-test failure field exists; test names are parsed from event summaries and a regex may be lossy
- reason_code is only populated on newer events, older ones fall in an unspecified bucket
- Follow the gate_ledger sys.path import convention to avoid bloating the 2348-line generate_retro.py
- Layer chosen as observability (agent monitoring/retro tooling).

## Implementation Notes
New sibling `tools/agent-monitoring/retro_failures.py` (`render_section(runs, events, is_failed_run, agent_of, resolve_status)`), wired from `generate_retro.py` through `_failures_section` (try/except returning None, like `_gates_section`) and a `failures=` keyword on `generate()`. It renders non-DONE runs (the existing `_is_gate_fail` on deduped latest-per-execution runs), every failed/blocked event grouped by `_normalize_agent` then `reason_code` (`unspecified` for older events) with counts and a one-line capped summary, and the tests named in two or more distinct tickets (node ids first, bare `test_*` only when the summary has no node id; names are parsed from summaries and the heading says so). The section sits right after "Gate Failure Breakdown" (planner's placement ruling); with no failures it renders an explicit zero line. Read-only. The predicates are passed in so the module never imports `generate_retro` (cycle).

## Test Summary
`pytest tests/tools/test_retro_failures.py test_generate_retro.py test_path_report.py test_gate_ledger.py`: 236 passed (10 new in test_retro_failures.py: BLOCKED run listed, grouping with counts, recurring test across tickets, same ticket twice not recurring, bare vs node id, zero line, one-line cap, exception returns None and the retro still writes, section order, shards unchanged). The existing golden report test is unchanged (no section passed means no change).

## Files Changed
tools/agent-monitoring/retro_failures.py, tools/agent-monitoring/generate_retro.py, tests/tools/test_retro_failures.py

## Completion Summary
Failures section implemented and wired; all acceptance criteria met. Known gap (stated in the section itself): test names come from free-text summaries, so a test can be missed or two same-named tests merged; the known-failing-test baseline stays an owner decision.
