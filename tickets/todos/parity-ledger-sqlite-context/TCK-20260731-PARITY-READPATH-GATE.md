---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-READPATH-GATE
phase: open
date: 2026-07-31
tags: [ai, agent-monitoring, observability, process-improvement, testing, workflows]
---

# TCK-20260731-PARITY-READPATH-GATE

## Title
Run the parity-index read-path payoff gate before adoption work

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Run Gate A as an offline, reproducible review of whether the completed read-only index materially
improves parity selection. This ticket is a decision gate, not permission to integrate the index
into agent context or a workflow.

## Scope
- Predeclare and version a review rubric and corpus: legacy edge fixtures plus immutable,
  ticket-derived cases; include a faction source-path case. Preserve source references/hashes and
  distinguish asserted ground truth from evaluator judgement.
- For each case, capture legacy selection, index selection, expected obligation IDs/shards,
  discrepancy adjudication, candidate count/context-byte or token estimate, and consistently
  measured analyst effort.
- Reproduce results and issue an explicit GO, NO-GO, or INCONCLUSIVE decision with rationale and
  a next action. GO only authorizes later ticket scoping, not implementation.

## Out of Scope
- Any context-packet/retrieval-cache/workflow/gate/config/monitoring mutation or live token-savings claim.
- Implementing Phase 3+ or changing the index/legacy tools to improve the score during the review.

## Acceptance Criteria
- [ ] Corpus and rubric are reviewable before results are generated; every case has reproducible
      source references/hashes and expected-set/adjudication fields.
- [ ] Legacy and index results are captured for all cases; every mismatch is adjudicated rather
      than silently averaged away.
- [ ] The decision reports recall, false positives, selection size/context estimate, and analyst
      effort. It records zero unexplained obligation false negatives against the adjudicated set.
- [ ] A GO additionally demonstrates faction/all-shard coverage, fewer false positives, or smaller
      selection size without recall regression. NO-GO/INCONCLUSIVE leaves legacy behavior live and
      files/backlogs only a bounded follow-up if warranted.
- [ ] No production consumer, telemetry event, guidance/config/workflow change, or source YAML write occurs.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC
- TCK-20260731-PARITY-IMPACT-PROOF (dependency)
- TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS (decision-gate precedent, distinct scope)

## Related Docs
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md
- docs/engine/contracts/context_packet_contract.md (boundary only)
- docs/observability/retrieval_retention_redaction_policy.md (artifact boundary only)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/context_packet_assembler.py (protected boundary; no edit expected)
- tools/agent-monitoring/generate_retro.py (evaluation precedent only)
- tests/tools/test_context_packet_assembler.py (protected regression boundary)
- tests/tools/test_generate_retro.py (evaluation precedent only)

## Assumptions / Open Questions
- The Gate A decision is human-reviewable evidence, not an automatic promotion threshold.

## Implementation Notes
If evidence is insufficient, close as INCONCLUSIVE and keep later adoption out of scope.

## Test Summary

## Files Changed

## Completion Summary

