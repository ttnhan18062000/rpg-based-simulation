---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE
phase: open
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE

## Title
Bridge CampaignState's episode-boundary signals into per-tick gameplay — unlocks ideas 56 (Drifting Loyalty) and 57 (Living Legend)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 1 of 6,
highest priority. Ideas 56 (Drifting Loyalty, M6) and 57 (Living Legend Feedback Loop, M5) — the two
most recently shipped ideas among this epic's items — share one root architectural blocker, confirmed
2026-09-07: `LoyaltyDriftService`'s `region_cultures` signal and `FameDeriver`'s `LegendFact` output
both live in `CampaignState` (`src/domains/campaigns/state.py:325,330`), which has zero connection to
the per-tick `Kernel` loop. `Kernel` (`src/engine/kernel.py`) has no `CampaignState` reference
anywhere; `GroupPhase.resolve()` (`src/engine/pipeline_phases/groups.py:28`, the one live caller of
`PartyLifecycleService.check_defection()`/`effective_defection_threshold()`, idea 56's own consumer)
only accepts `(state: AuthoritativeState, update: StateUpdate)`. Today, `LoyaltyDriftService`'s one
live per-tick call site always supplies the backward-compatible `0.0` default; `LegendFact` has zero
live Perception/Motivation pipeline call sites at all.

## Scope
- Design and build a real bridge that carries `CampaignState`'s episode-boundary-derived signals
  (`region_cultures`, `legend_facts`) into per-tick-reachable state at episode start, mirroring the
  existing `EntityCarryForward`/`CultureCarryForward` pattern already used for cross-episode
  entity/culture data — most likely a snapshot field on `AuthoritativeState` populated by
  `CampaignOrchestrator`, not a change to `Kernel`'s own signature (confirm the cheapest real
  architecture during Investigate, don't assume this exact shape is final).
- Wire `LoyaltyDriftService`'s real per-tick call site (inside `GroupPhase`/`PartyLifecycleService`)
  to read the bridged `region_cultures` snapshot instead of always defaulting to `0.0`.
- Wire a real Perception/Motivation consumer for `LegendFact` (`PerceptionUpdatePhase`
  `src/domains/perception/phase.py`, `MotivationBiasService` `src/domains/motivation/service.py`) to
  read the bridged `legend_facts` snapshot and produce a measurable route-bias shift, per idea 57's
  own original design intent.
- Add real tests proving both signals now reach live per-tick gameplay in at least one real corpus
  scenario (this can inform, but does not need to duplicate, M9's own already-authored dormant-idea
  disclosures).

## Out of Scope
- Rebuilding `CultureDeriver`/`FameDeriver`/`LoyaltyDriftService` themselves — all three are confirmed
  correct and already shipped; this ticket only builds the missing delivery path.
- Any other item from the Dormant Mechanism Closure epic's scope.
- Making this bridge generic/reusable beyond these two signals unless doing so is genuinely no more
  expensive — don't over-engineer a framework for a 2-consumer need.

## Acceptance Criteria
- [ ] A real bridge mechanism carries `region_cultures` and `legend_facts` from `CampaignState` into
      per-tick-reachable state at episode start.
- [ ] `LoyaltyDriftService`'s real per-tick call site reads the bridged signal instead of a hardcoded
      `0.0` default, confirmed via a test showing a non-default loyalty-pressure value affecting the
      defection threshold.
- [ ] A real Perception/Motivation consumer reads bridged `LegendFact` data and produces a measurable
      route-bias shift for at least one Townsperson entity, confirmed via a test.
- [ ] Determinism confirmed: no unsorted iteration over the new snapshot data feeds any durable
      structure's key/iteration order (the exact failure class PR #128's own architecture review
      caught once already in this codebase).

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`, `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (the shipped
  mechanics this ticket connects to live gameplay)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/world/culture_drift_contract.md`, `docs/world/fame_legend_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/engine/kernel.py`, `src/engine/pipeline_phases/groups.py`
- `src/domains/campaigns/{state,orchestrator}.py`
- `src/systems/social_systems/party_lifecycle.py`, `src/systems/social_systems/loyalty_drift.py`
- `src/domains/fame/legend.py`, `src/domains/perception/phase.py`, `src/domains/motivation/service.py`

## Assumptions / Open Questions
- The exact real shape of the bridge (snapshot field on `AuthoritativeState` vs. a different
  mechanism) is not decided here — real architecture design work for this ticket's own
  Investigate/Plan phases, likely warranting an architecture-reviewer pass before implementation
  given this touches the Kernel/episode-boundary layer.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
