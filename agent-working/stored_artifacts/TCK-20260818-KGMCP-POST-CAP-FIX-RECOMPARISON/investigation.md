---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON
artifact_type: investigation
tags: [ai, mcp, performance, testing]
---

# Investigation: TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON

## What Was Actually Missing

Confirmed by reading both prior comparison tickets in full:
- `TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`'s own runner (`_run_gateway()`) calls
  `_run_knowledge_context(query=query_text)` exactly once per entry, against whatever cache state
  happened to exist — explicitly cold/near-cold by the ticket's own design (Step 1 decision only
  addresses fixture-reuse staleness, not cache state).
- `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` re-measured §4.1/§4.2 (absolute
  proposal thresholds) on a genuinely warm run and found both FAIL 0/7 — but this is a different
  measurement axis (absolute threshold vs. baseline) from Phase 4's *relative* paired comparison
  against direct tool calls.

No ticket had run Phase 4's specific paired-comparison methodology against a warm gateway. That is
this ticket's entire scope.

## Reusable Methodology

`tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`'s direct-tool call
functions, quality-axis computation (`_compute_source_completeness`,
`_compute_context_search_half`, `_compute_graphify_half`), and `_combined_direct_stats` are all
pure/reusable and import cleanly — reused unmodified, never reimplemented, per this repo's
established convention for successor comparison runners.

`kgmcp_phase3_gateway_runner.py::_install_timing_spy()` is the established, real, structural
verification technique for "is this actually a cache hit" (assemble_packet call count == 0, not
`response["cache"]` alone) — reused unmodified.

## Real Gateway Availability — Confirming the Prior Ticket's Correction

`TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING` corrected a false "environment blocked"
finding mid-session (wrong Python interpreter). Confirmed directly at the start of this ticket:
`.venv/bin/python3 -c "from knowledge_gateway_mcp import _run_knowledge_context; ..."` runs the
real gateway without issue — no special setup needed, matching that ticket's own corrected
conclusion.

## Design Decision

Wrote a new runner (`kgmcp_phase4_warm_direct_tool_comparison_runner.py`) rather than editing the
frozen Phase 4 runner — matches every prior comparison ticket's own precedent (Phase 2/3/4 each
wrote their own runner rather than editing a predecessor's). The only new logic is
`_run_gateway_warm()`: a cold priming call (discarded), then a real, timed, spied warm call.
Everything else (direct-tool calls, quality axis, corpus, assembly into the final report shape) is
imported directly from the frozen Phase 4 runner.

## Real Result

Cleared both cache tables, ran the corpus once (cold priming + warm measurement per entry, per the
runner's own design — genuine warmth structurally verified on all 7). Real, honest result:

- **Warmth**: 7/7 structurally verified (`assemble_packet` call count 0 on every measured call).
- **Latency**: gateway still slower on all 7/7 entries, but ratios drop from the cold measurement's
  1.31x-3.76x to 1.06x-1.34x.
- **Tokens**: gateway still heavier on all 7/7 entries, ratios drop from 1.04x-2.93x cold to
  1.05x-1.98x warm.
- **Reviewer verdicts**: identical distribution to cold — 6/7 `direct_equal_or_better`, 1/7
  `mixed` (`Q3_requirement_completeness`), 0/7 `gateway_equal_or_better`.

Full per-entry data and rationale in the committed fixture and
`docs/engine/contracts/knowledge_gateway_mcp/phase4_warm_direct_tool_comparison.md`.

## One Disclosed, Unexplored Observation

Even a structurally-proven cache hit still takes ~1.6-1.8 seconds of wall time — much more than a
"read one row, skip the provider round trip" operation would suggest. Not root-caused further here
(out of this ticket's measurement-only scope) — recorded as a real finding for whoever next
decides whether to invest in closing the remaining gap.
