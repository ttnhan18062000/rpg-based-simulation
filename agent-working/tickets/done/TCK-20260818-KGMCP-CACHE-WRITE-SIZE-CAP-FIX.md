---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX
phase: done
date: 2026-08-18
tags: [ai, mcp, performance]
---

# TCK-20260818-KGMCP-CACHE-WRITE-SIZE-CAP-FIX

## Title
Fix the retrieval cache write-size cap causing 0/7 real cache hits — CLOSED: already fixed, ticket scoped on stale evidence

## Status
DONE

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
**Superseded — see Completion Summary.** All items below were satisfied by
`TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` before this ticket existed:
- [x] Root cause of the 8192-byte cap's value documented — done by the recalibration hotfix
      (never-measured Phase-0 placeholder).
- [x] Fix landed in `tools/knowledge_gateway_redaction.py` (not `tools/retrieval_cache.py` — this
      ticket's own file-location assumption was also wrong; the cap constant and its check live in
      the redaction module) with `redaction_retention_policy.md` §5 updated in the same change.
- [x] Real run of the frozen 7-entry corpus produced genuine cache writes — 7/7, independently
      verified by the recalibration hotfix.
- [x] Regression tests covering both the accept and still-reject cases were added by that hotfix
      (`TestSizeCap`-related tests, per its own Completion Summary).
- [x] No existing KGMCP test regressed — that hotfix's own scoped suite ran 107/108 passing (1
      known/explained pre-existing failure, documented in its own ticket).

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
Investigation (before any code was touched, per Hard Rule "do not act without validating
context") traced the real rejection path: `perform_cache_write()` in
`tools/retrieval_cache.py` calls `knowledge_gateway_redaction.evaluate_write_candidate()`,
whose `check_size_cap()` enforces `MAX_PAYLOAD_BYTES` — defined in
`tools/knowledge_gateway_redaction.py:68`. Live grep of that file (not the ticket's own,
un-verified `tools/retrieval_cache.py`-only assumption inherited from the epic's summary of
`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`) shows:

```
MAX_PAYLOAD_BYTES: int = 65536            # §5, redaction_retention_policy.md:121 — recalibrated
                                           # by TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION
```

`git log -p -G "65536" -- tools/knowledge_gateway_redaction.py` traces this to commit
`62311b44`, `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` (2026-08-16, closed,
`tickets/done/`). That ticket's own Completion Summary: recalibrated the cap from the
never-measured 8192-byte placeholder to a real, data-derived 65536 bytes (~2.15x the observed
7-entry-corpus maximum of ~30,548 bytes), then **re-ran the real live gateway against a
genuinely cold cache and confirmed 7/7 genuine cache hits** (up from the historical 0/7) —
independently verified, not assumed. Confirmed on the current working tree that the value is
still 65536 (`python3 -c "from tools import knowledge_gateway_redaction as kgr;
print(kgr.MAX_PAYLOAD_BYTES)"` → `65536`), i.e. nothing has regressed this since.

This ticket's own premise — inherited verbatim from this session's earlier exploratory
conversation citing `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`'s 0/7 result as the *current*
state — was stale: that result predates the same-day recalibration hotfix by roughly 30 minutes
of wall-clock ticket-sequence time. No code change is warranted or was made. Per this project's
"stop and report truthfully, even if it looks trivially resolvable" gate-integrity discipline,
the correct action on discovering a ticket's premise no longer holds is to close it honestly as
a no-op, not to invent scope to justify the ticket existing, and not to silently delete the
record of the mistake.

One genuinely new, real finding surfaced during this investigation and is **not** already
covered by any existing child ticket: the recalibration hotfix explicitly, honestly re-measured
§4.1 (latency) and §4.2 (token-reduction) *on this same genuinely-warm, 7/7-hit run* and found
both **still FAIL, 0/7** — i.e., even with caching now genuinely working, the warm path does not
meet the gateway's own proposal thresholds. This strengthens, not weakens, the epic's original
concern, and has been folded into `TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`'s rescoped
Request Summary (its false dependency on *this* ticket has also been removed, since the
recalibration hotfix already satisfies what that dependency was for).

## Test Summary
No code changed; no new tests needed. Verified via direct interpreter check that
`MAX_PAYLOAD_BYTES == 65536` on the current tree (see above) — confirms the prior fix is still
in effect, not regressed.

## Files Changed
None — investigation-only closure.

## Completion Summary
Closed as a no-op: this ticket's premise (the retrieval cache's write-size cap causing 0/7 real
cache hits) was already fixed on 2026-08-16 by `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-
RECALIBRATION`, roughly two days before this ticket was scoped, using a stale citation of
`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`'s pre-fix 0/7 result as if it were current state.
Verified the fix is still in effect on the current working tree (cap == 65536, unchanged since).
No code, test, or doc change was needed or made. The one substantive new finding from this
investigation — that §4.1/§4.2 still FAIL 0/7 even on the now-genuinely-warm path — has been
folded into the epic's recomparison child ticket rather than lost. The parent epic
(`TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC`) and the recomparison child ticket
(`TCK-20260818-KGMCP-POST-CAP-FIX-RECOMPARISON`) have been updated in the same pass to remove
the stale premise and the now-satisfied dependency.
