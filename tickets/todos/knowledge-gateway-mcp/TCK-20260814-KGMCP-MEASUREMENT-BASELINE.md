---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260814-KGMCP-MEASUREMENT-BASELINE
phase: open
date: 2026-08-14
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260814-KGMCP-MEASUREMENT-BASELINE

## Title
Record the Knowledge Gateway Phase 0 measurement baseline and predeclare promotion thresholds,
reusing existing retrieval-effectiveness metrics

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 0 requires recording a direct-tool
baseline (latency, tool-call counts, repeated-demand signals, returned-token estimates) for a fixed
representative-query corpus, and predeclaring measurable promotion thresholds, before any gateway
work is evaluated. §18 requires separately measuring lookup, evidence-validation, provider-fallback,
packet-assembly, and end-to-end latency rather than one blended number. §18.1 requires a repeated-
demand estimate using safe deterministic intent/entity IDs, not raw prompt text.

This ticket must **not** build a second, parallel measurement path.
`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (sibling epic child, `agent-tooling-integrity-
hardening`) is already wiring `raw_investigation_count`/`search_count`/`read_to_search_ratio` from
`tools/agent-monitoring/retrieval_baseline_metrics.py` into the recurring `generate_retro.py`
report, including a compliant-vs-non-compliant `Read`-count correlation section. This ticket's
baseline work depends on and extends that infrastructure.

## Scope
- **Investigate (mandatory before Plan):** check the real status of
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (OPEN as of this ticket's creation). If it
  has landed, build directly on its retro sections. If it is still open, coordinate rather than
  duplicate — this ticket's baseline corpus should consume the same
  `retrieval_baseline_metrics.py` functions that ticket wires into the retro, not a second
  `read_to_search_ratio`-equivalent computation.
- Create a fixed representative-query corpus (per §20) spanning the query-routing shapes in §8's
  table (definition/terminology, symbol lookup, requirement-completeness, ticket/historical
  rationale, test-impact, ticket-status, broad-task-context) and the representative use cases in
  §22 (`AuthoritativeState` ownership, feature-completeness check, historical-removal rationale,
  test-impact-of-change, negative-knowledge/Kafka-style query).
- For each corpus query, record the direct-tool baseline: provider outputs, authoritative sources
  recalled, wall time, tool-call count, and serialized tokens returned — using real tool
  invocations against this repository, not estimates.
- Define separate measurement points for lookup latency, evidence-validation latency, provider-
  fallback latency, packet-assembly latency, and end-to-end latency (§18), even though no gateway
  exists yet to measure — this ticket defines the measurement points and instrumentation contract
  that Phase 1+ code must emit into.
- Predeclare minimum latency, token-reduction, and no-regression-recall thresholds derived from the
  recorded baseline (§20's explicit requirement not to invent thresholds before the baseline
  exists).
- Define the repeated-demand estimation approach from §18.1: exact repeated lookup identities,
  entity-and-intent-equivalent requests with different query hashes, repeated misses by entity and
  intent — using safe deterministic intent/entity IDs and the keyed query hash, never raw prompt
  text.

## Out of Scope
- Wiring any of this into a live gateway — no gateway exists yet in Phase 0.
- Modifying `retrieval_baseline_metrics.py`'s existing `SEARCH_TOOL_NAMES` design or Bash-exclusion
  rationale — reused as-is, per `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s own
  out-of-scope note.
- Semantic clustering of repeated demand — §18.1 explicitly defers privacy-reviewed semantic
  clustering to Phase 5.
- Backfilling correlation numbers for historical weeks — first data point is real, forward-looking
  data only.

## Acceptance Criteria
- [ ] `investigation.md` confirms the real status of `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-
      TRACKING` and states explicitly how this ticket's baseline work reuses (not duplicates) its
      metric functions.
- [ ] A fixed, versioned representative-query corpus exists, covering all routing shapes from §8
      and all 5 use cases from §22.
- [ ] Each corpus query has a recorded direct-tool baseline (provider outputs, sources recalled,
      wall time, tool-call count, serialized tokens) from a real run, not an estimate.
- [ ] Lookup, evidence-validation, provider-fallback, packet-assembly, and end-to-end latency are
      defined as distinct measurement points with a documented instrumentation contract.
- [ ] Minimum latency, token-reduction, and no-regression-recall thresholds are predeclared and
      derived from the recorded baseline numbers (not invented independently of them).
- [ ] The repeated-demand estimation design uses only deterministic intent/entity IDs and query
      hashes — no raw prompt text is persisted.
- [ ] Tests mirror `tests/tools/test_retrieval_baseline_metrics.py`'s never-silent,
      derivation-string convention.

## Related Tickets
- TCK-20260814-KNOWLEDGE-GATEWAY-MCP-EPIC (parent)
- TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING (OPEN; owns the metric infrastructure this
  ticket must reuse — check status before Plan)
- TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC (DONE; original `raw_investigation_count`/
  `read_to_search_ratio` metric)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (BACKLOG; broader retrieval epic this baseline also
  informs)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §18, §18.1, §20, §22
- `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_retrieval_baseline_metrics.py`

## Assumptions / Open Questions
- Whether the representative-query corpus lives as a fixture file consumed by both this ticket and
  `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s correlation section, or is scoped
  independently — Investigate should check that sibling ticket's actual implementation (once it
  lands) before deciding, to avoid a second corpus definition.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
