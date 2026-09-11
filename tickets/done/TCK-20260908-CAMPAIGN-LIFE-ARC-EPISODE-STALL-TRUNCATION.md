---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION
phase: done
date: 2026-09-08
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION

## Title
`campaign_life_arc` episodes produce zero kernel `SimulationEvent`s from ~tick 2 onward — the
stall-detector truncation at ~tick 52 is its correct downstream report, not the bug

**Naming note (2026-09-08, peer review `rpg-feature-planning`):** this ticket's original title
("episodes stall and truncate at ~tick 52") named the symptom the stall detector correctly
reports, not the underlying defect — that framing invites the wrong fix (raising
`STALL_THRESHOLD` past 200 makes the ticket's own AC read "closed" while the simulation is still
dead for ~198 of 200 ticks, and disables the one mechanism that was honestly reporting the
problem). Retitled to name the real finding. **Do not fix this ticket by raising
`STALL_THRESHOLD` or otherwise changing what the stall detector counts** — see amended Scope/Out
of Scope below.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
**The real finding: `campaign_life_arc` episodes produce zero kernel `SimulationEvent`s from
roughly tick 2 onward.** The ~tick-52 truncation is the stall detector correctly reporting that
inactivity 50 ticks later — it is the downstream symptom, not the defect. Confirmed directly from
the originating investigation's own event-stream data (18 `world_emergence_event`s, all at tick 1;
`scenario_objective_progressed` is recorded after `kernel.tick_once()` returns each tick and so
never resets the stall counter) — every simulation-quality measurement made against
`campaign_life_arc` to date was measured on a world that stops doing anything after the first tick.

Found during `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s investigation into
whether Campaign-mode baselines drifted after PR #148. That investigation ran
`campaign_life_arc` (`config/simulation_quality/profiles/campaign_life_arc.yaml`,
`campaign_episodes: 3`) directly against `CampaignOrchestrator.run_episode()`, instrumented to
capture the final `AuthoritativeState` per episode. Result: **every one of 3 episodes completed at
tick 52 — not the configured `tick_limit=200` victory condition.**

Root cause traced (cheaply — one grep, not a deep chase — flagged during that investigation as
worth its own ticket rather than resolved as an aside):
`ScenarioRuntimeService`'s own stall detector (`src/engine/scenario_runtime.py`,
`STALL_THRESHOLD=50`) sets `self._paused = True` once 50 consecutive ticks produce zero simulation
events (`kernel.tick_once()`'s own `_current_tick_event_count`), and the episode's run loop is
gated on `not self._paused` — matching the observed truncation almost exactly (50 + a couple of
ticks for the counter to cross the threshold and the loop to notice, before it can resume). The
JSONL replay for this exact run also shows `3 scenario_stalled` events (one per episode),
corroborating this directly.

**Why this matters beyond the originating investigation**: every future attempt to measure
anything about `campaign_life_arc` — whether war/siege/calamity ever fire at their intended
episode length, SimQ scoring, any future baseline work — is measured over roughly a quarter of the
intended window unless this is understood or fixed. The originating investigation could not
determine whether the PR #148-reactivated war/siege/calamity subsystems fire within a real
200-tick campaign episode specifically because of this truncation, not because those subsystems
are themselves unreachable.

## Scope
- Confirm the "zero kernel events from ~tick 2 onward" finding directly (per-tick
  `_current_tick_event_count` logging across a real `campaign_life_arc` episode), not only via the
  originating investigation's own aggregate JSONL counts.
- Determine WHY the simulation goes event-silent that early — this is the actual defect to find,
  not merely re-confirm the stall detector's report of it. Test the peer-raised hypothesis (not
  yet confirmed — see `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`'s
  cross-reference) that `RuntimeMode.DEGRADED`/`ScanPolicy.EXACT_DIRTY` movement starvation is the
  cause, alongside any other real candidate (e.g. a genuinely quiet, event-sparse narrative-setup
  phase by design — check content/scenario config before assuming a bug).
- If a real gap in event production (or in whatever mechanism should be generating activity) is
  found: fix that underlying cause.
- If the ~50-tick silence is confirmed to be intended, event-sparse content behavior (not a bug):
  document that explicitly as the disposition, with real evidence for why it's intended — do not
  default to this conclusion without positive evidence.
- Once the real silence is fixed (or confirmed intended and something else explains the observed
  truncation), re-run the war/siege/calamity observability question from the originating
  investigation to finally answer whether those subsystems fire in a real, full-length Campaign-mode
  run.

## Out of Scope
- **Raising `STALL_THRESHOLD`, or otherwise changing what the stall detector counts, as a fix.**
  The detector is correctly reporting genuine simulation inactivity — per peer review, this is the
  same class of defect as violating Gate Integrity: the stall detector is a correctness signal,
  not an obstacle, and tuning it to stop reporting the silence would hide the real defect rather
  than fix it. A disposition of "raise the threshold" is not an acceptable closure for this ticket
  under any circumstance short of the event-silence itself being fixed or independently confirmed
  as intended content behavior with real evidence.
- The stall detector's own general design/threshold value for non-Campaign-mode profiles — this
  ticket is scoped to `campaign_life_arc`'s specific observed event-silence, not a general stall-
  detector redesign.
- Tuning or balancing the war/siege/calamity subsystems themselves once they are observable —
  `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own Out of Scope already
  excludes that; this ticket inherits the same boundary.
- Any performance work. Per standing user direction (2026-09-08), only hard failures are fixed
  here; anything found that is "correct but slower" is deferred to the planned performance effort.

## Acceptance Criteria
- [x] Per-tick `_current_tick_event_count` evidence directly confirms the event-silence (not
      inferred only from the stall detector's own aggregate report). Confirmed: 0 on every tick
      from 2 through 52, no exceptions.
- [x] A real determination is made of WHY the simulation goes event-silent: a real gap (e.g. the
      peer-hypothesized `EXACT_DIRTY` movement-starvation link, confirmed or ruled out with real
      evidence) or genuinely intended event-sparse content behavior (with positive evidence, not
      assumed). **Confirmed real gap, `EXACT_DIRTY` hypothesis ruled out**: the episode has zero
      entities throughout — `CampaignOrchestrator._build_initial_state()` never spawns any. See
      Implementation Notes.
- [x] A disposition is recorded and, if a fix is warranted, implemented with test evidence that
      the simulation produces real activity across the episode (not merely that episodes now run
      to their full configured tick count — running longer while still silent is not a fix).
      **Resolved by `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`**: real entities now spawn
      via `CatalogScenarioStateBuilder`, producing genuine, non-zero activity every tick (not
      merely a longer silent run) — re-verified directly here (2026-09-11) with a real,
      uninstrumented 200-tick `campaign_life_arc` episode: `ScenarioObjectiveState.OBJECTIVE_MET`
      at tick 200, `stall_counter=0` throughout, **zero ticks with a zero event count across all
      198 recorded ticks**, 1542 total events across 18 distinct types (combat, cooperation,
      economy, progression, ecology). Independently re-ran the existing
      `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` suite (4/4 passing) before
      trusting this.
- [x] The fix, if any, is NOT a `STALL_THRESHOLD` change or any other alteration to what the stall
      detector counts (see Out of Scope). **Confirmed** — `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-
      SPAWN-WIRING`'s own diff touches only `src/domains/campaigns/orchestrator.py` and
      `src/scenarios/resolver.py`; `scenario_runtime.py`/`STALL_THRESHOLD` untouched.
- [x] `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own Finding 3 (whether
      war/siege/calamity fire within a full-length episode) is revisited once episodes run long
      enough to test it for real, and that ticket's own record is updated if the answer changes.
      **Revisited (2026-09-11), real answer recorded**: in the same real 200-tick, 16-entity run
      above, `war_declared`, `military_conflict_resolved`, `territory_ownership_changed`, and
      `calamity_spawned` all occurred **zero** times. The episode now genuinely runs long enough
      and has real entities to test this — but these specific conditional subsystems (which need a
      persisting war pair or a region crossing `calamity_intensity > 0.3`, per
      `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own citations) did not
      trigger in this one real run/seed. This is a real, honest answer — not "still can't tell" (the
      simulation is no longer silent) and not "confirmed broken" (one run not firing a conditional,
      probabilistic mechanism is not proof of a defect) — recorded as-is in that ticket's own file,
      cross-referenced there rather than re-investigated further here (out of this ticket's own
      scope).

## Related Tickets
- `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT` (origin of this finding; that
  ticket's own Finding 3 explicitly could not answer whether war/siege/calamity fire at full
  episode length because of this truncation)
- `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` — **hypothesized (not yet confirmed)
  shared root cause**, raised by peer review (`rpg-feature-planning`, 2026-09-08): under
  `RuntimeMode.DEGRADED`/`ScanPolicy.EXACT_DIRTY`, non-urgent entities (including freshly-spawned
  ones with no active AI goal) are permanently excluded from movement candidacy; if most of a
  `campaign_life_arc` episode's entities fall into that category, nothing moves, no movement events
  are generated, `kernel._current_tick_event_count` stays at 0, and this ticket's own stall counter
  climbs to the threshold — one phenomenon (event-silence under `EXACT_DIRTY`), not two unrelated
  bugs. Not traced end to end; the cheap falsification test is logging
  `_current_tick_event_count` per tick in a `campaign_life_arc` episode and checking whether it goes
  to 0 at the same tick `RuntimeMode` enters `DEGRADED`. Whoever picks up either ticket first should
  check this before treating the two as independent.

  **Update (2026-09-08): tested and ruled out for this ticket specifically** — see this ticket's
  own Implementation Notes. `DEGRADED`/`EXACT_DIRTY` IS real and present from tick 1, but the
  episode has zero entities throughout, so there is nothing for `EXACT_DIRTY` to exclude — the real
  cause is the missing entity spawn, not movement starvation. The starvation ticket's own findings
  are unaffected by this — only the shared-cause hypothesis is disproven.
- `TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION` — new, filed alongside this
  determination: why the governor enters `DEGRADED` at tick 1 of an essentially empty kernel is
  itself a separate, unexplained oddity, flagged rather than chased here.

## Related Docs
None yet.

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up.

## Related Code Areas
- `src/engine/scenario_runtime.py` (`ScenarioRuntimeService`, `STALL_THRESHOLD`, the stall
  detector itself)
- `src/domains/campaigns/orchestrator.py` (`CampaignOrchestrator.run_episode()`, the caller)
- `config/simulation_quality/profiles/campaign_life_arc.yaml`

## Assumptions / Open Questions
- Whether the ~50-tick silence is expected narrative-setup quiet time or a real content gap is
  the central question this ticket must resolve — deliberately not decided here.
- Whether the stall detector's own zero-event-tick counting is too strict for Campaign-mode's own
  event cadence, or correctly reflects genuine simulation inactivity, is not determined here.

## Implementation Notes

**Root cause confirmed (2026-09-08), per this ticket's own Scope/AC — determination only, no fix
implemented yet.** Ran a clean, uninstrumented falsification test (real
`ScenarioRuntimeService.step()` calls, reading only already-computed
`kernel._current_tick_event_count`/`kernel._current_policy` after each real tick — no
monkeypatching, avoiding the exact instrumentation-overhead confound flagged in
`DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`'s own Request Summary) against a real single-episode
`campaign_life_arc`-shaped manifest. Result:

**`campaign_life_arc`'s episode-0 world has ZERO entities, for the entire run.**
`CampaignOrchestrator._build_initial_state()` (`src/domains/campaigns/orchestrator.py:655-663`),
for the "no alive_carry_forwards" branch, returns
`AuthoritativeState(tick=0, seed=episode_seed, regions=compiled_regions, places=compiled_places)` —
`entities` defaults to `{}`. `ScenarioRuntimeService._build_kernel()` uses that state as-is; it
never spawns anything (unlike `V2EngineManager`'s own kernel-construction path, which explicitly
spawns a hero + goblins via `EntityGenerator`). `tools/calibrate_simq.py`'s own
`_run_campaign_engine()` accepts an `entity_count` parameter but never references it anywhere in
its body — confirmed dead for this path (only `_run_engine()`, the non-Campaign path, uses it).

**This is not a first-episode quirk — it cascades.** `_build_initial_state()`'s branch selection is
`if not alive_carry_forwards`. Episode 0 spawns nobody, so `CampaignState.persistent_entities`
stays empty after it (`_advance_state()` extracts carry-forwards from `final_state.entities`, which
is empty). Episodes 1 and 2 therefore hit the exact same empty-branch on their own
`_build_initial_state()` call. All 3 episodes in the real `campaign_episodes: 3` profile run
entity-less from tick 0 to their own stall at ~tick 52, independently.

Per-tick trace (single episode, `MAX_STEPS=70`, real `step()` calls): tick 1 has 7 events (matches
the earlier investigation's own JSONL — `world_emergence_event`, `POPULATION_MIGRATION`-category,
one-time seeding); ticks 2 through 52 (the observed stall point) are event_count=0 on every single
tick, with zero exceptions. `governor_mode=DEGRADED` and `scan_policy=EXACT_DIRTY` from tick 1
onward — real and confirmed, but **ruled out as the cause here**: there is nothing alive to select
as a movement candidate either way, so `EXACT_DIRTY`'s own non-urgent-exclusion mechanism cannot be
what's silencing this specific run. See
`TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION`'s own Related Tickets note — that
ticket's own real-raider evidence is unaffected and still stands on its own; only the *shared-cause
hypothesis* between the two tickets is disproven, not the starvation mechanism itself.

**A real, working entity-spawn pipeline does exist in this codebase** —
`CatalogScenarioStateBuilder`/`ScenarioSetupResolver`/`WorldEntitySpawner`
(`src/scenarios/catalog_state_builder.py`, `src/scenarios/resolver.py`) reads a scenario's
`world_composition`+`perspective` and produces real `AuthoritativeState(entities=...)` via a
tested pipeline (`WorldAssemblyResolver.assemble()` → `WorldEntitySpawner.spawn_from_context()`).
The comment above `_build_initial_state()`'s empty-branch return
(`"the scenario's setup_tags and world_composition govern spawn placement"`) is not purely
aspirational — that mechanism is real. But **it is wired into no live production entrypoint at
all**, Campaign or otherwise: `CampaignOrchestrator` never calls it (uses only
`WorldCompiler.compile()` for regions/places); `V2EngineManager` (the live, non-Campaign API path)
also doesn't use it — it manually spawns a hero + goblins via `EntityGenerator` instead.
`CatalogScenarioStateBuilder` is referenced only by test files
(`tests/unit/certification/test_catalog_scenario_state_builder.py`,
`tests/integration/certification/test_catalog_vs_legacy_scenario_semantics.py`,
`tests/integration/certification/test_catalog_arena_smoke.py`) — the same "real, tested, but
completely unwired" pattern already found for `BiologicalSystem.update()` in the dirty-set
investigation. A third, "legacy" `build_scenario_state()`/`ArenaInjector` path
(`src/certification/scenarios.py`) also exists, certification/arena-specific. **The fix decision is
therefore not "wire Campaign to the existing live spawn mechanism" — there isn't one; it is a real
choice between at least 3 candidate approaches** (wire `CatalogScenarioStateBuilder` in; build a
Campaign-specific minimal spawn similar to `V2EngineManager`'s own manual approach; or something
else), each with a different blast radius. Per peer review, this is being routed to the user for a
scoped decision before any implementation — not decided in this ticket yet.

**Citation blast-radius check (peer-requested, per the base-rate concern that
`TCK-20260824-GRIEF-NEMESIS-REACHABILITY` created this profile specifically to test grief/nemesis
reachability, and an entity-free simulation cannot produce a death event)**: grepped
`tickets/done/*.md` and `tickets/working_log.csv` for `campaign_life_arc`. 4 done tickets cite it:
- `TCK-20260824-GRIEF-NEMESIS-REACHABILITY` — the profile's origin ticket. Its "reachable" claim
  decomposes into two parts: (1) `CampaignOrchestrator.run_episode()` is reachable from a real
  production entrypoint — confirmed by `tests/integration/tools/test_calibrate_simq_campaign_mode.py`,
  a pure wiring test, unaffected by the entity-count finding; (2) `grief_urgency_triggered`/
  `nemesis_relation_formed` events "are emitted from... paths" — verified only via
  `tests/simulation_quality/test_social_scorer.py`'s `TestGriefNemesis` class, which constructs a
  **synthetic** event envelope directly (`scorer.score(_env("grief_urgency_triggered"), _ctx())`),
  never runs a real campaign episode. **No test anywhere in that ticket confirms a real
  `campaign_life_arc` run ever actually produced a grief/nemesis event from genuine entity death —
  and per this finding, it structurally cannot, since no entity has ever died in one.** The ticket's
  own Completion Summary phrasing reads more confident than what was actually verified. Worth a
  closer look, not asserted as false — the underlying emission code paths may still be independently
  correct (verified via their own non-campaign_life_arc unit tests, not audited here).
- `TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY` — passing reference only (regions/places carry-forward
  context, not an entity/reachability claim). Clean, no invalidated claim.
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` — its own test file
  (`tests/integration/culture/test_loyalty_drift_campaign.py`) explicitly states in its own docstring
  that "a multi-episode `campaign_life_arc.yaml` engine run is out of scope for a fast [test]" and
  instead only confirms the profile file exists, building `region_cultures` synthetically via
  `ChronicleGrouper`/`CultureDriftExporter`. Already self-aware of the limitation. Clean, no
  invalidated claim.
- `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT` — this session's own ticket. Its
  post-closure addendum already narrowed its own claim to "no inference about subsystem
  reachability can be drawn... in either direction" (corrected after an earlier peer-review round).
  Fully consistent with, and now explained by, this finding — strengthens rather than invalidates
  the existing correction. No further update needed there.

**Net: 1 of 4 citing tickets (`GRIEF-NEMESIS-REACHABILITY`) has a claim worth a closer look; the
other 3 are clean.** Not reopened — reporting only, per peer instruction, pending the user's own
scoping decision on the actual spawn fix.

Also found and flagged separately, not chased here: `governor_mode=DEGRADED`/`scan_policy=
EXACT_DIRTY` from tick 1 of an essentially empty, trivial-compute kernel is itself suspicious — not
organic load. Filed as its own P3 disposition ticket:
`TCK-20260908-GOVERNOR-DEGRADED-AT-TICK-ONE-EMPTY-WORLD-DISPOSITION`.

## Test Summary
Closed by verification, not new implementation in this ticket itself (the real fix landed in
`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`). Re-verified independently here, 2026-09-11:
- `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` — 4/4 passing, re-run directly
  (not just trusted from the fix ticket's own record).
- A fresh, real, uninstrumented 200-tick `campaign_life_arc` probe (`CampaignOrchestrator` →
  `ScenarioRuntimeService`, real `Kernel` ticks, no monkeypatching): `ScenarioObjectiveState.
  OBJECTIVE_MET` at tick 200, `stall_counter=0` throughout, 0/198 zero-event ticks, 1542 total
  events across 18 real event types. `war_declared`/`military_conflict_resolved`/
  `territory_ownership_changed`/`calamity_spawned` all 0 in this run — a real, honest answer to
  this ticket's last open AC, not further chased (out of scope; these are conditional/probabilistic
  subsystems, one non-firing run is not evidence of a defect).

## Files Changed
None directly by this ticket (verification/closure only). The real fix's files are recorded in
`TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own Files Changed section.

## Completion Summary
Root cause (zero entities spawned for any `campaign_life_arc` episode) was determined by this
ticket and fixed by `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`. Closed here after
independent re-verification (2026-09-11, `TCK-20260909-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`
Batch A triage, per `rpg-feature-planning`): a real 200-tick episode now runs its full configured
length with continuous genuine activity (0/198 zero-event ticks), the stall detector itself was
never touched, and this ticket's own deferred war/siege/calamity reachability question was revisited
with a real answer (did not fire in this specific run — recorded honestly, not chased further).
