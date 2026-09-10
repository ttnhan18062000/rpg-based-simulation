---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL
phase: open
date: 2026-09-10
tags: [agent-monitoring, mcp]
---

# TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL

## Title
Remove the orphaned KGMCP measurement runners and their unconsumed fixtures

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Three measurement tools under `tools/agent-monitoring/` survived the Knowledge Gateway MCP
deprecation because they do not import anything that was deleted — they still run. But what they
measure is a gateway-vs-direct-tool baseline whose gateway counterpart no longer exists, so they
now produce a comparison with nothing to compare against.

Verified against `origin/main` on 2026-09-10 (re-verify at Investigate):

- `tools/agent-monitoring/kgmcp_baseline_corpus.py` — the shared 7-entry corpus definition.
- `tools/agent-monitoring/kgmcp_baseline_runner.py` — imports `kgmcp_baseline_corpus` (:49) and
  `search_mcp._run_search` (:54), both live.
- `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` — imports
  `registry_query` (:69), live.

None has a Makefile target, a `.claude/` invocation, or a test that imports it. Notably
`tests/docs/test_phase5_repeated_demand_measurement_doc.py` does **not** import the phase5 runner
— it reads a fixture directly (:32), so the runners have no test consumer at all.

Nine `tests/tools/fixtures/kgmcp_*.json` fixtures relate to this family. Four are already
orphaned outright; three more are consumed *only* by the runners above and therefore fall with
them; two are independently consumed by live `tests/docs/` tests and must stay.

## Scope
- Remove the three runner/corpus modules listed above.
- Remove the four already-orphaned fixtures: `kgmcp_phase1_baseline_comparison_results.json`,
  `kgmcp_phase2_baseline_recomparison_results.json`,
  `kgmcp_phase3_pilot_acceptance_measurement_results.json`,
  `kgmcp_phase4_warm_direct_tool_comparison_results.json`.
  Note `kgmcp_phase2_baseline_recomparison_results.json` only *looks* referenced —
  `tools/write_path_guard.py:61` mentions it inside a `#` comment, not code.
- Remove the three fixtures consumed only by the removed runners:
  `kgmcp_measurement_baseline_corpus_results.json`,
  `kgmcp_phase5_events_investigate_snapshot.json`,
  `kgmcp_phase5_working_log_snapshot.json`.
- Re-verify each fixture's consumer set immediately before deleting it, rather than trusting the
  classification above — the split between "orphaned," "falls with the runners," and "keep" is
  the whole risk in this ticket.

## Out of Scope
- **These two fixtures must be RETAINED** — they have live `tests/docs/` consumers independent of
  the runners: `kgmcp_phase4_direct_tool_comparison_results.json` and
  `kgmcp_phase5_repeated_demand_measurement_results.json`.
- `tests/tools/test_knowledge_gateway_archival.py` — retained. It was correctly updated by
  `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` to assert the gateway modules are *hard-deleted*
  rather than archived, so it is a live regression guard, not residue.
- `docs/engine/contracts/knowledge_gateway_mcp/` — retained as institutional record.
- The `retrieval_cache.py`/retro/dashboard access-log chain — separately scoped as
  `TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL`.

## Acceptance Criteria
- [ ] The three runner/corpus modules are removed, with no remaining import or invocation
      anywhere (`tools/`, `tests/`, `.claude/`, `Makefile`).
- [ ] Exactly seven fixtures are removed and the two named in Out of Scope are still present.
- [ ] `tests/docs/test_phase5_repeated_demand_measurement_doc.py` and the other `tests/docs/`
      fixture consumers still pass.
- [ ] Full `tests/tools/` and `tests/docs/` lanes pass.

## Related Tickets
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` (done) — the deprecation that orphaned these.
- `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS` (done) — archived the five gateway-dependent
  runners; these three survived because they are not gateway-dependent, only gateway-purposed.

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` (now
  `status: historical`) — describes the corpus this ticket removes the code for; leave the doc,
  it is the historical record.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_baseline_runner.py`,
  `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py`
- `tests/tools/fixtures/kgmcp_*.json`

## Assumptions / Open Questions
- These tools are functional, not broken — this is a "purposeless, therefore remove" call rather
  than a defect fix. If Investigate finds a genuine remaining use (e.g. the corpus being reusable
  for a non-gateway retrieval benchmark), say so and narrow the ticket rather than removing on
  the strength of this framing alone.

## Implementation Notes
(filled in during implementation)

## Test Summary
(filled in during implementation)

## Files Changed
(filled in during implementation)

## Completion Summary
(filled in at close)
