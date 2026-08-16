---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON
phase: open
date: 2026-08-15
tags: [ai, mcp, testing]
---

# TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON

## Title
Honestly re-measure the real cache-hit path against Phase 0's baseline and predeclared thresholds

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` honestly found all 3 §4 thresholds FAIL against
Phase 1's necessarily-cold gateway. This ticket is the other half of Phase 2's own bargain: once
`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` lands a real cache, run the same 7-entry corpus
through the gateway twice per entry (first call cold, second call warm/cached) and report,
honestly, whether §4.1's latency threshold is now met on the warm path — and, separately and
without assuming caching fixes it, whether §4.2's token-reduction threshold is met.

## Scope
- Reuse the exact same frozen 7-entry corpus (`tools/agent-monitoring/kgmcp_baseline_corpus.py`)
  and the exact same Phase 0 baseline fixture as the comparison target — never a modified corpus,
  never a different baseline.
- For each corpus entry, run the real gateway TWICE: once cold (first call, cache miss expected),
  once warm (second call, cache hit expected) — recording real `time.perf_counter()` timings for
  both, and recording whether the second call was genuinely served from cache (not just assumed).
- Compute §4.1 (latency) against the WARM path numbers — this is the fair comparison Phase 1's own
  cold-only measurement couldn't make. Report honestly whether the threshold is now met.
- Compute §4.2 (token reduction) against BOTH the cold and warm path numbers — do not assume the
  warm path automatically satisfies this threshold; report the real numbers for both.
- Compute §4.3 (no-regression-recall) again, reusing `TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-
  TRUNCATION`'s now-fixed evidence-ID normalization — expect recall for the single-provider-routed
  entries (Q2/Q5) to still structurally miss for the same, already-documented architectural reason
  (routing, not caching) — report this honestly again, do not expect Phase 2 to fix it.
- Write a new results doc and committed fixture, following
  `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s own established pattern (never editing that
  ticket's historical record).

## Out of Scope
- Redefining any threshold to force a pass, or excluding any of the 7 entries — the same Gate
  Integrity discipline `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` established applies here with
  equal force.
- Fixing the token-reduction threshold if it's still missed after this measurement — this ticket
  measures and reports; if a fix is warranted, that's a separate, later ticket a human reviewer
  scopes based on this ticket's honest findings.
- Fixing the routing-caused recall miss on Q2/Q5 — architectural, out of Phase 2's scope entirely
  (as the Phase 2 epic's own text already states).
- Any change to `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or the cache read/write code built by the
  dependency ticket — this ticket is measurement-only.

## Acceptance Criteria
- [ ] Each of the 7 corpus entries is run twice (cold + warm) against the real gateway, with the
      warm call's cache-hit status independently verified (not assumed) via a real check (e.g. a
      spy/counter proving the provider round-trip was skipped).
- [ ] §4.1 is computed against the warm-path numbers and reported honestly, whatever the result.
- [ ] §4.2 is computed against both cold and warm numbers separately — no assumption that caching
      alone satisfies it.
- [ ] §4.3 is recomputed with the now-fixed evidence-ID normalization; the Q2/Q5 architectural
      miss (if still present) is reported with the same honest routing-design narrative Phase 1's
      own results doc used, not silently dropped or re-explained away.
- [ ] If any threshold is missed, the ticket's own Completion Summary states this plainly — no
      threshold is redefined, no entry excluded, and Phase 2 is not characterized as more successful
      than the real numbers support.

## Related Tickets
- TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC (parent; this ticket closes its acceptance loop)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (dependency; supplies the real cache-hit path to
  measure)
- TCK-20260815-KGMCP-P1-BASELINE-COMPARISON (DONE; supplies the corpus, Phase 0 baseline fixture,
  and the honest all-FAIL cold-path result this ticket extends with a warm-path measurement)
- TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION (DONE; the evidence-ID fix this ticket's §4.3
  recomputation relies on)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (the Phase 1 result
  this ticket extends, never edits)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/kgmcp_baseline_corpus.py` (frozen corpus, reused verbatim)
- `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` (the Phase 1 runner this ticket's own
  runner mirrors the shape of, extended for cold+warm double-calling)

## Assumptions / Open Questions
- Whether this ticket's own runner should be a new file or an extension of
  `kgmcp_phase1_gateway_runner.py` — Investigate should decide based on how much of the existing
  runner's logic is directly reusable versus needing a genuinely different cold/warm double-call
  shape.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
