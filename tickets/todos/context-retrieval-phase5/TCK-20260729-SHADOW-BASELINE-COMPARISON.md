---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260729-SHADOW-BASELINE-COMPARISON
phase: open
date: 2026-07-29
tags: [retro, agent-monitoring, observability]
---

# TCK-20260729-SHADOW-BASELINE-COMPARISON

## Title
Add shadow-vs-baseline retrieval comparison view to generate_retro.py

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Extend generate_retro.py with a query/report that compares shadow-packet-covered phase outcomes against existing baseline metrics, mirroring Phase 4's compute_retrieval_metrics() precedent. This produces comparison data only, never a promotion scorecard, and is fixture-tested.

## Scope
- Add a new function in generate_retro.py that partitions retrieval-shaped events by real (TCK-...) vs. synthetic (RETRIEVAL-EVENT-<slug>) run_id provenance
- Compute comparison rows for the shadow cohort using the same measurement domain as compute_retrieval_metrics() (cache rates, noise ratios, freshness-authority, expansion rate) — resolved as the correct baseline per this ticket's Resolved Decision, not tools/agent-monitoring/retrieval_baseline_metrics.py's separate duration/outcome/token-stat JSON report, because compute_retrieval_metrics() measures the same retrieval-quality domain for both cohorts and lives in the same file, following the established byte-identical-output-preserving extension pattern
- Follow generate()'s existing conditional-render pattern: the new comparison section is omitted entirely (not rendered empty) when zero shadow events are present
- Add fixture-only tests (synthetic runs.jsonl/events.jsonl) exercising both the zero-shadow-events (section omitted) and nonzero-shadow-events (comparison rows rendered) cases

## Out of Scope
- No scorecard or comparison against the six approval-gate criteria — verified by asserting none of those criteria phrases appear in generated report text
- No changes to retrieval_baseline_metrics.py's own standalone JSON report format
- No changes to existing non-shadow report output — must remain byte-identical (TCK-20260718-RETRO-STATS-REFACTOR precedent)
- No live dashboard/UI surfacing — report text output only
- No independent event-emission or call-site logic — this ticket only reads events already emitted by the merged shadow-packet call-site ticket

## Acceptance Criteria
- [ ] A new function in generate_retro.py partitions retrieval-shaped events by real-vs-synthetic run_id provenance and computes comparison rows using compute_retrieval_metrics()'s measurement domain (cache rates, noise ratios, freshness-authority, expansion rate)
- [ ] When zero shadow (real-run-id) events are present, the new report section is omitted entirely, per generate()'s existing conditional-render pattern
- [ ] Existing non-shadow report output remains byte-identical to current output on the same fixture inputs
- [ ] No phrase from any of the six approval-gate criteria appears in the new comparison section's generated text (asserted by test)
- [ ] New tests are fixture-only (synthetic runs.jsonl/events.jsonl), with no live-data dependency

## Related Tickets
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260729-SHADOW-PACKET-CALL-SITE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/retrieval_baseline_metrics.py
- tools/retrieval_events.py
- tests/tools/test_generate_retro.py

## Assumptions / Open Questions
- Hard dependency: this ticket cannot land or be exercised against real data until the merged shadow-packet-call-site ticket (TCK-20260729-SHADOW-PACKET-CALL-SITE) lands and begins emitting real-run-id-provenance retrieval events; fixture tests here are built against the event shape that ticket defines

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
