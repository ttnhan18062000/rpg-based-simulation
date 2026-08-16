---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT
phase: open
date: 2026-08-16
tags: [ai, mcp, testing]
---

# TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT

## Title
Honestly measure the real Level 2 cache-hit path against proposal §21's full Phase 3 Pilot
Acceptance Criteria

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Proposal §20 states "Completion of Phase 3 is the first production-capable pilot boundary," and §21
lists roughly 18 concrete Phase 3 Pilot Acceptance Criteria the gateway must satisfy. Many are
already satisfied by Phase 1/Phase 2 work (Context Search and Graphify remain independently
callable, a gateway failure never blocks investigation, evidence-validity/lookup-identity
separation, capability-descriptor-bounded routing, branch-scope correctness, no-sensitive-content-
written, database delete-and-rebuild safety). This ticket is where the genuinely NEW criteria —
made real by `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s Level 2 wiring — are honestly
measured for the first time: "Returned content respects the requested budget within a documented
tolerance," "Conflicts are visible and never silently merged," and the closing criterion that
evaluation reports lookup/validation/fallback/assembly/end-to-end latency separately and
demonstrates lower median end-to-end latency and fewer delivered tokens for repeated representative
queries without reducing authoritative-source recall. This mirrors
`TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`'s own "no result may be assumed, only measured"
discipline, extended from Level 1's threshold set to §21's full Phase 3 criteria list.

## Scope
- Reuse the exact same frozen 7-entry corpus (`tools/agent-monitoring/kgmcp_baseline_corpus.py`)
  and the Phase 1/Phase 2 measurement-methodology precedent (`kgmcp_phase1_gateway_runner.py`,
  `kgmcp_phase2_gateway_runner.py`) as the reusable foundation — import pure helpers, never
  reimplement equivalent logic, per this repo's own strict Gate Integrity discipline.
- For each corpus entry, run the real gateway against the now-live Level 2 cache path, capturing
  real per-stage timings (lookup, evidence validation, provider fallback, packet assembly,
  end-to-end) separately — not a single aggregate wall-clock number — per §21's closing criterion's
  explicit requirement.
- Compute and honestly report, for the full corpus, whether:
  - Returned content respects the requested budget within the documented tolerance the
    dedup/budget-enforcement ticket established.
  - Conflicts (where the corpus surfaces any) are visible and never silently merged.
  - Median end-to-end latency on the warm/Level-2-hit path is lower than the appropriate baseline
    (Phase 1's cold baseline and/or Phase 2's Level 1 warm baseline — decide which is the correct
    comparison target in this ticket's own Investigate phase and state the reasoning).
  - Delivered tokens for repeated representative queries are fewer than the appropriate baseline,
    without reducing authoritative-source recall relative to Phase 1/Phase 2's own recorded recall
    counts.
- Re-verify, at real-corpus scale (not merely unit/fixture level), the criteria that depend on
  Level 2-specific behavior newly built by this epic's other child tickets: a changed cited source
  causes a stale rejection of the affected packet; an unrelated changed source does not invalidate
  it; branch-local results are not reused across incompatible branches; relevant uncommitted changes
  invalidate affected cached evidence.
- Write a new results doc and committed fixture, following
  `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`'s own established pattern (never editing that or
  Phase 1's historical record).

## Out of Scope
- Redefining any §21 criterion or excluding any of the 7 corpus entries to force a favorable
  result — the same Gate Integrity discipline `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` and
  `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` both established applies here with equal force.
- Fixing any criterion found to fail after this measurement — this ticket measures and reports; if a
  fix is warranted, that is a separate, later ticket a human reviewer scopes based on this ticket's
  honest findings, mirroring Phase 2's own precedent.
- Re-measuring criteria already conclusively demonstrated by Phase 1/Phase 2's own work and
  unaffected by Level 2 (e.g. "Context Search and Graphify remain independently callable," "a
  gateway failure never blocks repository investigation") — this ticket's own Investigate phase
  should enumerate which of §21's ~18 criteria are genuinely new/Level-2-dependent versus already
  settled, and scope real measurement effort to the former, citing (not re-deriving) the settled
  ones from Phase 1/Phase 2's own results docs.
- Any change to `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or any cache read/write code built by the sibling
  Phase 3 tickets — this ticket is measurement-only.
- Declaring Phase 3 "production-capable" or the epic closed — this ticket reports the real
  measurement; the epic's own closure decision (mirroring Phase 1/Phase 2's own precedent of a
  human reviewer making the final call on an honest result) is not this ticket's to make.

## Acceptance Criteria
- [ ] Each of the 7 corpus entries is run against the real, live Level 2 cache path, with per-stage
      timings (lookup, validation, fallback, assembly, end-to-end) captured and reported separately,
      per §21's closing criterion's explicit requirement.
- [ ] Budget-respecting behavior is measured against real requests using a constrained
      `budget_tokens` value and reported honestly, whatever the result — no assumption that the
      dedup/budget-enforcement ticket's unit-level tests guarantee real-corpus-scale compliance.
- [ ] Conflict visibility (where the corpus surfaces any provider disagreement) is checked and
      reported — a real test/measurement, not a documentation claim of "conflicts are structurally
      possible to represent."
- [ ] Median end-to-end latency and delivered-token counts for the warm/Level-2-hit path are
      computed against a clearly stated baseline (with the choice of baseline justified in
      Implementation Notes) and reported honestly, including a FAIL if the real numbers do not show
      an improvement.
- [ ] Authoritative-source recall is recomputed and compared against Phase 1/Phase 2's own recorded
      recall counts — any regression is reported plainly, not glossed over.
- [ ] Stale-rejection, unrelated-change-non-invalidation, branch-partition, and uncommitted-change
      invalidation criteria are each independently re-verified at real-corpus (not fixture-only)
      scale where the corpus makes this feasible; where a criterion cannot be exercised by the real
      7-entry corpus, this is disclosed explicitly rather than silently marked satisfied.
- [ ] If any §21 criterion is missed, the ticket's own Completion Summary states this plainly — no
      criterion is redefined, no entry excluded, and Phase 3 is not characterized as more successful
      than the real numbers support.
- [ ] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added, certifying this
      ticket's measurement tool and honest reporting as correct and tested — not the measured
      gateway/cache performance itself, mirroring `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON`'s
      own `INFRA-344` precedent.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC (parent; this ticket closes its acceptance loop)
- TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING (dependency; supplies the real Level 2
  cache-hit path to measure)
- TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT (supplies the budget-tolerance mechanism
  this ticket measures against)
- TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION (supplies the invalidation behavior this
  ticket re-verifies at corpus scale)
- TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON (DONE; supplies the corpus, methodology precedent, and
  the Level 1 warm-path 7/7-hit baseline — post-hotfix — this ticket's Level 2 measurement compares
  against)
- TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION (DONE; confirms Level 1's real 7/7
  genuine-hit baseline this ticket's Level 2 latency/token comparison is measured relative to)
- TCK-20260815-KGMCP-P1-BASELINE-COMPARISON (DONE; the original cold-path baseline both Phase 2's
  and this ticket's measurements ultimately trace back to)

## Related Docs
- `docs/plans/knowledge-gateway-mcp-proposal.md` §21 (Phase 3 Pilot Acceptance Criteria — the full
  list this ticket measures against)
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` §4
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` (the honest 0/7 →
  7/7 Level 1 result this ticket's Level 2 comparison builds on)
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` (original cold-path
  result, never edited)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/kgmcp_baseline_corpus.py` (frozen corpus, reused verbatim)
- `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py`,
  `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` (the runner precedents this ticket's own
  runner imports pure helpers from and mirrors the shape of, extended for Level 2 per-stage timing
  capture)

## Assumptions / Open Questions
- Whether this ticket's own runner is a new file or an extension of `kgmcp_phase2_gateway_runner.py`
  is left to this ticket's own Investigate phase, mirroring how Phase 2's own recomparison ticket
  made this same choice relative to Phase 1's runner.
- Which baseline (Phase 1 cold, or Phase 2 Level-1-warm) is the correct comparison target for §21's
  closing "lower median end-to-end latency and fewer delivered tokens" criterion is not decided
  here — Investigate should determine the most defensible comparison (likely Level-1-warm, since
  that is the immediately prior working state Level 2 must improve on) and state the reasoning
  explicitly.
- Whether the frozen 7-entry corpus is sufficient to exercise every §21 criterion (e.g. real
  provider conflicts, which may not naturally occur across all 7 entries) is an open question this
  ticket's Investigate phase must resolve — where the corpus cannot exercise a criterion, that
  limitation must be disclosed, not silently worked around by inventing a non-frozen 8th entry or
  synthetic data presented as corpus-derived.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
