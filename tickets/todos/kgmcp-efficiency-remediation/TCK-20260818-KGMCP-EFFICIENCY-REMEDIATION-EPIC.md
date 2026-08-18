---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC
phase: open
date: 2026-08-18
tags: [ai, mcp, testing]
---

# TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC

## Title
KGMCP efficiency remediation: fix the root cache-write blocker, re-measure honestly, close the accounting and pipeline gaps it exposed

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P1

## Request Summary
User asked, after watching two real CI hotfixes land against KGMCP-touching code today, "do you
think we need to improve KGMCP or something?" The honest answer is already on record across the
epic's own Phase 1-5 tickets, never softened or hidden, and it says the gateway is currently not
earning its cost:

- **Phase 2** (`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`): **0/7** corpus entries got a
  genuine cache hit. Every real response payload exceeds the deployed cache's 8192-byte write-size
  cap, so `perform_cache_write()` rejects every write (`"oversized_payload"`). Nothing has ever
  been cached in a real measured run. **Correction (2026-08-18, see
  `TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX`'s Completion Summary): this was already fixed
  same-day by `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`, before this epic was
  scoped — the cap is now 65536 bytes and a real re-run confirmed 7/7 genuine cache hits. That
  same hotfix also honestly re-measured §4.1/§4.2 on the now-warm path and found both still
  FAIL 0/7 — the epic's underlying concern survives the correction, just on updated evidence.**
- **Phase 3** (`TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE`): a real, measured fix
  shrank payloads 11%-22%, but the §21 #12 budget-tolerance pass rate stayed stuck at **2/7** —
  the accounting still doesn't count JSON structural overhead or untouched response fields that
  the real `json.dumps(response)` measurement counts.
- **Phase 4** (`TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`): a live, fresh, paired comparison
  against calling Context Search / Graphify / the Parity Ledger adapter directly found the
  gateway **slower** (1.31x-3.76x) and **heavier in tokens** (1.04x-2.93x) on all **7 of 7**
  entries, with direct tools judged equal-or-better on 6/7 and the gateway equal-or-better on
  **none**.
- **Phase 5** (`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`): the repeated-question demand
  that would justify a caching layer at all is weak in this repo's real history (5.8%-18.5% of
  tickets show any repeat signal, mostly natural incremental investigation, not literal repeats).
  The phase's own recorded recommendation: proceed with the rest of Phase 5 "only after Phase 3's
  own disclosed gaps close — not now, not never."
- **Today** (`TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD`): the
  latest KGMCP-touching ticket shipped with two existing regression tests broken
  (`tests/tools/test_knowledge_gateway_cache.py`,
  `tests/tools/test_knowledge_gateway_redaction.py`) that its own Verify/Finalize phase should
  have caught before Finalize but didn't — required two separate follow-up hotfixes
  (`TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-GUARD-TESTS`,
  `TCK-20260818-HOTFIX-WEBSOCKET-OBSERVABILITY-MOVEMENT-EVENT-RACE`) to get real CI green again.

This epic scopes and tracks the child tickets needed to fix the root blocker, re-measure honestly
with it fixed, close the remaining accounting gap, and close the process gap that let a
KGMCP-touching ticket ship with pre-existing tests broken. It does not implement any fix directly.

## Scope
- Scope-only epic: track and sequence the child tickets in
  `tickets/todos/kgmcp-efficiency-remediation/`; no direct implementation in the parent.
- ~~Fixing the cache write-size cap~~ — **already done** before this epic was scoped, by
  `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`. The child ticket that duplicated this
  (`TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX`) is closed as a no-op with the correction
  disclosed in its own Completion Summary.
- Running Phase 4's gateway-vs-direct-tool comparison methodology on a genuinely *warm* gateway
  (never done — Phase 4 itself was explicitly cold-cache-only) to produce a real go/no-go verdict
  on keeping KGMCP over direct tool calls, now that caching itself is confirmed working.
- Closing Phase 3's disclosed JSON-structural-overhead accounting gap in
  `assemble_within_budget()` so the §21 #12 budget-tolerance measurement reflects the real
  `json.dumps(response)` payload size, not an undercount.
- Closing the process gap that let today's KGMCP ticket ship with two pre-existing tests broken:
  Verify-phase test scoping for tickets touching shared/widely-depended-on modules (like
  `tools/retrieval_cache.py`) needs to run the full affected test directory, not just the
  ticket's own new tests, before Finalize.

## Out of Scope
- Building any of Phase 5's remaining planned capabilities — explicitly blocked by Phase 5's own
  recorded recommendation until this epic's re-measurement produces a real go/no-go.
- Any change to the routing-caused Q2/Q5 recall miss — confirmed architectural (single-provider
  routing), out of scope for every prior KGMCP phase and this epic too.
- Deciding right now whether to deprecate KGMCP entirely — that decision is the deliverable of
  the re-measurement child ticket, not a premise of this epic. This epic fixes the known root
  blocker and measures honestly; it does not pre-judge the outcome.

## Acceptance Criteria
- [x] The cache write-size cap fix child ticket lands — closed as a no-op 2026-08-18: verified
      already fixed by a pre-existing hotfix, cache hits confirmed 7/7 by that hotfix's own
      independent verification (not assumed from code inspection alone).
- [ ] The re-comparison child ticket produces a real, honestly reported go/no-go verdict on
      KGMCP vs. direct tool calls on the warm path — whatever the result, stated plainly.
- [ ] The budget-tolerance accounting gap child ticket either closes the gap (higher §21 #12 pass
      rate, honestly measured) or reports plainly why it still can't, per this project's Gate
      Integrity discipline (no threshold redefined to force a pass).
- [ ] The Verify-phase test-scoping child ticket lands and is verified against a real
      reproduction of today's exact failure mode (a ticket touching `tools/retrieval_cache.py`
      breaking an existing test outside its own new-test set) — the fix must catch that class of
      regression before Finalize, not just document the gap.
- [ ] Epic is not closed merely because child tickets exist — each must reach `tickets/done/`
      with its own evidence before this epic closes.

## Related Tickets
- TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON
- TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE
- TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON
- TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
- TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-GUARD-TESTS
- TCK-20260818-HOTFIX-WEBSOCKET-OBSERVABILITY-MOVEMENT-EVENT-RACE
- TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX (child)
- TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON (child)
- TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING (child)
- TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP (child)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §18 (Observability and Cache Economics)
- `stored_artifacts/TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON/`
- `stored_artifacts/TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON/`
- `stored_artifacts/TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT/`

## Related Stored Artifacts
None directly (epic tier — see child tickets).

## Related Code Areas
- `tools/retrieval_cache.py`
- `tools/knowledge_gateway_mcp.py`
- `tools/knowledge_gateway_packet_assembly.py`
- `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`

## Assumptions / Open Questions
- Assumes the frozen 7-entry corpus (`tools/agent-monitoring/kgmcp_baseline_corpus.py`) remains
  the correct measurement instrument for the re-comparison child ticket — if a child ticket finds
  reason to believe otherwise, that's a finding to report, not something to change unilaterally.

## Implementation Notes
N/A — epic ticket, no direct implementation.

## Test Summary
N/A — epic ticket.

## Files Changed
N/A — epic ticket.

## Completion Summary
(Fill in when all child tickets are DONE.)
