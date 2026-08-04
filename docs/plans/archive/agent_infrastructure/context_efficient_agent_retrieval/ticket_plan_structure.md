---
status: historical
layer: ai
authority: P2
audience: developer
maturity: shipped
date: 2026-07-28
archived: 2026-08-04
tags: [ai, workflows, process-improvement]
---

# Ticket Plan Structure — Context-Efficient Agent Retrieval and Observability

Guide for `/create-tickets`'s Comprehend/Structure phases when parsing
`idea_context_efficient_agent_retrieval_observability.md`.

## Scope this batch to Phase 0-1 of the source doc's "Sequenced Future Epic" only

The source doc is explicit that this is a 7-phase epic gated by evidence at each
step ("does not authorize a new mandatory workflow gate, a production monitoring
writer change, or a new external retrieval service" — Maturity banner; "must
begin with baseline measurement... no workflow change" — Phase 1). Ticketing the
full 7 phases now would violate that gating.

**This batch should produce:**

1. **One `tier: epic` tracking ticket** for the whole initiative — scope-only,
   no implementation, tracks the 7-phase sequence from the source doc as its
   own reference, lists all 6 Open Decisions as unresolved. Mirrors this
   repo's existing epic-tracking pattern (e.g. `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`,
   `TCK-20260702-OBSISO-EPIC`).
2. **Standard-tier child ticket(s) covering ONLY Phase 0 (Prerequisites) and
   Phase 1 (Baseline and evaluation fixtures)** from the source doc's
   "Sequenced Future Epic" section:
   - Phase 0: confirm the provider-neutral execution identity and monitoring
     writer prerequisite is actually satisfied (it should be — verify against
     `TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC` and
     `TCK-20260721-MONITORING-WRITER-UNIFICATION`, both closed — this is a
     confirmation task, not new implementation).
   - Phase 1: audit current retrieval behavior, repair stale expectations in
     `tools/eval/queries.json`, define scenarios and outcome joins per the
     source doc's "Baseline" and "Offline retrieval evaluation" sections.
     Explicitly **no workflow change** — this phase produces measurement
     artifacts and fixtures only.

**Do NOT ticket in this batch** (these are Phase 2 onward in the source doc,
each gated behind the prior phase's evidence, not yet authorized):
- The `ContextPacket`/`ContextRequest` contract design (Phase 2)
- Any actual retrieval/cache implementation — embedding cache, query-result
  cache, context-packet cache (Phase 3)
- Retrieval observability events or dashboard views (Phase 4)
- Shadow context packets or the new workflow phase (Phase 5-6)

If investigation reveals the Phase 0 prerequisite is NOT actually satisfied,
say so plainly in that ticket rather than silently assuming it — this is the
one thing this batch should genuinely verify, not take on faith from the
source doc's own claim.
