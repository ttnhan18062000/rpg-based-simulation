---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY
phase: done
date: 2026-09-04
tags: [world]
---

# TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY

## Title
CampaignOrchestrator._build_initial_state() never carries Region/Place into per-episode AuthoritativeState

## Status
DONE

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
- [x] `CampaignOrchestrator._build_initial_state()` calls `WorldCompiler.compile()` (or equivalent) and
  populates `AuthoritativeState.regions`/`.places` for both episode-0 and survivor-reconstruction
  branches.
- [x] `TownResolutionSystem.resolve()` no longer early-exits for a Campaign-mode episode with declared
  regions, and its now-live behavior is verified deliberately (not assumed neutral).
- [x] New/updated tests cover: episode 0 gets compiled regions/places; a later episode (survivor
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

`_build_initial_state()` now takes the episode's own `SimulationScenarioDefinition` (previously only
`episode_seed`) and really compiles it:

```python
world_repo = WorldRepository("data/worlds")
world_spec, world_context = world_repo.load_world_with_context(spec.world_composition)
compiled_state, _compile_report = WorldCompiler.compile(world_spec, seed=episode_seed, context=world_context)
```

`regions=`/`places=` from that compile are threaded into **both** return branches (the episode-0
fresh-start branch and the survivor-reconstruction branch). The one call site,
`run_episode()`, already had `spec` in scope and now passes it through.

**Resolved open question 1 (compile-once vs. compile-per-episode)**: compile fresh per episode.
The ticket named "check the non-Campaign entrypoints' pattern first" — every one of them
(`src/cli/entry.py`, `src/api/engine_manager.py`, `src/lab/orchestrator.py`,
`src/worldbuilding/cli.py`) compiles once per *run* with that run's own seed. A Campaign episode is
that entrypoints' unit-of-work equivalent (each episode already gets its own deterministic
`episode_seed = base_seed + idx`), so compiling per episode preserves the same seed-to-compile
relationship rather than freezing episode 0's topology across a whole campaign.

**Deliberately NOT threaded**: `entities=`, `buildings=`, `resource_nodes=`, `town_tiles=` and every
other compiled field. Only region/place topology comes from the compile. This is load-bearing —
letting the compiled world's own entity roster leak in would silently break this method's
pre-existing contract (episode 0 has an empty roster; episode N>0's roster is exactly the
reconstructed survivors) and every carry-forward assertion that depends on it. Verified empirically:
`entities` is still `{}` on the episode-0 path after the change.

**Resolved open question 2 (is making `TownResolutionSystem.resolve()` live actually neutral?)** —
verified directly, not assumed. Against a real compiled `unit_faction_tension` state:

```
regions populated : 3  -> ['hometown', 'near_forest', 'wolf_den']
places  populated : 2
town_tiles        : 0
entities          : 0     <- ep-0 carry contract preserved
TownResolution early-exit would fire? False
resolve() ran live path (returned new update object): True
```

`town_tiles` is 0 for this world, so pre-fix the `not has_town and not has_regions` guard fired and
the whole regional pass was skipped; post-fix `has_regions` is True and `resolve()` genuinely runs
its live path (returns a *new* update object rather than the identical one the early-exit returns).
No existing Campaign-mode test asserts anything about tax/suppression side effects, and the full
Campaign-mode suite stays green — so the newly-live path is additive here, not a silent behavior
regression.

**Parity ledger**: checked and deliberately not updated — no existing entry claims Campaign-mode
region/place inertness (grepped `docs/parity_ledger/*.yaml` for Campaign+region/inert/empty claims,
zero matches), so there is no stale caveat to correct. This ticket's own AC does not ask for one.

**Call sites found only by running the broader suites, not by the ticket's own text** (the reason
its "verify deliberately" instruction mattered): four other test files call `_build_initial_state()`
directly or monkey-patch it, and two build their own local manifests with bare `MagicMock()` episode
specs whose `.world_composition` is a MagicMock rather than a str. All updated in step.

## Test Summary
- **New** (`tests/unit/domains/campaigns/test_campaign_orchestrator.py`, 3 tests):
  `test_build_initial_state_episode_zero_carries_compiled_regions_and_places`,
  `test_build_initial_state_survivor_branch_also_carries_compiled_regions_and_places`,
  `test_town_resolution_no_longer_early_exits_once_campaign_regions_are_populated`.
- **Updated call sites** (signature change): `test_campaign_orchestrator.py` (`_make_manifest`),
  `test_fame_wiring.py` (2 direct calls + new `_episode_spec()` helper),
  `test_progression_planner_three_episode.py` (local `_make_manifest`),
  `test_campaign_runtime.py` (monkey-patch lambda + 1 direct call),
  `test_social_memory.py` (2 monkey-patch lambdas + 2 direct calls).
- **Regression**: `tests/unit/domains/campaigns/`, `tests/integration/campaigns/`,
  `tests/integration/scenarios/test_campaign_runtime.py`,
  `tests/integration/scenarios/test_social_memory.py`,
  `tests/integration/scenarios/test_campaign_chronicle.py`, `tests/integration/culture/`
  → **161 passed, 0 failed**.
- One transient failure appeared mid-run
  (`test_phase9_campaign_runner.py::test_campaign_runner_is_deterministic_for_same_seed`,
  `FileNotFoundError: Manifest not found for run_id`) — reproduced as the known shared-worktree
  `data/runs/` cleanup race (a concurrent sibling task cleaning `data/runs/*` mid-test), not this
  change: the test passes in isolation and on a clean re-run of the full set.

## Files Changed
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()` signature + real compile + both
  return branches; `run_episode()` call site)
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` (helper + 3 new tests)
- `tests/unit/domains/campaigns/test_fame_wiring.py`
- `tests/integration/campaigns/test_progression_planner_three_episode.py`
- `tests/integration/scenarios/test_campaign_runtime.py`
- `tests/integration/scenarios/test_social_memory.py`

## Completion Summary
Campaign-mode episodes now receive real compiled `regions`/`places` in their per-episode
`AuthoritativeState`, closing a general reachability gap that had silently made every
`len(state.regions) == 0`-gated system inert for Campaign mode — `TownResolutionSystem.resolve()`'s
regional tax/suppression/vacancy logic most visibly. Fixed at the one real root
(`_build_initial_state()` never calling `WorldCompiler.compile()`), matching what every
non-Campaign entrypoint already did, for both the episode-0 and survivor-reconstruction branches.
Scoped tightly: only region/place topology is threaded from the compile, never the compiled world's
own entity roster, so every existing carry-forward contract is preserved. The ticket's two named
open questions were both resolved with real evidence rather than assumption, and the
"is the early-exit removal neutral?" question in particular was verified by directly observing the
guard's inputs and `resolve()`'s live-vs-early-exit return behavior on a real compiled state.

## Post-Closure Disclosure (2026-09-08, found during `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE`'s
own follow-up pass)
This ticket's own fix has a materially higher-stakes consequence than originally scoped, surfaced
by `rpg-feature-planning` and independently re-verified: **the entire war/siege/territory-transfer
subsystem was silently no-op'ing in Campaign mode for the same root cause this ticket fixed.**
`MilitaryConflictPhase._find_contested_region()` (`src/engine/military_conflict.py`) and the
siege-progress loop both key off `state.regions`; with `state.regions` empty (this ticket's own
bug, now fixed), no siege could ever begin, so `FactionState.territory` could never be populated
and `FactionDecisionPhase`'s `EXPAND_TERRITORY` gate could never fire for any faction in any
Campaign-mode episode — not because the mechanism was dead, but because its one real, live
producer (siege completion) was unreachable. Once regions are populated (this ticket's own fix),
the war/siege math itself is fast (`_SIEGE_PROGRESS_DELTA = 0.05`/tick undefended, `-0.02`/tick
defended by ≥3 GUARDs — reaching `progress >= 1.0` in ~20-34 ticks), so this is not expected to be
a long-horizon gap once exercised. Not re-opening this ticket or adding new scope — this note
exists so a future investigator finds the connection rather than re-discovering it, and so this
ticket's own real-world impact is accurately understood as broader than "regional tax/suppression
logic." Whether a real WAR pair persists long enough in practice to actually complete a siege is a
genuine simulation-dynamics question, deliberately left open for a future corpus run now that
regions are populated — not answerable before this fix landed.

**Amended 2026-09-08 (second peer-review pass, independently re-verified): a third affected
subsystem.** `CalamityService.process_world_dynamics()` (`src/world/calamity.py`) selects its
calamity/world-boss spawn target via `[r for r in state.regions.values() if r.calamity_intensity >
0.3]` — with `state.regions` empty, this list is always empty, so calamity/world-boss spawning was
*also* silently no-op'ing in Campaign mode for the same root cause, alongside war/siege/territory-
transfer. Confirmed directly against `src/world/calamity.py`. Same disposition as above: not
re-opening this ticket, this fix already resolves it — recorded here so the full blast radius is
accurately understood.
