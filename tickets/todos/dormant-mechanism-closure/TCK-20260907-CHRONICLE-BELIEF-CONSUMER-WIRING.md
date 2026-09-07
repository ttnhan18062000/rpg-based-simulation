---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING
phase: open
date: 2026-09-07
tags: [simulation-quality, architecture]
---

# TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING

## Title
Wire idea 62's FidelityState and idea 63's BeliefInstitution into a live per-tick consumer

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) — new child
ticket, not in the original 6-ticket plan. Split out of
`TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS` on 2026-09-07 after that ticket's own
investigation found the epic's original premise for idea 62 ("blocked on idea 63 not existing")
was stale — both idea 62 (Chronicle Fidelity Drift, `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`) and
idea 63 (Belief Institution, `TCK-20260905-BELIEF-INSTITUTION-DESIGN`) shipped 2026-09-05, each
explicitly disclosed at ship time as having "no live consumer yet" — a structurally identical gap
to idea 56 (Drifting Loyalty) and idea 57 (Living Legend) before this same epic's own
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`/`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`
tickets bridged those into `AdventureRouteScorer.score()`'s live `personality_bias` mechanism.

Real user decision, 2026-09-07 (via `AskUserQuestion`): scope and build this wiring now rather than
leave it as a disclosed-but-deferred gap.

## Scope
- Confirm during Investigate (do not re-trust this Request Summary's own citations, re-verify
  against real code) exactly how `CampaignState.historical_drift: Dict[str, FidelityCarryForward]`
  (`src/domains/fidelity/model.py`) and `CampaignState.belief_institutions: Dict[str,
  BeliefInstitutionCarryForward]` (`src/domains/belief_institution/model.py`) are populated
  end-of-episode, and confirm the same `Kernel`/`CampaignState` per-tick reachability gap this
  epic's own P1 bridge ticket (`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`) already solved for
  `region_cultures`/`legend_facts` applies here too (i.e. these two fields likely need the *same*
  bridge-into-`AuthoritativeState` treatment, not a new bridge mechanism — check whether
  `AuthoritativeState` already carries them or needs new fields, following the exact pattern
  `region_culture_states`/`entity_legend_facts` established, including their
  `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` carry-forward fix — do not repeat
  that regression; add any new field to `ApplyPath.apply_generation()`'s carry-forward list in the
  same change that adds it to the constructor).
- Determine the real, evidence-backed consumer point. `FidelityState.fidelity` (event-memory
  accuracy, decays with Era-distance) and `BeliefInstitution.belief_strength` (a Clan's organized
  reverence around a real legendary event) are conceptually distinct from `LegendFact.fame`
  (individual renown) — do not assume the exact same `QUEST_OPPORTUNITY` branch idea 57 used is
  automatically correct here; investigate which `AdventureRouteScorer.score()` route family(ies)
  a Clan's belief-strength or an event's fidelity would plausibly bias (candidates to evaluate,
  not prescribe: `PROTECT_TARGET` for a clan defending a belief-linked person/place,
  `FORM_PARTY` for belief-driven in-group cohesion — confirm against real `RouteFamily` values and
  real entity/clan-membership data available at scoring time, do not invent a route family that
  doesn't exist).
- Wire the chosen branch(es) into `personality_bias`, following the exact pattern of the Culture
  Drift and Living Legend branches already shipped in `src/domains/adventure/scoring.py`.
- Prove it with a real corpus/calibration run — same evidentiary bar as every other ticket in this
  epic (a real, non-flat, attributable pillar or scoring change, not just a passing unit test).
- Update the relevant parity ledger entries (likely `docs/parity_ledger/social_narrative.yaml` for
  belief institution and `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-FIDELITY-*` entries) and
  `docs/guidelines/intentional_divergences.md` (extend or add alongside the existing §2.53 entry,
  `STRAT-227`) with the same rigor as the idea 56/57 wiring disclosure.

## Out of Scope
- Redesigning `FidelityDeriver`/`BeliefInstitutionDeriver`'s own derivation logic — confirmed
  correct and already shipped; this ticket only wires their real output into a live consumer.
- Any other item from the Dormant Mechanism Closure epic's scope.
- If Investigate finds the real consumer wiring requires a materially larger architecture change
  than the idea 56/57 precedent (e.g. a genuinely new bridge mechanism, not reuse of the existing
  one) — STOP and report back to the orchestrator with concrete options rather than deciding or
  implementing unilaterally. Do not call `AskUserQuestion` directly.

## Acceptance Criteria
- [ ] `historical_drift`/`belief_institutions` reach a real per-tick `AuthoritativeState` consumer,
      confirmed via the same bridge pattern (or an explicitly justified variant) as
      `region_culture_states`/`entity_legend_facts`.
- [ ] At least one real `personality_bias` branch reads fidelity and/or belief-strength data,
      following the existing Culture Drift/Living Legend branch pattern.
- [ ] A real corpus/calibration run shows a non-flat, attributable effect from this wiring.
- [ ] No regression in the multi-tick carry-forward behavior `APPLY-GENERATION-EPISODE-BRIDGE-
      CARRYFORWARD` fixed for the sibling fields — verify these new fields are included in
      `ApplyPath.apply_generation()`'s carry-forward from the same commit that introduces them.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS` (`tickets/done/` — split this ticket out after
  finding the epic's original "idea 62 blocked" premise was stale)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (`tickets/done/` — the original
  `CampaignState`→`AuthoritativeState` bridge pattern this ticket should reuse)
- `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`, `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`
  (`tickets/done/` — the `personality_bias` wiring pattern this ticket should follow)
- `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD` (`tickets/done/` — the carry-forward
  regression class to avoid repeating)
- `TCK-20260905-CHRONICLE-FIDELITY-DRIFT`, `TCK-20260905-BELIEF-INSTITUTION-DESIGN` (`tickets/done/`
  — idea 62/63's own original shipping tickets)

## Related Docs
- `docs/guidelines/intentional_divergences.md` §2.53 (`STRAT-227`)
- `docs/world/belief_institution_contract.md`, `docs/world/chronicle_fidelity_contract.md`
- `docs/parity_ledger/social_narrative.yaml`, `docs/parity_ledger/world_dynamics.yaml`
  (`WORLD-FIDELITY-001`, `WORLD-FIDELITY-002`)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/fidelity/`, `src/domains/belief_institution/`
- `src/domains/campaigns/{state,orchestrator}.py`
- `src/core/state.py` (`AuthoritativeState`)
- `src/engine/apply.py` (`ApplyPath.apply_generation()`)
- `src/domains/adventure/scoring.py` (`personality_bias`)
- `src/ai/goals/adventure_scorer.py`

## Assumptions / Open Questions
- Which specific `RouteFamily` branch(es) fidelity/belief-strength should bias is not decided
  here — real investigation work for this ticket's own Investigate/Plan phases, evidence-backed
  against real `RouteFamily` values and real clan-membership/entity data, not assumed from the
  idea 56/57 precedent alone.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
