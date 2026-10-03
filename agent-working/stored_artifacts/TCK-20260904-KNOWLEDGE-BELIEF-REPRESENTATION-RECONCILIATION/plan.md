---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION
artifact_type: plan
tags: [content]
---

# Plan — TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION

Decision (per this ticket's own Scope, options + recommendation, no unilateral merge):

**Chosen: Option 1 — keep both, document the split explicitly.** Reconciling/merging would be
over-engineering: the investigation confirmed `BeliefEntry` and `KnowledgeFact` genuinely serve
different pipeline stages (raw/observed/contested vs. structured/queried/assimilated), dispatched from
a single real call site (`phase.py`), with different real lifecycles (decay + contradiction-tracking vs.
capacity-bounded, no decay). No live consumer needs a fused view today.

Actions:
1. Add a short cross-reference note to both `docs/simulation/belief_and_detour_contract.md` and
   `docs/simulation/domains/information_contract.md` naming the sibling model and the dispatch site
   that decides between them (`phase.py`), so a future reader isn't left to independently re-derive
   this the way this ticket had to.
2. Record the decision in `rpg_design_roadmap.md`'s Knowledge/Belief axis section.
3. File a small, separate, non-blocking follow-up ticket for the `"combat_risk"` dead-code read
   (`src/domains/cooperation/evaluators.py:47`) — out of scope for this ticket's own decision, but a
   real finding surfaced during it, per this repo's own "file tickets for workflow/code gaps" pattern.
4. No merge/bridge implementation — explicitly not warranted by the evidence.
