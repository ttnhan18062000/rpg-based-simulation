---
status: historical
layer: ai
authority: P1
audience: agent
tags: [ai, mcp, testing, performance]
---

# Knowledge Gateway MCP — Warm-Gateway Direct-Tool Comparison Results

Source ticket: `TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`. Answers the one question left open
after `TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`'s cold-cache comparison: does a genuinely
*warm* (cache-hit) gateway change the verdict against calling Context Search / Graphify / the
Parity Ledger adapter directly? Full per-entry data is committed at
`tests/tools/fixtures/kgmcp_phase4_warm_direct_tool_comparison_results.json`, produced by
`tools/agent-monitoring/kgmcp_phase4_warm_direct_tool_comparison_runner.py`.

## Why this ticket exists — and a correction along the way

This epic's own child ticket, `TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX`, was originally scoped
to fix a cache write-size cap believed to still be broken; investigation found it had already been
fixed two days earlier (`TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`, 7/7 genuine
cache hits confirmed). That hotfix's own honest re-measurement found the gateway's absolute §4.1/
§4.2 latency/token thresholds still FAIL even genuinely warm — but no ticket had ever run Phase 4's
own *relative*, paired-comparison methodology (gateway vs. direct tools) on a warm gateway; Phase 4
itself was explicitly cold-cache-only by design. This ticket runs exactly that.

Separately, mid-epic, `TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING` briefly and wrongly
concluded the live `context_search` provider was blocked in-session by a missing knowledge-search
stack — a false negative from testing with the wrong Python interpreter (`python3` instead of
`.venv/bin/python3`). That was caught and corrected before that ticket closed, and this ticket
confirms the correction: the real gateway runs fine via `.venv/bin/python3`, no special
environment setup needed.

## Methodology

Reuses Phase 4's frozen direct-tool call functions, quality-axis computation, and corpus
(`tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`, imported, never
reimplemented) with one change: the gateway side is called twice per entry — a cold priming call
(discarded, populates both cache tiers) followed by a real, timed, spied warm call. Genuine warm
status is structurally verified, not assumed from `response["cache"]` alone: `assemble_packet`
(`tools/knowledge_gateway_packet_assembly.py`) is wrapped with a pass-through timing spy
(`kgmcp_phase3_gateway_runner.py::_install_timing_spy()`, imported, never reimplemented) for the
duration of the measured call, and the measured call's `assemble_packet` call count must be 0 — a
structural proof no fresh assembly ran, meaning the response was genuinely served from cache.

Both live cache tables (`retrieval_provider_result_cache_rows`, `retrieval_context_packet_cache_rows`
— gitignored, untracked local dev-machine state) were cleared once before the run, so every entry's
priming call is a genuine cold write, not a leftover hit from earlier session activity.

## Headline result: genuine warmth structurally verified on all 7 entries; the cost gap narrows substantially but never flips

| Entry | Routing shape | Gateway ms | Direct combined ms | Latency ratio | Gateway tokens | Direct combined tokens | Token ratio | Reviewer verdict |
|---|---|---|---|---|---|---|---|---|
| Q1_authoritative_state | definition_terminology_architecture | 1770 | 1571 | 1.13x slower | 2668 | 2546 | 1.05x heavier | direct_equal_or_better |
| Q2_symbol_lookup | symbol_lookup_callers_references | 1626 | 1540 | 1.06x slower | 4975 | 2618 | 1.90x heavier | direct_equal_or_better |
| Q3_requirement_completeness | requirement_completeness_verification | 1654 | 1236 | 1.34x slower | 2904 | 2699 | 1.08x heavier | mixed |
| Q4_historical_rationale | ticket_historical_rationale | 1638 | 1267 | 1.29x slower | 2773 | 2553 | 1.09x heavier | direct_equal_or_better |
| Q5_test_impact | test_impact_of_change | 1740 | 1309 | 1.33x slower | 4953 | 2500 | 1.98x heavier | direct_equal_or_better |
| Q6_ticket_status | ticket_work_status | 1742 | 1317 | 1.32x slower | 2836 | 2198 | 1.29x heavier | direct_equal_or_better |
| Q7_negative_knowledge | broad_task_context | 1641 | 1235 | 1.33x slower | 2745 | 2607 | 1.05x heavier | direct_equal_or_better |

**Every one of the 7 entries is still slower and heavier on tokens through the gateway than calling
the direct tool(s) directly — even with genuine, structurally-verified cache warmth.** No entry is
excluded, no threshold redefined. But the magnitude changed a lot: the cold-cache comparison's worst
latency ratio was 3.76x (Q1); warm, Q1 is the *closest-to-parity* entry at 1.13x. The cold
comparison's ratios ranged 1.31x-3.76x latency and 1.04x-2.93x tokens; warm, they range 1.06x-1.34x
latency and 1.05x-1.98x tokens. **Caching genuinely helps — it just isn't enough to win.**

Every entry's real per-entry latency ratio dropped versus its cold counterpart (verified
mechanically, `test_warm_cost_gap_is_narrower_than_cold_but_did_not_flip_the_verdict`). Even a
structurally-proven cache hit still costs ~1.6-1.8 seconds of wall time — noticeably more than a
"just read a row and return" operation would suggest. This gateway-side floor (present on every
entry, hit or not) is not root-caused further here; it's a real, disclosed observation for a future
ticket to investigate if the gap is judged worth closing further, not this ticket's own scope
(measurement only).

## Quality axis

Reused unmodified from the cold comparison's own methodology. `context_search_half`'s objective
recall proxy fails (`pass: False`) for all 7 entries — identical to the cold measurement's own
result, confirming this is a structural/normalization-shape effect (documented in the cold
comparison's own results doc), not something warm caching changed. `graphify_half_status` is
`"measured"` with zero missing/extra sources for every graphify-routed entry (Q2, Q5, Q7) —
content parity is exact, matching the cold measurement.

**Real per-entry verdicts (hand-authored, reading real retained content, never derived from the
objective proxy):** 6 of 7 entries (`Q1`, `Q2`, `Q4`, `Q5`, `Q6`, `Q7`) are judged
`direct_equal_or_better`; 1 of 7 (`Q3_requirement_completeness`) is judged `mixed` — the same
distribution as the cold measurement. Q3's `mixed` rationale carries forward the cold measurement's
own workflow-convenience argument (one gateway call returns Context Search excerpts plus a live
Parity Ledger check where direct needs two calls), now cheaper to exercise (1.34x cost vs. the cold
run's much larger ratio). No entry is judged `gateway_equal_or_better`. Full per-entry rationale is
in the committed fixture's `quality.reviewer_judgment.rationale` field.

## Overall honest verdict — this epic's decision-support deliverable

**Caching narrows the gap substantially but does not close it.** A genuinely warm gateway is
measurably, meaningfully closer to direct-tool cost than a cold one — but it never wins, on any of
7 representative query types, on either latency or token cost, even with cache warmth
structurally proven rather than assumed. Combined with this epic's other findings (§4.1/§4.2
absolute thresholds FAIL 0/7 even warm, per the recalibration hotfix; §21 #12 budget-tolerance now
7/7 PASS after the JSON-overhead accounting fix — a different, budget-constrained measurement, not
in tension with this one), the honest picture is: KGMCP's caching and budget-accounting mechanisms
now work correctly and as designed, but the gateway's own routing/assembly/redaction overhead is
large enough that, on this corpus, it is not yet cost-competitive with an agent simply calling the
underlying tools directly — warm or cold. Per this ticket's own Out of Scope, whether to invest in
closing that remaining overhead, accept it for the quality/workflow-convenience trade this doc's Q3
case illustrates, or reconsider the gateway's value proposition entirely is a separate, later,
human-reviewer call — not decided here.

## Cross-references

- `tools/agent-monitoring/kgmcp_phase4_warm_direct_tool_comparison_runner.py` — the runner that
  produced this measurement.
- `tests/tools/fixtures/kgmcp_phase4_warm_direct_tool_comparison_results.json` — full per-entry,
  real committed data, including the hand-authored `quality.reviewer_judgment` objects.
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md` — the cold-cache
  comparison this ticket reruns warm (never edited — this doc cross-references it instead).
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md` — the
  §4.1/§4.2 absolute-threshold warm measurement (FAIL 0/7) and the §21 #12 budget-tolerance
  measurement (now 7/7 PASS) — both distinct from, and not in tension with, this doc's relative
  comparison.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §18, §20, §21 — the requirements this document
  and its siblings answer.
- `staging_artifacts/TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON/` — this ticket's own
  investigation/plan/test_plan.
