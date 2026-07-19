---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-PHASE-AGENT-CASE-FOLD
phase: open
date: 2026-07-19
tags: []
---

# TCK-20260719-PHASE-AGENT-CASE-FOLD

## Title
Normalize phase/agent vocabulary casing in retro metrics

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Casing variants of phase/agent labels (e.g. Verify/verify/VERIFY, Implement/implement/IMPLEMENT, and 6 more phases) should be folded into one canonical bucket at read time, extending the existing normalization point in generate_retro.py. This closes a data-quality gap where fragmented vocabulary silently undercounts real failure rates when read naively — Review's true failure rate is 18.2%, the highest of any phase, but only visible after merging casing variants. A regression test proves the previously-undercounted rate is now computed correctly from raw fragmented input.

## Scope
- Extend generate_retro.py's compute_retro_metrics() aggregations (agent_status_distribution, spend_proxy_by_phase, spend_proxy_by_agent, gate counters) to normalize phase/agent casing variants
- Use vocabulary.py's canonical WORKFLOW_PHASES/WORKFLOW_AGENTS lists as the sole merge target (no second hardcoded list)
- Add regression test proving Review's real merged failure rate resolves to 18.2% from fragmented fixture input

## Out of Scope
- Modifying validate.py's compute_drift_report or its drift-visibility output — must remain unchanged, decoupled from retro merging; test_drift_report_frequency_table_non_canonical_phase_and_agent must keep passing unmodified
- Creating a second hardcoded phase/agent vocabulary list
- Implementing TCK-20260713-MONITORING-SQLITE-INDEX's derived-index migration (sibling ticket, confirmed not yet implemented; normalization proceeds directly in generate_retro.py instead of waiting)

## Acceptance Criteria
- [ ] All 8 affected phases' casing variants merged in compute_retro_metrics()'s aggregations (agent_status_distribution, spend_proxy_by_phase, spend_proxy_by_agent, gate counters) using vocabulary.py's canonical WORKFLOW_PHASES/WORKFLOW_AGENTS as merge target
- [ ] New regression test in tests/tools/test_generate_retro.py proving Review's real merged failure rate resolves to 18.2% from fragmented fixture input (Review/review/REVIEW mixed)
- [ ] validate.py's compute_drift_report drift-visibility output remains unchanged/unmodified (test_drift_report_frequency_table_non_canonical_phase_and_agent passes unmodified)
- [ ] test_canonical_vocabulary_single_sourced continues to pass (no second hardcoded vocabulary list introduced)

## Related Tickets
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260713-MONITORING-SQLITE-INDEX
- TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/vocabulary.py
- tools/agent-monitoring/validate.py
- tests/tools/test_generate_retro.py

## Assumptions / Open Questions
- Sequencing dependency on TCK-20260713-MONITORING-SQLITE-INDEX is resolved (confirmed status:active/phase:open, not yet implemented) — safe to proceed directly in generate_retro.py rather than wait for the derived-index migration

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
