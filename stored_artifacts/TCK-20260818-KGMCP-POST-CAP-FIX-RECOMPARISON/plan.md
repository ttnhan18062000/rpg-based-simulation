---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON
artifact_type: plan
tags: [ai, mcp, performance, testing]
---

# Plan: TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON

## Steps

1. New runner `tools/agent-monitoring/kgmcp_phase4_warm_direct_tool_comparison_runner.py`:
   imports Phase 4's frozen direct-tool/quality-axis functions and Phase 3's frozen
   `_install_timing_spy()`, adds only `_run_gateway_warm()` (cold priming call, discarded; then a
   real, timed, spied warm call; `warm_verified` = spy-proven zero `assemble_packet` calls).
2. Clear both live cache tables once before the run (gitignored, untracked local state).
3. Run the corpus, write a NEW fixture
   (`tests/tools/fixtures/kgmcp_phase4_warm_direct_tool_comparison_results.json`) — never
   overwrite the historical cold fixture.
4. Hand-author `reviewer_judgment` per entry, reading real retained content (gateway response,
   direct raw results/stdout/entry_result), same rubric as the cold measurement's own convention.
5. Write `tests/tools/test_kgmcp_phase4_warm_direct_tool_comparison.py`: fixture-shape checks,
   warm-verification checks, honest-no-cherry-picking guard, cold-vs-warm-improvement guard,
   reviewer-verdict-distribution guard, zero-mutation-of-agent-monitoring guard.
6. Write `docs/engine/contracts/knowledge_gateway_mcp/phase4_warm_direct_tool_comparison.md` — new
   doc, cross-references the cold comparison and both prior epic tickets' docs, never edits them.
7. Append a "Further update" paragraph to `docs/plans/knowledge-gateway-mcp-proposal.md` §21.
8. Run full `tests/tools/` regression before considering done.

## Acceptance-Criteria Map

| Criterion | Satisfied by |
|---|---|
| Cache genuinely warmed, verified not assumed | Step 1 (spy), Step 5 (test) |
| Phase 4-style ratios + reviewer_judgment, fresh | Steps 1-4 |
| Plain go/no-go recommendation | Results doc "Overall honest verdict" section |
| No result characterized more favorably than raw numbers | Steps 4, 5 (guard tests) |
| Cross-references (not repeats) the settled §4.1/§4.2 finding | Results doc's own cross-references |

## Scope Guards

- No fix attempted for the found cost gap — measurement and reporting only.
- No change to routing, caching, or packet-assembly logic.
- No modification of the frozen cold-cache fixture or its results doc.
