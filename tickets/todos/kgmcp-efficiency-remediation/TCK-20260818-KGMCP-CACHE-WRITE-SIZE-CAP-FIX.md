---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX
phase: open
date: 2026-08-18
tags: [ai, mcp, performance]
---

# TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX

## Title
Fix the retrieval cache write-size cap causing 0/7 real cache hits

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` honestly measured **0/7** genuine cache hits across
the frozen 7-entry corpus: every real default-budget response payload exceeds the deployed
cache's write-size cap (8192 bytes), so `perform_cache_write()` in `tools/retrieval_cache.py`
rejects every write with `"oversized_payload"`, independently confirmed by two agreeing real
signals on all 7 entries. This is the root blocker for the entire KGMCP epic's value
proposition: nothing else about caching effectiveness, latency improvement, or token-reduction
can be honestly re-evaluated while the cache has never actually cached a real response.

This ticket investigates and fixes the cap so real corpus responses can be written to the cache,
without silently invalidating the cap's original purpose (bounding SQLite row/blob size for the
operational limits documented in `docs/plans/knowledge-gateway-mcp-proposal.md` §9).

## Scope
- Investigate why 8192 bytes was chosen as the cap (check `docs/plans/knowledge-gateway-mcp-
  proposal.md` §9 SQLite operational limits and any parity ledger entry) and whether it was ever
  validated against real response payload sizes before being set.
- Determine the real fix: raise the cap to a value validated against real corpus payload sizes
  (with headroom, not just enough to squeak past today's 7 entries), compress the stored payload,
  or split large responses across the existing L1/L2 cache tiers more aggressively — investigate
  which is consistent with the rest of the cache's design before choosing.
- Update `tools/retrieval_cache.py`'s write path and the SQLite operational-limits doc/parity
  entry together, keeping them in parity per this repo's Authoritative Mechanics Rule equivalent
  for KGMCP (docs and code must not diverge).
- Add a regression test that writes a real (or realistically-sized synthetic) oversized-under-
  the-old-cap payload and asserts it's now accepted, plus a test that a payload past the new,
  larger cap is still correctly rejected (prove the cap still does its job, just at a size that
  reflects reality).

## Out of Scope
- Re-running the Phase 2 or Phase 4 comparisons — that's
  `TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`'s job, sequenced after this ticket.
- The JSON-structural-overhead accounting gap in `assemble_within_budget()` — that's
  `TCK-20260818-KGMCP-BUDGET-JSON-OVERHEAD-ACCOUNTING`, a separate, independent gap.
- Any change to which providers get called, packet assembly logic, or routing — this ticket only
  touches the cache write-acceptance path.
- Deciding whether KGMCP should be kept at all — this ticket unblocks that decision, it doesn't
  make it.

## Acceptance Criteria
- [ ] Root cause of the 8192-byte cap's value documented (why it was originally chosen).
- [ ] Fix lands in `tools/retrieval_cache.py` with the doc/parity entry updated in the same
      change (no divergence between what the code enforces and what's documented).
- [ ] A real (not mocked) run of the frozen 7-entry corpus through `perform_cache_write()`
      produces at least some genuine cache writes where all 7 previously failed —  report the
      real new count honestly, even if it's not 7/7.
- [ ] New regression tests cover both the "previously-rejected, now-accepted" case and the
      "still correctly rejected past the new cap" case.
- [ ] No existing KGMCP test regresses (run the full `tests/tools/test_knowledge_gateway_*.py`
      and `tests/tools/test_retrieval_cache.py` suites, not just this ticket's new tests — this
      is the exact class of gap `TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP` is
      separately fixing at the pipeline level, but this ticket must not be the next instance of
      it).

## Related Tickets
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC (parent)
- TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON (found the 0/7 result this fixes)
- TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE (adjacent payload-size work — read
  before designing this fix to avoid duplicating its accounting-widening approach)
- TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON (depends on this ticket)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §9 (SQLite operational limits), §18
  (Observability and Cache Economics)

## Related Stored Artifacts
(To be created: `staging_artifacts/TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX/` during
implementation — standard tier requires investigation.md/plan.md/test_plan.md.)

## Related Code Areas
- `tools/retrieval_cache.py`
- `tests/tools/test_retrieval_cache.py`
- `tests/tools/test_knowledge_gateway_cache.py`

## Assumptions / Open Questions
- Open: whether the right fix is "raise the cap" vs. "compress/restructure the stored payload" —
  the investigation phase should decide based on real payload size distribution, not guess before
  measuring.

## Implementation Notes
(Fill in during implementation.)

## Test Summary
(Fill in during implementation.)

## Files Changed
(Fill in during implementation.)

## Completion Summary
(Fill in when done.)
