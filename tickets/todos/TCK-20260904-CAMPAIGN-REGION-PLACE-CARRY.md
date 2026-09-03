---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY
phase: open
date: 2026-09-04
tags: [world]
---

# TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY

## Title
CampaignOrchestrator._build_initial_state() never carries Region/Place into per-episode AuthoritativeState

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260904-SETTLEMENT-CULTURE-READ`'s investigation (idea 61, Settlements Develop
Personalities). `CampaignOrchestrator._build_initial_state()`
(`src/domains/campaigns/orchestrator.py:575-655` at time of investigation) constructs
`AuthoritativeState(tick=0, seed=episode_seed)` for episode 0, or reconstructs only
`entities: Dict[int, EntityState]` from `EntityCarryForward` snapshots for later episodes — with
**no `regions=` argument and no `WorldCompiler.compile()` call anywhere in the method.**
`state.regions` is therefore an empty dict for every Campaign-mode episode today.

This is a general reachability gap, not specific to Culture Drift. By contrast, every non-Campaign
entrypoint that constructs an initial `AuthoritativeState` does call `WorldCompiler.compile(spec,
seed=...)` and does get `regions`/`places` populated: `src/cli/entry.py:223-228`,
`src/api/engine_manager.py:136`, `src/lab/orchestrator.py:198`, `src/worldbuilding/cli.py:282`.
`WorldCompiler.compile()` (`src/worldbuilding/compiler.py:322`) is confirmed to construct real
`PlaceState` objects today (idea 66's schema migration landed this).

Corroborating evidence of severity: `TownResolutionSystem.resolve()`
(`src/engine/town_resolution.py:38-43`) early-exits when `len(state.regions) == 0` — meaning
regional tax/suppression/vacancy-signal logic is *also* silently inert for every Campaign-mode
episode today, for the same root cause.

Not urgent: confirmed (by `TCK-20260904-SETTLEMENT-CULTURE-READ`'s own investigation) that none of
the 21 registered corpus worlds runs multi-episode Campaign mode today — Campaign mode is reachable
only via the client-triggered `/api/v1/campaigns` route and a standalone calibration profile
(`campaign_life_arc.yaml`), neither of which is part of the automated corpus pipeline.

## Scope
- Fix `CampaignOrchestrator._build_initial_state()` to call `WorldCompiler.compile()` (or an
  equivalent) and thread `regions=`/`places=` into the constructed `AuthoritativeState`, for both
  the episode-0 branch and the survivor-reconstruction branch (later episodes).
- Confirm `TownResolutionSystem.resolve()` and any other `len(state.regions) == 0` early-exit
  becomes live once `regions` is populated, and that this does not silently change Campaign-mode
  episode behavior in an unintended way (e.g. unexpected tax/suppression effects appearing for the
  first time) — verify deliberately, don't just assume the early-exit removal is neutral.

## Out of Scope
- The second, distinct plumbing gap this ticket's own parent investigation flagged: even after
  Region/Place carry is fixed here, `CampaignState.region_cultures` still would not automatically
  reach in-episode `AuthoritativeState`/`EntityState` — no field currently threads it through. That
  is a further, even-later dependency for any idea (56/57/61/62) wanting *in-episode* (not just
  post-episode-query) culture-biased entity behavior. Not solved by this ticket.
- Wiring `CulturalBiasApplicator`/`MotivationBiasService`/`SettlementPersonalityService` into any
  per-tick entity-decision system — unrelated to this ticket's Region/Place-carry scope.
- Fixing `register_campaign()`'s zero-production-call-sites gap (`src/api/routes/campaigns.py:40-50`)
  — a separate, pre-existing reachability issue at the API-registry layer, not the
  `AuthoritativeState`-construction layer this ticket addresses.

## Acceptance Criteria
- `CampaignOrchestrator._build_initial_state()` calls `WorldCompiler.compile()` (or equivalent) and
  populates `AuthoritativeState.regions`/`.places` for both episode-0 and survivor-reconstruction
  branches.
- `TownResolutionSystem.resolve()` no longer early-exits for a Campaign-mode episode with declared
  regions, and its now-live behavior is verified deliberately (not assumed neutral).
- New/updated tests cover: episode 0 gets compiled regions/places; a later episode (survivor
  reconstruction) also gets compiled regions/places; existing Campaign-mode carry-forward tests
  (entities, factions, culture, progression, social memory) remain unaffected.

## Related Tickets
- TCK-20260904-SETTLEMENT-CULTURE-READ (parent investigation; the read-side consumer this ticket's
  gap blocks from in-episode reachability)
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (same underlying Region/Place schema family)

## Related Docs
- docs/world/culture_drift_contract.md
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/domains/campaigns/orchestrator.py (_build_initial_state)
- src/worldbuilding/compiler.py (WorldCompiler.compile)
- src/engine/town_resolution.py (TownResolutionSystem.resolve — len(state.regions) == 0 early-exit)
- src/domains/campaigns/state.py (CampaignState.region_cultures — out-of-scope second gap, named for
  context only)

## Assumptions / Open Questions
- Whether `_build_initial_state()` should call `WorldCompiler.compile()` fresh each episode
  (deterministic per `episode_seed`, matching non-Campaign entrypoints) or compile once at
  `CampaignManifest` construction and reuse across episodes — an implementation decision for
  Plan, not resolved here. The non-Campaign entrypoints' pattern (compile once per run) is the
  natural precedent to check first.
- Whether making `TownResolutionSystem.resolve()` live for Campaign mode changes any existing
  Campaign-mode test's expected output (none of the 21 corpus worlds exercises this today, but
  Campaign-mode's own unit/integration test suite might) — must be checked directly during
  implementation, not assumed silent.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
