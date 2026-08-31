---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION
artifact_type: investigation
tags: [feature-flags, world]
---

# Investigation — TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION

## Method
`mcp__knowledge-search__search_docs` returned `{"error": "index not found"}` for
`"ENABLE_WORLD_EMERGENCE flag validation world emergence phase"` this session — the same
pre-existing environment gap the orchestrator had already confirmed (the fallback,
`python3 tools/knowledge_search.py query ... --top-k 5`, also reported "knowledge index not
found — run make knowledge-index" per the orchestrator's own prior check). Both semantic-search
tools were genuinely unavailable for this ticket, not skipped. `graphify query
"ENABLE_WORLD_EMERGENCE WorldEmergencePhase"` DID return real, useful nodes (`WorldEmergencePhase`,
its 6 collaborator services, its schema types, and 8 real test files under
`tests/unit/domains/world_emergence/` plus `tests/integration/`) — this ran first, before any
grep, satisfying the Context Scan order despite the MCP/fallback outage. Grep/read followed as the
sanctioned fallback once semantic tools were confirmed down, per CLAUDE.md's own explicit
design ("grep/read as follow-up once semantic tools are confirmed unavailable, not skipped
pre-emptively" — same posture the two sibling trial investigations already took). Read in full:
the ticket; `src/domains/world_emergence/phase.py`; `src/engine/pipeline.py` (the `run_phase()`
machinery and the `world_emergence` call site, lines 102-135 and 307-312);
`src/domains/optimization/feature_flags.py`; `src/domains/optimization/degradation.py`;
`src/engine/phase_graph.py` (`PhaseDependencyGraph`); `src/engine/apply.py`'s `quest_registry_add`
wiring; `src/observability/event_extractor.py` (lines 1580-1634) and
`src/observability/event_shapers.py` (lines 1260-1300); `tools/calibrate_simq.py`'s flag-override
and world-loading plumbing; `config/simulation_quality/corpus_registry.yaml` (full file, all 24
worlds' `active_feature_flags`); `docs/architecture/rollout_flag_decisions_m1.md`;
`docs/guidelines/intentional_divergences.md` (DEV-002, DEV-003, full-file grep for `world_emergence`
mentions); `docs/engine/known_limitations.md` §1.5; `docs/parity_ledger/world_dynamics.yaml` (all
`world_emergence`-referencing entries) plus a cross-file grep of `docs/parity_ledger/*.yaml`; the
two sibling stored artifacts in full
(`stored_artifacts/TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION/{investigation,test_plan}.md`,
`stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/investigation.md` referenced
via `rollout_flag_decisions_m1.md`'s own summary of it); every real (non-`__pycache__`) test file
under `tests/**/world_emergence/**` plus `tests/integration/scenarios/test_resource_depletion.py`,
`tests/architecture/test_adventure_routing_flag_inert.py`, and
`tests/integration/test_scenario_feature_flag_defaults.py`.

## Current Behavior

### `WorldEmergencePhase.execute()` (`src/domains/world_emergence/phase.py:21-135`)
A static method: `execute(state, update, recent_events) -> tuple[StateUpdate, WorldEmergenceResult]`.
Pipeline: aggregates `recent_events` into a 100-tick window (`aggregators.py`), evaluates
`RegionalPressureModel` (incl. cross-region propagation, E21E), `ScarcityModel`,
`WorldOpportunityPressureService`, `DynamicQuestSeedService`, a typed
`QuestOpportunityGenerator` pass over `recent_events` for `RESOURCE_DEPLETED`/`ENTITY_DEATH`/
`CAMP_RAID` categories (lines 61-74), `QuestLifecycleService.tick()` expiry, `RumorSeedService`,
and `ServiceStatePressureModel`. It then bridges local signals onto alive/active entities'
`property_updates` (`exposed_world_signals`, and `force_route_reevaluation` when a
`danger_pressure` exposure exceeds intensity `0.2`, lines 97-118) and finally returns
`replace(update, entity_updates=new_entity_updates, world_updates=new_world_updates,
metric_counters=metric_counters, quest_registry_add=list(quest_opps))` (lines 129-135).

**Merge-safety confirmed structurally different from the TCK-20260809 bug class.** Unlike
`CombatEngagementPhase.apply()` (which built a brand-new, standalone `StateUpdate()` with zero
awareness of the incoming accumulated update, requiring the `u.merge(...)` fix at
`pipeline.py:276`), `WorldEmergencePhase.execute()` calls `dataclasses.replace()` **on the
incoming `update` parameter itself** — every field not explicitly named in the `replace()` call
(including `world_events_add`, `faction_updates`, `dirty_set`, everything produced by every
earlier phase this same tick) is carried forward by construction, not silently discarded. The
pipeline's own call site (`pipeline.py:311`) is
`lambda u: WorldEmergencePhase.execute(state, u, recent_world_events)[0]` — no `u.merge(...)`
wrapper is used or needed, since `execute()` already folds `u` (renamed `update` inside the
function) into its own return value. This is confirmed by static read of the `replace()` call
signature, not yet by an empirical no-suppression corpus run (that run is Implement's job, not
Investigate's — see Corpus Trial candidates below).

### A second, independent gate inside `execute()` itself (lines 34-39)
```python
flag = getattr(state, "world_emergence_enabled", True)
if hasattr(state, "periodic_due_ticks") and "world_emergence_disabled" in state.periodic_due_ticks:
    flag = False
if not flag:
    return update, WorldEmergenceResult()
```
This is **separate from, and in addition to**, `run_phase()`'s own
`ff_manager.get_flag_mode("ENABLE_WORLD_EMERGENCE")` gating at the pipeline call site — two
independent OFF switches guard the same phase. A grep of all of `src/` for
`world_emergence_enabled`/`world_emergence_disabled` finds exactly one production-adjacent
reference: the string literal is written into `AuthoritativeState.periodic_due_ticks` by exactly
one test, `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py:11`.
No real content author, world compiler, or production code path anywhere in `src/` ever sets
`state.world_emergence_enabled=False` or adds `"world_emergence_disabled"` to
`periodic_due_ticks` — this second gate is **vestigial for production purposes today**: it exists,
is exercised by exactly one unit test, and cannot fire in any real corpus run because nothing
real ever sets it. Its default (`getattr(..., True)`) means it is silently permissive whenever the
pipeline-level `ENABLE_WORLD_EMERGENCE` flag is `ON` — it never fights that flag in practice, it
just never gets exercised. Not fixed or removed here (out of this ticket's scope — this is a
disclosure, not a defect requiring action); flagged as a Risk below since a future content author
could accidentally collide with the string `"world_emergence_disabled"` in `periodic_due_ticks`
for an unrelated purpose and unknowingly disable this phase.

### Cadence: `world_emergence` runs every eligible tick when ON (`src/engine/phase_graph.py:69`)
`PhaseDependencyGraph`'s metadata table registers `"world_emergence": PhaseMetadata("world_emergence",
{"all"}, {"all"}, must_run_every_tick=True)`. This rules out the false-negative risk the
`ENABLE_COMBAT_ENGAGEMENT` sibling trial had to explicitly guard against (a low
`PhaseDependencyGraph.should_run_phase()` accept-rate silently starving the phase even when the
flag is ON) — `world_emergence` is pinned to run every tick once the flag is `ON`, so
`metric_counters["run_world_emergence"]`/`["skip_world_emergence"]` should show ~100% run-rate in
any real trial; a trial that does *not* show this would itself be a new finding worth flagging.

### Graceful degradation drops `world_emergence` first under load (`src/domains/optimization/degradation.py:58-65`)
`DegradationController.should_skip_phase()` special-cases `"ENABLE_WORLD_EMERGENCE"` (alongside
`ENABLE_LIFE_ARC_CAMPAIGNS`, and `ENABLE_COOPERATION` at `CRITICAL` only) as a phase dropped first
under `DEGRADED`/`CRITICAL` time pressure — an intentional, already-existing graceful-degradation
interaction, not something this ticket investigates further per the orchestrator's own framing
("worth noting, not investigating deeply"). Whether `should_skip_phase()`'s return value is
actually consumed anywhere in `pipeline.py`'s `run_phase()` was not traced further (out of scope);
noted here only as a plausible confound if a real trial's tick-budget pressure rises during a long
run (as it did for `ENABLE_COMBAT_ENGAGEMENT`'s sibling trial).

### `FeatureFlagManager` registration (`src/domains/optimization/feature_flags.py:53-57`)
`ENABLE_WORLD_EMERGENCE` defaults `FeatureMode.OFF`, with an inline comment already citing this
exact ticket as the deferred follow-up ("real call site (world_emergence phase) and 3 test files,
but no corpus profile turns this on and no SHADOW-validation history exists"). The "3 test files"
figure in both the flag's own comment and this ticket's Request Summary **undercounts the real
test surface** — see Test Plan's Regression Surface for the reconciled count (14 real,
non-`__pycache__` files directly under `world_emergence`'s own test directories, plus 2 more
`phase8`-named files elsewhere whose relevance is assessed there).

### `tools/calibrate_simq.py` env-var override mechanism (lines ~244-283)
`ENABLE_WORLD_EMERGENCE` is already in `_KNOWN_FLAGS` (line ~250) — profile-YAML `feature_flags:`
block applied first, then a real `os.environ.get(flag, "")` read that can override it, both paths
writing into `state.feature_flags` which `pipeline.py`'s `refine()` applies onto the
`FeatureFlagManager`. `ENABLE_WORLD_EMERGENCE=ON python3 tools/calibrate_simq.py ...` is therefore
a real, already-supported way to force the flag on for a trial run without touching code — same
mechanism the two sibling tickets used. `_load_world_state()` (lines 143-157) raises
`FileNotFoundError` for any `--name` that fails to resolve against
`data/worlds/{name}/resolved/world.resolved.yaml`, except the literal `"generic"` (falls back to
the synthetic hero+goblins scenario) — so a mistyped/nonexistent `--name` cannot silently produce
a misleading "successful" trial.

### No shipped corpus profile turns `ENABLE_WORLD_EMERGENCE` on
Read `config/simulation_quality/corpus_registry.yaml` in full (24 worlds, every `run_key`'s
`active_feature_flags` block). `ENABLE_WORLD_EMERGENCE` appears in **zero** of them. The only
flags any shipped profile turns on are `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_SOCIAL_COOPERATION`,
`ENABLE_ADVENTURE_ROUTING`, `ENABLE_GUILD_QUEST_GENERATION`,
`ENABLE_INFORMATION_INTENT_EXECUTION`, and `ENABLE_SELF_MODEL_COGNITION` (the last two only on the
two dedicated self-model probe profiles). This directly confirms the ticket's own Request Summary
("no corpus profile turns it on") and matches the "no production evidence" class the deferred-OFF
verdict in `rollout_flag_decisions_m1.md` already recorded.

### `world_emergence_event` is NOT produced by `WorldEmergencePhase` — a red herring resolved
Both candidate observability paths were read directly:
- `src/observability/event_extractor.py:1612-1633` — the `world_emergence_event` construct
  iterates `getattr(update, "world_events_add", None)`, one event per entry, gated only by
  `_push_shapers_phase2_active` (i.e. `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, unrelated to this
  ticket's flag).
- `src/observability/event_shapers.py:1275-1288` — the live, default-ON push-shaper path
  (`WorldDynamicsShaper`) does the identical thing: iterates `update.world_events_add`, one
  `world_emergence_event` per `WorldEvent` entry, no flag check specific to `ENABLE_WORLD_EMERGENCE`
  at all.

`WorldEmergencePhase.execute()`'s own `replace(...)` call (lines 129-135, quoted above) **never
sets `world_events_add`** — it only touches `entity_updates`, `world_updates`, `metric_counters`,
and `quest_registry_add`. `world_events_add` entries that eventually surface as
`world_emergence_event` are populated by *other* pipeline phases entirely
(`diplomatic_transitions`, `military_conflict`, faction/sovereignty systems — see
`pipeline.py:236-244` for one concrete producer) and are *consumed as input* by
`WorldEmergencePhase` via its own `recent_events`/`recent_world_events` parameter, one tick later
(the same one-tick-lag pattern `pipeline.py:140-144`'s own comment documents for
`recent_world_events` generally). **Conclusion: `world_emergence_event` counts in
`simulation_events.jsonl` are unconditionally identical whether `ENABLE_WORLD_EMERGENCE` is ON or
OFF** — they are produced by systems this flag does not gate. Any future trial must not use
`world_emergence_event` as ON/OFF evidence for this flag; the real signals are
`metric_counters["run_world_emergence"]`/`["skip_world_emergence"]`,
`metric_counters["world_emergence_ms"]`/`["aggregates_generated"]`, `state.quest_registry` growth
(via `quest_registry_add`, merged durably at `src/engine/apply.py:326-329`), and the
`exposed_world_signals`/`force_route_reevaluation` entity `property_updates` — none of which are
logged to `simulation_events.jsonl` directly, all of which require inspecting
`metric_counters`/final state/chunk snapshots instead of grepping the events file.

### `ENABLE_WORLD_CAPABILITY_LAYER` combination — resolved, static analysis only, zero live gating call site
`grep -rn "ENABLE_WORLD_CAPABILITY_LAYER" src/ tools/ tests/ config/ docs/` returns exactly 4 real
hits: its own registration (`feature_flags.py:14`, default OFF), a test-scaffold
`pressure_signals` dict entry inside `src/testing/scenario_runner.py:101` (a simulated-tick test
helper — setting `pressure_signals["ENABLE_WORLD_CAPABILITY_LAYER"] = 1.0` only maps to a
`FeatureMode.ON` inside `FeatureFlagManager` if some phase actually names this flag in a
`run_phase(..., feature_flag=...)` call, which none does), `tools/calibrate_simq.py`'s
`_KNOWN_FLAGS` allowlist (a known-flag list, not a gating site), and
`tests/integration/test_scenario_feature_flag_defaults.py`'s own default-OFF allowlist entry. A
separate grep for a `WorldCapabilityLayer` class/module anywhere in `src/` returns **zero
matches** — no such phase or service exists in the codebase at all. This is a stronger inertness
finding than the sibling `ENABLE_ADVENTURE_ROUTING` case (which used to gate a real, now-deleted
phase): `ENABLE_WORLD_CAPABILITY_LAYER` appears to have **never** had a live gating call site.
Combining it `ON` with `ENABLE_WORLD_EMERGENCE=ON` is structurally impossible to produce any
interaction — there is no runtime path for its value to reach any code, let alone code that
touches `WorldEmergencePhase`'s state. No empirical combination trial is warranted; a static
regression guard mirroring `tests/architecture/test_adventure_routing_flag_inert.py` is
recommended (see Test Plan).

### Real test-file count reconciled (ticket claims "3 test files")
`find tests -iname "*world_emergence*" -o -iname "*phase8*"`, filtered to real files (no
`__pycache__`), returns:
- `tests/perf/test_phase8_world_emergence_budget.py`
- `tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py`
- `tests/integration/scenarios/test_phase8_world_emergence_scenarios.py`
- `tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py`
- `tests/unit/domains/world_emergence/test_phase8_world_emergence_events.py`
- `tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py`
- `tests/unit/domains/world_emergence/test_phase8_trauma_concern_bridge.py`
- `tests/unit/domains/world_emergence/test_phase8_service_state_pressure.py`
- `tests/unit/domains/world_emergence/test_phase8_world_to_entity_signal_bridge.py`
- `tests/unit/domains/world_emergence/test_phase8_rumor_seed_service.py`
- `tests/unit/domains/world_emergence/test_phase8_scarcity_model.py`
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`
- `tests/unit/domains/world_emergence/test_phase8_dynamic_quest_seed_service.py`
- `tests/unit/domains/world_emergence/test_phase8_world_opportunity_pressure.py`

That is **14 real test files**, not 3 — `feature_flags.py`'s own inline comment and this ticket's
Request Summary both undercount the real coverage. (Two further `phase8`-named files,
`tests/unit/progression/test_phase8_progression.py` and
`tests/unit/observability/test_phase8_m46_m47_m48.py`, were not confirmed to reference
`world_emergence` specifically and are treated as out of this domain's regression surface unless
Test Plan's own check finds otherwise.) Additionally, `tests/integration/scenarios/
test_resource_depletion.py` calls `WorldEmergencePhase.execute()` directly (bypassing the pipeline
and the `ENABLE_WORLD_EMERGENCE` flag entirely, confirmed via `grep` — no `ENABLE_WORLD_EMERGENCE`
reference in that file) to assert `RegionalPressureModel`/`ScarcityModel` non-zero output over a
1000-tick window — real, substantive coverage of the domain's core logic, but not evidence that
the flag itself is wired correctly end-to-end through the pipeline, which is exactly this ticket's
gap.

## Mechanics / Engine Constraints
- **Kernel 7-phase loop / `refine()`'s Resolution sequencing** (`docs/engine/kernel.md`):
  `world_emergence` sits in the Resolution phase after `world_dynamics`/`town_resolution`/
  `gold_sink` (Phase 5: Governance & Ecology, `pipeline.py:293-305`) and before `quest_rewards`
  (Phase 6: Economy & Evolution, `pipeline.py:314-319`) — i.e. it runs after resource/ecology state
  for the tick has settled and before quest rewards are resolved, consistent with its role of
  consuming settled-tick pressures to seed new quest opportunities rather than reacting mid-tick.
- **Durable State Rule**: `quest_registry_add` (typed `QuestOpportunity` objects) is the only
  durable-state-shaped output `WorldEmergencePhase` produces; it is merged into
  `AuthoritativeState.quest_registry` exclusively through `ApplyPath.apply_generation()`
  (`src/engine/apply.py:326-329`) — already compliant, no local/hidden durable state is created.
  `exposed_world_signals`/`force_route_reevaluation` are typed `EntityUpdate.property_updates`
  entries, also applied only through the authoritative pipeline.
- **Strategic/Tactical Rule**: `WorldEmergencePhase` is explicitly a world-signal-exposure /
  quest-seeding system (strategy-adjacent), not a tactical mutator — it never authoritatively
  changes entity HP/position/inventory, consistent with its scope.

## Docs Requiring Update
- `docs/architecture/rollout_flag_decisions_m1.md`: this ticket is the named follow-up its own
  `ENABLE_WORLD_EMERGENCE` table row cites ("Kept OFF, deferred... Follow-up:
  TCK-20260826-WORLD-EMERGENCE-FLAG-VALIDATION"). Whichever way the real trial resolves, that row
  and a new `## ENABLE_WORLD_EMERGENCE — Validation Trial Result (TCK-20260826)` section (mirroring
  the two existing sibling sections' structure exactly: worlds tested, commands, evidence tally,
  honest-gap disclosure, recommendation) must be added by Implement so the decision artifact stops
  pointing at an open follow-up that has actually been run.

The `docs/guidelines/intentional_divergences.md` doc is **not** listed above with a required-bullet,
matching the sibling `ENABLE_COMBAT_ENGAGEMENT` investigation's own reasoning exactly: whether a new
`DEV-00N` entry is needed depends on the real trial's outcome (flip vs. stay-OFF), which is not
decided by this investigation — per the Uncertainty Rule, "vague leads stay vague until evidence
narrows them." If the trial recommends flipping `ENABLE_WORLD_EMERGENCE` to `ON`, a new entry
mirroring DEV-003's structure is required at Implement time; if it recommends staying OFF (the more
likely outcome given zero shipped profiles turning it on today, matching both sibling flags'
outcome), no new divergence exists to record. `docs/engine/known_limitations.md` §1.5 is similarly
**not** required to change: its "all 11 flags default to `FeatureMode.OFF`" framing already lists
`ENABLE_WORLD_EMERGENCE` correctly and this ticket does not change that default — though it is
worth noting (Risks below) that §1.5's own header claim ("All 11 Phase 10 feature flags... default
to `FeatureMode.OFF`") is itself already stale as written, since `ENABLE_BELIEF_ASSIMILATION` and
`ENABLE_SOCIAL_COOPERATION` were flipped ON by the prior `TCK-20260824-ROLLOUT-FLAG-DECISIONS`
ticket and that doc's own bullet list still shows them — a pre-existing staleness this ticket did
not introduce and is not in scope to fix (path: `docs/engine/known_limitations.md`, under `docs/`).

## Parity Ledger Overlap
`docs/parity_ledger/world_dynamics.yaml` carries 7 entries whose `v2_evidence`/`text` reference
`world_emergence` code directly, all `status: verified`, all `priority: P1` (none `P0`, so none
carry a hard "must have a passing `test_path`" gate under the Authoritative Mechanics Rule, though
all already have real, existing `test_path`s that were confirmed to exist on disk):
- `WORLD-098` — resource-crisis quest generation on depletion (`QuestOpportunityGenerator.from_resource_depleted`), `test_path: tests/unit/quest/test_quest_generation.py::test_resource_crisis_quest_generated_on_depletion`
- `WORLD-099` — quest generation determinism, `test_path: tests/unit/quest/test_quest_generation.py::test_quest_generation_determinism`
- `WORLD-101` — quest expiry lifecycle (`QuestLifecycleService.tick`), `test_path: tests/unit/quest/test_quest_lifecycle.py::test_quest_expires_after_expiry_ticks`
- `WORLD-102` — `QuestOpportunity` objects reach `quest_registry` via `execute()`'s
  `quest_registry_add`, `test_path: tests/unit/domains/world_emergence/test_quest_registry_wiring.py::test_world_emergence_populates_quest_registry`
- `WORLD-104` — cross-region scarcity propagation (E21E, `RegionalPressureModel.propagate_cross_region`), `test_path: tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py::test_propagate_cross_region_adjacent_regions_receive_spread`
- `WORLD-106` — trauma→concern bridge (`TraumaRegionConcernBridge`), `test_path: tests/unit/domains/world_emergence/test_phase8_trauma_concern_bridge.py::test_concern_appears_within_one_tick_of_threshold_crossing`
- `WORLD-107` — sovereignty-shift events observable in `WorldEmergencePhase.execute()`, `test_path: tests/unit/world/test_sovereignty_events.py::test_sovereignty_shift_event_emitted_on_hero_takeover`

Also `WORLD-115` (`world_emergence_event`/`narrative_milestone` push-shaper reuse, `status:
verified`, `priority: P1`, `test_path: tests/unit/observability/test_event_shapers_world_dynamics.py`
— 25 tests) documents the same `world_events_add`-iteration mechanism this investigation traced
above; it is unaffected by this ticket (it's about the push-shaper pipeline, not
`ENABLE_WORLD_EMERGENCE`'s own gating).

**None of these 8 entries are expected to need a status/evidence change from this ticket** — this
ticket does not modify `WorldEmergencePhase`'s logic, only produces trial evidence about the
pipeline-level flag gating it. If the real trial surfaces a genuine new defect in any of these
mechanisms (not expected, but not ruled out), Implement must update the relevant entry then, not
assumed here.

## Prior Work
- **TCK-20260824-ROLLOUT-FLAG-DECISIONS** (DONE): reviewed 8 Phase-10 flags, deferred
  `ENABLE_WORLD_EMERGENCE` (kept OFF) with the thinnest rationale of the group — "No production
  evidence" — and named this ticket as the follow-up. Established the decision-artifact format
  (`docs/architecture/rollout_flag_decisions_m1.md`) and the two legitimate decision classes ("Flip
  ON" requires real standing production evidence; "Keep OFF, deferred" requires a named follow-up)
  this ticket's own eventual recommendation must fit.
- **TCK-20260826-COMBAT-ENGAGEMENT-FLAG-VALIDATION** (DONE): closest-shaped sibling — same tier,
  same "produce real trial evidence, don't flip" job. Its `dungeon_crawl`/`wilderness_survival`,
  seed 42, 2000-tick, OFF-then-ON A/B method is the template this ticket's own Corpus Trial
  candidates below follow. Its key process lesson: capture
  `metric_counters["run_<phase>"]`/`["skip_<phase>"]` alongside raw event counts, not raw counts
  alone, to rule out phase-starvation false negatives (a smaller risk here per the
  `must_run_every_tick=True` finding above, but the same capture discipline should still apply).
- **TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION** (DONE): closest-shaped sibling for the
  `ENABLE_<OTHER_FLAG>` combination-check methodology — resolved
  `ENABLE_ADVENTURE_ROUTING`'s combination question via pure static analysis (zero live gating call
  site) plus a dedicated architecture-guard regression test
  (`tests/architecture/test_adventure_routing_flag_inert.py`), explicitly declining an empirical
  trial since "a trial cannot produce a different answer than the static analysis already gives."
  This ticket's own `ENABLE_WORLD_CAPABILITY_LAYER` finding above follows the identical reasoning
  and the identical recommended regression-guard shape.
- **DEV-002/DEV-003** (`docs/guidelines/intentional_divergences.md`): DEV-002 is the blanket
  Phase-10 default-OFF policy (all 10 original flags, `tools/balance_measure.py` re-run as its
  literal unblock condition). DEV-003 established that standing real SimQ-corpus-profile usage in a
  flag's own domain can satisfy DEV-002's underlying intent without literally re-running
  `balance_measure.py`. `ENABLE_WORLD_EMERGENCE` has **no** standing corpus-profile usage at all
  (unlike the two DEV-003-flipped flags), so this ticket's trial — if it runs one — would be
  establishing fresh evidence, not invoking the DEV-003 substitution precedent directly.

## Risks and Open Questions
- **Open question (not resolved by this investigation, Implement's job):** whether a single
  ON/OFF corpus trial confirming no-suppression and real quest-registry/metric-counter activity is
  itself sufficient standing evidence to recommend a flip, or whether — per both sibling
  precedents' own outcome — "keep OFF, deferred, but now with a real trial on file" remains the
  honest recommendation until a shipped profile actually turns the flag on in production. Given
  zero shipped profiles use `ENABLE_WORLD_EMERGENCE` today (stronger absence than either sibling
  flag, both of which had *some* prior real-world evidence — `unit_selfmodel_pilot` for self-model,
  the TCK-20260809 fix history for combat-engagement), a "keep OFF, deferred" outcome is the more
  likely honest read, but this is explicitly Implement's call to make with real evidence in hand,
  not pre-decided here.
- **Risk**: the vestigial `state.world_emergence_enabled`/`periodic_due_ticks` in-function gate
  (see Current Behavior above) is dead in production today, but a future content author or test
  fixture could accidentally collide with the exact string `"world_emergence_disabled"` in
  `periodic_due_ticks` for an unrelated purpose (e.g. a generically-named "disable this system"
  marker) and silently disable `WorldEmergencePhase` without touching the real
  `ENABLE_WORLD_EMERGENCE` flag at all. Not a defect to fix in this ticket (no real path exercises
  it today), but worth disclosing as a latent footgun.
- **Risk**: which world(s) to trial on is not pre-decided here per the Uncertainty Rule
  ("vague leads stay vague until evidence narrows them") — `WorldEmergencePhase`'s real
  signal-producing paths need `RESOURCE_DEPLETED`/`ENTITY_DEATH`/`CAMP_RAID` `WorldEvent`s in
  `recent_world_events` to produce nonzero `quest_registry_add`/pressure output; a world with thin
  resource-depletion/death/raid activity in its OFF baseline would produce a weak "ON == OFF, both
  near-zero" result, the same near-zero-baseline caveat both sibling trials disclosed. Candidate
  worlds with the domain's real event-producing content:
  `dungeon_crawl`/`wilderness_survival` (both already used by the `ENABLE_COMBAT_ENGAGEMENT`
  sibling, `monster_only_gauntlet` archetype — likely to produce real `ENTITY_DEATH`/`CAMP_RAID`
  events from real combat) and `resource_dense_basin` (highest `resource_density` of any shipped
  world at `2.3333`, `resource_node_count: 7` — likely to produce real `RESOURCE_DEPLETED` events
  over a long run) or `tests/integration/scenarios/test_resource_depletion.py`'s own synthetic
  1000-tick depletion window as a lower-bar sanity reference (not a substitute for a real corpus
  world). Implement should pick based on which world's own real content actually exercises this
  domain, following the same "pick based on the domain's own event-producing paths, not
  convenience" instruction the orchestrator gave, and disclose the actual OFF-baseline counts
  rather than assume them.
- **Risk**: `tools/calibrate_simq.py`'s `_KNOWN_FLAGS` allowlist and `FeatureFlagManager`'s own
  dict are two independently-maintained lists of the same flag set (same class of
  three-independently-synchronized-copies smell `rollout_flag_decisions_m1.md`'s own "A Real
  Correction Made During Implementation" section already disclosed for
  `_DELIBERATE_ON_DEFAULT_FLAGS`) — not this ticket's job to consolidate, noted for awareness only.

## Anti-Drift Hazards
- **Do not conflate this ticket with fixing or extending `WorldEmergencePhase` itself.** Out of
  Scope excludes flipping the default; it likewise should be read to exclude any new
  gameplay/logic change to the phase's own behavior — the ticket is purely evidence-gathering. If
  a genuine new bug surfaces during a trial, disclose it and hand it off as a separate ticket, not
  fix it inline.
- **Do not use `world_emergence_event` counts in `simulation_events.jsonl` as ON/OFF evidence** —
  confirmed above to be produced by other systems entirely and unconditionally identical between
  legs. Using it anyway would produce a false "no suppression" result that proves nothing about
  this specific flag.
- **Do not treat a clean ON/OFF diff on a near-zero-baseline world as sufficient "real activity"
  evidence** without also reporting the absolute `quest_registry_add`/`metric_counters` volume in
  the OFF-vs-ON legs (same caveat both sibling trials already disclosed for their own domains).
- **Do not run an empirical `ENABLE_WORLD_CAPABILITY_LAYER` combination trial** — the static
  zero-live-gating-call-site finding above already resolves the naming-proximity check the ticket's
  Scope asked for; running a trial anyway would not produce a different answer and would be
  scope-inflation beyond what the orchestrator's own instruction called for.
- **Do not silently reuse `data/calibration/`/`data/runs/` output from a different concurrent
  session** — per the Hard Rules on shared-directory concurrency, generate fresh,
  uniquely-tagged output (`--output`/`--name` carrying this ticket's own tag).
- **Clean up `data/runs/*` and any ad hoc calibration output at Finalize**, per the Definition of
  Done — a validation trial produces no permanent code change but still leaves run artifacts that
  must be cleaned.

## Corpus Trial Candidates (for Implement — not run by this investigation)
Per the sibling precedent, Investigate's job is to identify method and candidates; running the
trial and writing `trial_evidence.md` is Implement's job.

**Primary candidate — `dungeon_crawl` (seed 42, 2000 ticks)**: reuses the exact world/seed/tick
count both sibling trials already used, giving a directly comparable baseline and a
`monster_only_gauntlet` archetype likely to produce real `ENTITY_DEATH`/`CAMP_RAID` events from
its purpose-built combat content (`COMBAT: 2.0` pillar weight).
```
python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_world_emergence_OFF
ENABLE_WORLD_EMERGENCE=ON python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000 \
  --output data/calibration/dungeon_crawl_seed42_2000t_world_emergence_ON
```

**Secondary candidate — `resource_dense_basin` (seed 42, 200 ticks; no dedicated scoring profile,
so `--profile default` applies)**: highest `resource_density` (2.3333) and `resource_node_count`
(7) of any shipped world — the strongest candidate for exercising `RESOURCE_DEPLETED`-driven
`ScarcityModel`/quest-seed generation specifically, a signal `dungeon_crawl` (low resource density)
is less likely to exercise strongly. `resource_dense_basin`'s shipped run_keys only go to 200
ticks; Implement should confirm whether a longer synthetic run is warranted or whether 200 ticks
already produces real depletion activity (the domain's own `test_resource_depletion.py` synthetic
test uses 1000 ticks to reliably observe scarcity rise, suggesting 200 real ticks may be thin —
disclose the actual counts rather than assume either way).
```
python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42 --ticks 200 --profile default \
  --output data/calibration/resource_dense_basin_seed42_200t_world_emergence_OFF
ENABLE_WORLD_EMERGENCE=ON python3 tools/calibrate_simq.py --name resource_dense_basin --seed 42 --ticks 200 --profile default \
  --output data/calibration/resource_dense_basin_seed42_200t_world_emergence_ON
```

**What evidence to capture (per world, per ON/OFF pair)**, given `world_emergence_event` is
disqualified as a signal (see Current Behavior above):
1. `metric_counters["run_world_emergence"]`/`["skip_world_emergence"]` — should show ~100%
   run-rate when ON given `must_run_every_tick=True`; a lower rate would itself be a new finding.
2. `metric_counters["world_emergence_ms"]`/`["aggregates_generated"]` — phase's own telemetry,
   confirms real work is happening, not just a no-op pass.
3. Final-state `len(state.quest_registry)` growth (or a chunk/state-snapshot diff) between OFF and
   ON legs — the durable signal `quest_registry_add` produces; requires inspecting final state, not
   `simulation_events.jsonl`.
4. Whether `exposed_world_signals`/`force_route_reevaluation` `property_updates` appear on any
   entity in the ON leg's final state (bridged per-entity, not globally logged either).
5. Absolute (not just relative) activity in the OFF baseline — real `RESOURCE_DEPLETED`/
   `ENTITY_DEATH`/`CAMP_RAID` counts feeding the aggregator, to confirm the trial world isn't
   degenerate/near-empty for this domain specifically.
