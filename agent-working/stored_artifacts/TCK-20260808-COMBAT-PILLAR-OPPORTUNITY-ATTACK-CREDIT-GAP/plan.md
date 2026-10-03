---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [combat, simulation-quality]
---

# Plan — TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP

## No code fix — real, evidenced conclusion: no bug found

investigation.md resolves both halves of the original concern with direct, same-run evidence:
(1) `entity_killed` events from the opportunity-attack path genuinely reach `CombatScorer` (no
credit gap — the dual-emission-path design already covers this); (2) the real scoring formula
intentionally treats kills as a negative (`attrition`) signal, so the C grade on both probed
worlds is a direct, correct consequence of that formula, not evidence either is under-credited.

## Real deliverable: documentation only (already done during Investigate)

`docs/simulation_quality/quality_scoring_contract.md` §7's own COMBAT section now cross-references
this real finding — done directly during Investigate since it required no further design work,
matching the same pattern used by the sibling `GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX` ticket.

## Acceptance-criteria map

| Criterion | Satisfied by |
|---|---|
| Real event-types read by CombatScorer reported | investigation.md |
| Real combat event volume measured, compared | investigation.md — same-run instrumentation, `urban_political` vs `wilderness_survival` |
| Real, evidenced conclusion: gap vs. genuine low activity | Neither — a real scoring-direction misunderstanding in the ticket's own original premise, resolved with the real weights config |
| If gap found: fix + re-verify | N/A — no gap found |
| If no gap: documented, not silently closed | `quality_scoring_contract.md` updated |
| Scoped pytest passes | N/A — no code change |
