---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-COST-PROXY-WRITE-PATH
phase: open
date: 2026-07-19
tags: []
---

# TCK-20260719-COST-PROXY-WRITE-PATH

## Title
Move TOOL_STATS compute out of writeMonitoring's LLM step into record_events.py

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Investigation (not just an audit) found duration_s coverage is already resolved: scoped to start_ts > 2026-07-09T08:39:45Z (TCK-20260709-AGENT-MONITORING-DURATION's real landing), coverage is 114/115 = 99.13%, with the single miss being an expected IN_PROGRESS run with no end_ts yet — close as non-issue, no code change. However, cost_proxy_score/tool_call_count remain a real, confirmed, ongoing gap: scoped to ts > 2026-07-11T14:32:38Z (TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION's landing) for workflow=implement-ticket, 36.7% of 562 events are still null for cost_proxy_score and 29.5% null for tool_call_count, spanning 37 distinct tickets from 2026-07-11 through today, with 30 of 37 affected runs showing all-or-nothing nulls (consistent with a per-run compute step failing wholesale, not per-event flakiness). Root cause confirmed by direct code read: writeMonitoring (.claude/workflows/implement-ticket.js:258-320) is an LLM-executed agent() call that computes TOOL_STATS via an inline python3 -c command and substitutes values into each event before calling record_events.py --data; record_events.py itself is a dumb writer with no compute logic. This is the exact LLM-bookkeeping-determinism anti-pattern already fixed for duration_s (moved into record_run.py) and sidecar registration (moved to orchestrator bash()), but never extended to cost_proxy_score/tool_call_count. Fix moves the compute into deterministic code in record_events.py, mirroring record_run.py's compute_duration_s precedent.

## Scope
- Move TOOL_STATS computation (cost_proxy_score, tool_call_count) out of writeMonitoring's LLM-executed agent() prompt in .claude/workflows/implement-ticket.js
- Implement deterministic computation of both fields in tools/agent-monitoring/record_events.py at write time from tools.jsonl, mirroring record_run.py's compute_duration_s precedent
- Preserve fail-silent/non-blocking monitoring-write behavior per CLAUDE.md hard rule (monitoring write failure must never fail the workflow)
- Add test asserting record_events.py populates both fields correctly without relying on caller-supplied/LLM-transcribed values

## Out of Scope
- implement-epic/create-tickets — 100% missing for both fields by documented, deliberate design (no sidecar registered); this is not a bug and stays out of scope
- Historical backfill of already-written null records in agent-monitoring/events.jsonl (fix is forward-looking only, no-backfill precedent)
- duration_s — already resolved at 99.13% coverage, no action needed beyond documenting it as closed

## Acceptance Criteria
- [ ] Ticket body records duration_s as already resolved: 114/115 = 99.13% coverage scoped to start_ts > 2026-07-09T08:39:45Z, single miss is an expected in-progress run; no code change made for duration_s
- [ ] Ticket body records the confirmed real gap: 36.7% null cost_proxy_score, 29.5% null tool_call_count across 562 implement-ticket events scoped to ts > 2026-07-11T14:32:38Z, spanning 37 tickets, with an all-or-nothing per-run null pattern
- [ ] TOOL_STATS compute/substitution logic removed from writeMonitoring's agent()-executed prompt in .claude/workflows/implement-ticket.js
- [ ] record_events.py computes cost_proxy_score and tool_call_count deterministically from tools.jsonl at write time instead of relying on caller-supplied values
- [ ] New test in tests/tools/test_record_events.py asserts deterministic computation (not passthrough) of both fields
- [ ] Regression test confirms implement-epic/create-tickets events remain unaffected (fields stay absent/null as documented, no sidecar)
- [ ] Monitoring write failure still never fails the workflow (fail-silent behavior preserved end to end)

## Related Tickets
- TCK-20260708-AGENT-COST-OBSERVABILITY
- TCK-20260709-AGENT-MONITORING-DURATION
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH

## Related Docs
- docs/agent-monitoring/schema.md
- docs/plans/archive/agent_infrastructure/idea_agent_bookkeeping_determinism.md
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/cost_proxy.py
- tests/tools/test_record_events.py
- tests/tools/test_record_run.py

## Assumptions / Open Questions
- Fix only benefits future runs — the historical 2026-07-11-to-today null gap in already-written records is permanent and will not be backfilled
- Sample size is modest (562 events / 37 runs) but the all-or-nothing per-run pattern was directly observed via code read, not statistically inferred, so root cause confidence is high despite sample size

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
