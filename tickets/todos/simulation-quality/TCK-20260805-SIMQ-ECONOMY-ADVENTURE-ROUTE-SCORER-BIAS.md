---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS
phase: open
date: 2026-08-05
tags: [simulation-quality, economy, adventure]
---

# TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS

## Title
Investigate whether AdventureRouteScorer's craft/buy selection bias is a miscalibration or a correct reflection of archetype incentives

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` (done) investigated why no entity ever forms an
accepted harvest/craft/trade objective, fixed the general `TacticalDecisionSystem` routing gap, and
precisely isolated 3 remaining contributing factors via real full-corpus verification. Factor 3 is
fixed (`TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION`). Factor 1
(`ENABLE_ADVENTURE_ROUTING` defaulting OFF) is a deliberate DA-ruled design boundary
(`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`), not in scope here. Factor 2 is this ticket:
`AdventureRouteScorer` (`src/domains/adventure/`) never selects `craft_upgrade`/`buy_upgrade`
routes even in the 2 corpus runs where `ENABLE_ADVENTURE_ROUTING` is on — empirically confirmed
0/492 and 0/342 real selections, consistently outscored by `form_party`/`gather_resource`.

**This is a realistic RPG simulation.** Whether that 0-selection result is a genuine scoring
miscalibration, or a correct reflection that this corpus's entity archetypes rarely have a
legitimate in-fiction reason (perceived need, opportunity, resource proximity) to prefer craft/buy
over party-forming or gathering in the situations they face, is not yet known. This ticket must
determine which before proposing any scoring change — a fix that simply forces craft/buy routes to
score higher, without a legible cognitive/action-layer justification, would manufacture an
unrealistic route the design never intended, trading one artificial signal (ECONOMY's silence in
scoring) for another (unmotivated harvesting/crafting behavior).

## Scope
- Investigate `AdventureRouteScorer`'s scoring inputs and bias terms for `craft_upgrade` and
  `buy_upgrade` route kinds, and the entity states in the 2 routing-enabled corpus runs where they
  were never selected.
- Determine, with evidence, whether the 0-selection outcome reflects: (a) a genuine scoring bug or
  miscalibration (e.g. a bias term that's structurally impossible to overcome, or a bug that always
  zeroes/undervalues these route kinds regardless of entity state), or (b) a correct reflection of
  those archetypes' actual circumstances (e.g. they never have inventory/need states that should
  legitimately trigger craft/buy).
- If (a): propose and implement a targeted, evidence-justified scoring fix — the ticket's plan.md
  must cite the specific entity state(s) that should have triggered a route and didn't, and connect
  the fix to a real cognitive/action-layer path (not a blanket weight bump).
- If (b): no scoring change — document the finding and close as "confirmed correct, not a gap."

## Out of Scope
- Factor 1 (`ENABLE_ADVENTURE_ROUTING`'s default) — a separate DA-ruled policy question, not
  reopened by this ticket.
- Re-litigating the general routing/wiring fix already landed in
  `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` or
  `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` — both are correct and closed.
- Any scoring change to `form_party`/`gather_resource` themselves — only craft/buy's own scoring
  terms are in scope, and only if diagnosed as a genuine miscalibration.
- Adding new content/archetypes to the corpus to manufacture craft/buy opportunities — that would
  be its own separate, deliberate content decision, not this ticket's investigation-first scope.

## Acceptance Criteria
1. Investigation produces concrete evidence (not speculation) for whether the 0/492, 0/342 outcome
   is a scoring miscalibration or a correct reflection of archetype incentives — citing specific
   entity states, route-score breakdowns, or scorer code paths.
2. If a fix is implemented, it is justified in `plan.md` by a specific, named cognitive/action-layer
   scenario where craft/buy should legitimately have won and didn't — not a generic "increase the
   weight" change.
3. If no fix is warranted, the ticket closes with the finding documented in
   `docs/simulation_quality/current_state.md` and `docs/audits/D20_simq_quality_status_review.md`,
   explicitly correcting Finding 2's "Factor 2" status from open to resolved/confirmed-correct.
4. Regression tests (`test_grade_regression.py` for ECONOMY, plus any adventure-routing-specific
   tests under `tests/`) pass after any change.
5. If a scoring change lands, verify via a fresh calibration run (not just unit tests) that craft/buy
   routes are now selected in circumstances that make in-fiction sense — spot-check at least one
   concrete example in the Completion Summary.

## Related Tickets
- `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` — the investigation and general fix this ticket
  follows on from; source of the Factor 1/2/3 breakdown.
- `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` — Factor 3's fix, confirmed to have zero
  corpus-wide effect on its own, consistent with Factors 1/2 still blocking.
- `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` — the DA ruling behind Factor 1 (out of scope here, cited
  for context only).

## Related Docs
- `docs/simulation_quality/current_state.md` — Finding 2 in the 2026-08-05 refresh, full Factor
  1/2/3 breakdown.
- `docs/audits/D20_simq_quality_status_review.md` — Finding 2, Item B2 in the Candidate Work Items
  table.
- `docs/parity_ledger/infrastructure.yaml` (INFRA-242) — related ECONOMY finding detail.
- `stored_artifacts/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP/investigation.md` — prior
  investigation's full evidence trail, warm-start reference for this ticket's own investigation.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP/` — plan.md, investigation.md,
  test_plan.md for the prior ticket in this chain.

## Related Code Areas
- `src/domains/adventure/` (`AdventureRouteScorer`, `RouteToProjectMapper`)
- `src/engine/tactical.py` (`TacticalDecisionSystem.evaluate_entity_intent`)
- `src/domains/adventure/resolver.py` (`ObjectiveIntentResolver`)
- `src/domains/optimization/feature_flags.py` (`ENABLE_ADVENTURE_ROUTING` — read-only reference)

## Assumptions / Open Questions
- Assumes the 2 routing-enabled corpus runs referenced (0/492, 0/342) are still reachable/reproducible
  from the prior ticket's calibration artifacts or a fresh run — investigation phase must confirm
  this before proceeding.
- Open question the investigation phase must resolve: is there *any* entity state in the current
  corpus that should legitimately prefer craft/buy, or does closing this gap require corpus content
  changes that are explicitly out of scope for this ticket (in which case the ticket closes as
  "confirmed correct, no fix, corpus-breadth expansion is a separate future decision")?

## Implementation Notes
(fill during implementation)

## Test Summary
(fill during implementation)

## Files Changed
(fill during implementation)

## Completion Summary
(fill during implementation)
