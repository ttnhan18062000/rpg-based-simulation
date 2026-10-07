---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261007-RETRO-FAILURES-SECTION
phase: open
date: 2026-10-07
tags: [agent-monitoring]
---

# TCK-20261007-RETRO-FAILURES-SECTION

## Title
Retro Failures section: non-DONE runs, failed/blocked events, recurring failures

## Status
OPEN

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
- [ ] A week containing a run with final_status BLOCKED renders a Failures section listing that run_id and status
- [ ] Every failed/blocked event appears with its one-line summary, grouped by agent then reason_code, with a per-group count
- [ ] A test failing in 2 or more distinct tickets is listed once with count N and the ticket IDs; a single occurrence is not flagged recurring
- [ ] A week with no non-DONE runs or failed/blocked events renders an explicit zero line or is omitted, consistent with sibling sections
- [ ] An exception while building the section returns None and the retro still writes
- [ ] Retro generation leaves shard files unchanged (test)
- [ ] Tests added alongside tests/tools/test_generate_retro.py pattern

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

## Test Summary

## Files Changed

## Completion Summary
