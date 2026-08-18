---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON
phase: open
date: 2026-08-18
tags: [ai, mcp, performance, testing]
---

# TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON

## Title
Run the still-missing warm-path (genuine cache-hit) gateway-vs-direct-tool comparison

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
**Rescoped 2026-08-18** after `TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX` was closed as a no-op
— its premise (cache write-size cap still broken) was stale: `TCK-20260816-HOTFIX-KGMCP-CACHE-
SIZE-CAP-RECALIBRATION` already fixed it on 2026-08-16 and re-verified 7/7 genuine cache hits.
That same hotfix *also* honestly re-measured §4.1 (latency) and §4.2 (token-reduction) on this
genuinely-warm, 7/7-hit run and found both **still FAIL, 0/7** against the gateway's own absolute
proposal thresholds — so the Phase 2 cold+warm recomparison this ticket originally scoped is
already done; no need to repeat it.

What is still genuinely missing: `TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON`'s live,
paired, gateway-vs-direct-tool comparison ran on a **fresh, cold-cache** gateway (by its own
explicit design) and found the gateway losing on latency and tokens on 7/7 entries. That measures
raw routing/packet-assembly/redaction overhead, not whether a genuinely warm, cache-hit gateway
changes the verdict against direct tool calls. No ticket has ever run Phase 4's *comparison*
methodology (paired against direct tools) with a *warm* gateway. This ticket runs exactly that —
the one real remaining gap — and reports the honest result.

## Scope
- Reuse the exact same frozen 7-entry corpus and Phase 0 baseline fixture as every prior
  comparison in this epic — never a modified corpus, never a different baseline (same discipline
  every prior KGMCP phase held itself to).
- Warm the cache first (one full cold pass through the real gateway per entry, discarded from
  the comparison — this is priming, not the measurement), confirm genuine warm status via a real
  spy/counter (not assumed), then run Phase 4's exact paired-comparison methodology (gateway vs.
  calling Context Search / Graphify / the Parity Ledger adapter directly) across all 7 entries on
  the now-warm gateway: latency ratio, token ratio, and the same falsifiable `reviewer_judgment`
  field Phase 4 used (`test_no_query_type_disadvantage_is_silently_excluded_or_redefined`-style
  guard carried forward).
- Do not re-measure §4.1/§4.2 in isolation — that number already exists (FAIL 0/7, per the
  recalibration hotfix's own honest report) and re-running it here would be redundant, not
  additional evidence. This ticket's unique contribution is the *relative* warm-vs-direct-tools
  comparison, not the *absolute* proposal-threshold comparison.
- Write a new dated results doc following the established phase-results pattern (never editing
  the historical Phase 2, Phase 4, or recalibration-hotfix results docs — append a new one,
  cross-reference all three).
- State a plain go/no-go recommendation on keeping KGMCP over direct tool calls, based on the new
  warm-path numbers — this is the epic's actual decision-support deliverable.

## Out of Scope
- Fixing anything found to still be broken — this ticket measures and reports; if the new numbers
  still show KGMCP losing, that's a finding for a human reviewer to act on, not something this
  ticket tries to engineer around.
- The Q2/Q5 single-provider-routing recall miss — still architectural, still out of scope, same
  as every prior phase.
- Redefining any threshold or excluding any corpus entry to force a more favorable aggregate —
  the same Gate Integrity discipline Phase 1/2/4 established applies here with equal force.

## Acceptance Criteria
- [ ] Cache is genuinely warmed (real priming pass, discarded from measurement) and warm status
      independently verified (not assumed) before the comparison run.
- [ ] Phase 4-style latency/token ratios and `reviewer_judgment` computed fresh for all 7 entries
      on the warm gateway vs. direct tool calls, with the anti-cherry-picking guard test carried
      forward.
- [ ] A plain, unhedged go/no-go recommendation is stated in the results doc and this ticket's
      Completion Summary.
- [ ] No result is characterized more favorably than the raw numbers support (Gate Integrity).
- [ ] Results doc explicitly cross-references (not repeats) the already-settled §4.1/§4.2
      warm-path FAIL 0/7 finding from `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`.

## Related Tickets
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC (parent)
- TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX (closed as no-op — its premise was already handled
  by the ticket below before this epic existed; no longer a real dependency)
- TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION (**already satisfies the "working cache"
  precondition** — 7/7 genuine hits confirmed; also already reports §4.1/§4.2 FAIL 0/7 warm, cross-
  reference rather than repeat)
- TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON (methodology source for cache-hit verification)
- TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON (methodology source for the paired comparison —
  this ticket is that methodology re-run warm instead of cold)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §18

## Related Stored Artifacts
(To be created during implementation.)

## Related Code Areas
- `tools/agent-monitoring/kgmcp_phase4_direct_tool_comparison_runner.py`
- `tools/retrieval_cache.py` (read path only — no changes)

## Assumptions / Open Questions
None — this is a pure re-measurement ticket using established, already-validated methodology.

## Implementation Notes
(Fill in during implementation.)

## Test Summary
(Fill in during implementation.)

## Files Changed
(Fill in during implementation.)

## Completion Summary
(Fill in when done.)
