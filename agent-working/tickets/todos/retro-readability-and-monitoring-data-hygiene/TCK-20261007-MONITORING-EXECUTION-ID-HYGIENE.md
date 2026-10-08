---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE
phase: open
date: 2026-10-07
tags: [agent-monitoring, data-quality]
---

# TCK-20261007-MONITORING-EXECUTION-ID-HYGIENE

## Title
Monitoring data hygiene: execution_id gaps and validator warning report

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
About 900 of 2116 run rows lack execution_id (mostly W23-W34, but also W40: 5, W41: 3). Find which writer still omits it in W40/W41, then decide to tolerate as predates/by design or fix the writer, since the retro dedupe key (run_id, execution_id, start_ts) is weakened. Also address non-canonical tiers (epic_batch, epic-batch), null-tier rows, tools.jsonl rows skipped by the loader, and tickets with 2-4 Scope events at seq 1 (resume collision). Report the make agent-monitoring-validate warning count for W40+ rows before and after. No backfilling or rewriting of past shards and no blocking gate.

## Scope
- Record baseline: make agent-monitoring-validate output (currently 139 warnings, not the proposed 318) and the W40+ warning count with counting method
- Document the decision for the 5 W40 rows (create-tickets/implement-epic omit execution_id by design): tolerate with a note, or add execution_id to those writers' record_run payload
- Run the drift report to locate non-canonical tier, null-tier, loader-skipped tools.jsonl and Scope/seq=1 collision rows and surface them as report-only output
- If writers are fixed, add a test that their payloads include execution_id and run_dedup group key uses the (run_id, execution_id, start_ts) form
- Report W40+ warning count after the change

## Out of Scope
- Backfilling or rewriting any past shard
- Adding a blocking gate or non-zero exit on warnings
- Fixing the historical 'DONE has no working_log entry' warning class
- Changing the resume seq source in writers unless required by the chosen decision

## Acceptance Criteria
- [ ] Report states W40+ validator warning count before and after with the filter method; baseline notes 139 total warnings
- [ ] Decision on the W40 create-tickets/implement-epic missing execution_id is documented as tolerate-by-design or fixed
- [ ] If fixed, a test asserts create-tickets/implement-epic record_run payloads carry a non-empty execution_id and run_dedup groups them by (run_id, execution_id, start_ts)
- [ ] Validator reports non-canonical tiers, null-tier rows, loader-skipped tools.jsonl rows and Scope/seq=1 collision tickets as report-only output
- [ ] make agent-monitoring-validate exits 0 with only warnings
- [ ] git diff on agent-working/agent-monitoring/data shows no rewrites of past shards

## Related Tickets
- TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY
- TCK-20260904-COST-PROXY-EPIC-TICKETS
- TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX

## Related Docs
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/run_dedup.py
- tools/agent-monitoring/vocabulary.py
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/build_index.py
- tools/agent-monitoring/writer.py
- .claude/workflows/create-tickets.js
- .claude/workflows/implement-epic.js
- .claude/workflows/implement-ticket.js
- Makefile
- tests/tools/test_validate_agent_monitoring.py
- tests/tools/test_monitoring_anomaly_validator.py

## Assumptions / Open Questions
- Proposal numbers are stale; validate currently prints 139 warnings and 8 W40/W41 runs lack execution_id (5 W40, 3 W41 including 2 NATIVE-RUN-FAILING-GATE-PROBE rows)
- Native workflow runtime has no clock/shell, so wiring execution_id into create-tickets.js/implement-epic.js may need a different identity source and could justify tolerating instead
- Null-tier and epic_batch/epic-batch rows were not located in validate output and need a drift report run to confirm
- Monitoring write failure must never fail the workflow

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
