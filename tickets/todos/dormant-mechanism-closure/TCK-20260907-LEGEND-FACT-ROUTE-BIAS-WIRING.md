---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING
phase: open
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING

## Title
Wire LegendFact into the real route-bias scoring infrastructure — closes out idea 57 (Living Legend)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Split out of `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` on 2026-09-07, sequenced
**after** `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (a hard dependency — this ticket has
nothing to wire into until that ticket's own route-bias scoring formula/data model exists for real).
This is idea 57's (Living Legend, `TCK-20260905-FAME-DERIVER-LEGEND-FACT`) own narrow piece: once
the shared prerequisite infrastructure is real, connect `LegendFact` specifically as one real input
to it, producing a measurable route-bias shift for at least one Townsperson entity — the original
design intent of idea 57, finally reachable in live gameplay.

**Re-scoped, 2026-09-07, per the infrastructure ticket's own investigation and the orchestrating
session's ratified decision**: the real integration point is a new branch inside
`AdventureRouteScorer.score()`'s existing `personality_bias` mechanism (`src/domains/adventure/
scoring.py`), NOT `MotivationBiasService.compute_bias_multiplier()`/`DoctrineResolver`/
`IdentityDoctrine` — those are confirmed-dead legacy code, superseded by `personality_bias`, and are
deliberately not being revived (see `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own
Implementation Notes for the full evidence). Re-confirm this ticket's own citations against whatever
that infrastructure ticket actually shipped before implementing — do not assume the exact shape from
this text alone.

## Scope
- Re-confirm `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own real, shipped shape during this
  ticket's own Investigate phase — do not assume its exact design from this ticket's own text; read
  what actually landed.
- Bridge `LegendFact`/`legend_facts` (`CampaignState`, per idea 57's own shipped ticket) into
  per-tick-reachable state, following the exact same real precedent
  `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` already established for idea 56's `region_cultures`
  signal (a snapshot field on `AuthoritativeState`, populated once per episode by
  `CampaignOrchestrator._build_initial_state()`).
- Convert the bridged `LegendFact` data into whatever tag/doctrine-shaped input the now-real
  infrastructure (from `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`) expects —
  `LegendFactService.to_world_signal()` (`src/domains/fame/legend.py`) may already do part of this
  conversion; confirm and reuse rather than duplicate.
- Add a real, end-to-end test proving a `LegendFact` about a real legendary subject produces a
  measurable, attributable route-bias shift for at least one Townsperson entity, through the real
  live pipeline (not a hand-called pure function in isolation).
- Confirm determinism: no unsorted iteration over the bridged `legend_facts` data feeds any durable
  structure's key/iteration order, matching the sibling bridge ticket's own precedent.

## Out of Scope
- Building any part of the shared route-bias-scoring infrastructure itself — that is
  `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own scope, a hard prerequisite for this ticket.
- The Culture Drift bias overlay's own live-reachability — already covered by the infrastructure
  ticket's own Acceptance Criteria, not this ticket's job to re-verify.
- Rebuilding `FameDeriver`/`LegendFactService` themselves — confirmed correct and already shipped.

## Acceptance Criteria
- [ ] A real bridge carries `legend_facts` from `CampaignState` into per-tick-reachable state at
      episode start (mirroring the idea-56 bridge precedent).
- [ ] `LegendFact` data reaches the real route-bias scoring infrastructure built by
      `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`, producing a measurable route-bias shift for
      at least one real Townsperson entity, confirmed via a real end-to-end test.
- [ ] Determinism confirmed for the new bridge, matching the sibling bridge ticket's own bar.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (hard prerequisite — must land first)
- `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` (`tickets/done/` — the investigation both
  this ticket and the infrastructure ticket were split out of)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (`tickets/done/` — the structural precedent for this
  ticket's own `CampaignState` → per-tick bridge)
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (idea 57's own shipped mechanism, the beneficiary)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/world/fame_legend_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/fame/legend.py` (`LegendFactService.to_world_signal()`)
- `src/domains/campaigns/orchestrator.py` (`CampaignOrchestrator._build_initial_state()`)
- `src/core/state.py` (a new `AuthoritativeState` snapshot field, mirroring
  `region_loyalty_pressure`)
- Whatever real consumer `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` builds (`src/domains/
  motivation/`, `src/domains/adventure/`)

## Assumptions / Open Questions
- The exact real shape of `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own deliverable is not
  known here (that ticket hasn't landed yet) — real work for this ticket's own Investigate phase
  once it does.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
