---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260824-WIRE-ORPHANED-MECHANISMS
artifact_type: investigation
tags: [social, cognition, progression]
---

# Investigation — TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Context Scan Note

Both mandated Step-0 context-search tools failed with a pre-existing environment gap before any
grep/file-read was performed:
- `mcp__knowledge-search__search_docs` → `{"error":"index not found","action":"run make knowledge-index"}`
- Fallback `python3 tools/knowledge_search.py query ... --top-k 5` → `knowledge index not found — run make knowledge-index`

`graphify query "Wire the Remaining Orphaned Mechanisms InformationNeedDetector EvolutionService SabotageAction"`
succeeded (BFS depth=2, 133 nodes found) and was used to seed the initial file-target list
(`cognition_extras.py`, `src/town/sabotage.py`, `src/engine/domain/lead_routing.py`,
`src/engine/pipeline_phases/lead_contradiction.py`, `src/domains/information/providers.py`) before
any grep was run. Both semantic search failures are logged here per Hard Rule; all findings below
come from graphify + source reads + grep as the mandated follow-up.

## Current Behavior

### 1. InformationNeedDetector → CognitionDomain.execute_brain()

- `InformationNeedDetector.detect_and_generate(entity, tick)` — `src/engine/domain/cognition_extras.py:46-98`.
  Pure static method, scans `entity.self_model.knowledge.unknowns` for candidates
  (`priority > 0.5`, `seeking_project_id is None`), returns an optional `StrategicUpdate`
  creating one `INFORMATION_SEEKING` project. Docstring at file top (lines 15-16) states the
  intended insertion point explicitly: "call `detect_and_generate()` in
  `CognitionDomain.execute_brain()` after existing project evaluation and before route scoring."
- `CognitionDomain.execute_brain()` — `src/engine/domain/cognition.py:26-75`. Current body:
  early-exit checks (lines 40-56) → `AppraisalSystem.evaluate_emotional_state()` (lines 61-67,
  "1. Emotional Appraisal") → `TacticalDecisionSystem.evaluate_entity_intent()` (line 70,
  "2. Tactical Intent") → return. **There is no project-evaluation or route-scoring step inside
  `execute_brain()` itself** — those live in the pipeline-level
  `StrategicIntelligenceSystem.fused_strategic_pass()` (referenced in `CognitionDomain`'s own
  class docstring, lines 16-18, as owning "Strategic Planning (Authoritative)" exclusively) and in
  `LeadRoutingSystem` (`src/engine/domain/lead_routing.py`). The docstring's insertion point
  ("after project eval, before route scoring") therefore does not literally exist inside
  `execute_brain()` as currently written — this is a Risk flagged below, not silently resolved.
- Caller check: `grep -rn "InformationNeedDetector" src/` returns only its own definition
  (`cognition_extras.py:36,68`) and one comment reference in
  `src/engine/pipeline_phases/lead_contradiction.py:13` ("InformationNeedDetector fires an
  INFORMATION_SEEKING project next tick" — a comment describing intended future behavior, not a
  call). Zero real callers.
- Parity ledger `STRAT-229` (`docs/parity_ledger/strategic_cognition.yaml:2588-2602`) is marked
  `status: verified` with `test_path:
  tests/unit/cognition/test_information_seeking.py::TestInformationNeedDetectorNormalFlow::test_unknown_fact_generates_seeking_project`
  — this verifies `detect_and_generate()` in isolation, not that it fires from a real
  `CognitionDomain.execute_brain()` / Kernel run, which is exactly what this ticket's AC #1 demands
  ("verified via a real Kernel run").

### 2. EvolutionService vs. EvolutionSystem — Duplicate-Check A

- `EvolutionService` — `src/progression/evolution.py` (30 lines total). Static-only class:
  `check_evolution(kind, level)` looks up `EVOLUTION_MAP = {"goblin_0": {"target": "goblin_1",
  "required_level": 10}, "goblin_1": {"target": "goblin_2", "required_level": 20}}`;
  `get_evolution_gear(new_kind)` returns hardcoded gear dicts for `"goblin_1"`/`"goblin_2"`.
- `EvolutionSystem` — `src/engine/evolution.py`. `evaluate(state, update)` (lines 20-154) is
  wired into the authoritative pipeline: `src/engine/pipeline.py:23` imports it,
  `src/engine/pipeline.py:337` runs it as phase `"evolution"`
  (`run_phase("evolution", update, lambda u: EvolutionSystem.evaluate(state, u))`). Its
  `_get_evolved_kind()` helper (lines 156-169) evolves any `"<name>_<digit>"` kind string by
  incrementing the trailing digit (`"goblin_0"` → `"goblin_1"`) when a level-up crosses one of
  `[10, 25, 50]` (line 93).
- **Caller grep**: `grep -rn "EvolutionSystem" src/` → only its own file and the two pipeline.py
  references above. `grep -rn "EvolutionService" src/` → only its own file (definition +
  self-reference on line 17). `grep -rln "EvolutionService" tests/` → **zero results**.
  `EvolutionService` has no callers anywhere, including its own tests — it has no tests at all.
- **Direct proof of duplicate mechanism**: `tests/unit/progression/test_evolution.py::test_goblin_evolution`
  builds an entity with `kind="goblin_0"`, drives it to level 10 via `EvolutionSystem.evaluate()`,
  and asserts `new_entity.kind == "goblin_1"` with gear `{MAIN_HAND: "iron_sword", TORSO:
  "leather_armor"}` (test lines 96-103). This is the exact `"goblin_0"→"goblin_1"` transition and
  exact gear set that `EvolutionService.EVOLUTION_MAP`/`get_evolution_gear()` also encode — proving
  both classes target the identical named mechanism. The two disagree on the second-stage
  threshold: `EvolutionSystem` uses level 25 (`for threshold in [10, 25, 50]`) for the next kind
  step, while `EvolutionService.EVOLUTION_MAP["goblin_1"]["required_level"]` is 20 — an internal
  inconsistency that would produce contradictory behavior if both were ever wired simultaneously.
- **Disposition: dead duplicate.** `EvolutionSystem` is the live, pipeline-wired, tested
  implementation of exactly the `goblin_0/1/2` mechanism. `EvolutionService` is untested,
  uncalled, and its thresholds conflict with the live system's. There is no distinct purpose to
  preserve — recommend fold/delete, not wire as a second call site. Deleting
  `src/progression/evolution.py` (or reducing it to a thin re-export, if any doc/comment elsewhere
  references the module path) removes the duplicate without touching `EvolutionSystem`.

### 3. SabotageAction vs. BuildingSabotageSystem — Duplicate-Check B

- `SabotageAction` — `src/town/sabotage.py`. `apply(entity, building_id, state)` (lines 11-42):
  validates `building_id` exists and building is functional, checks proximity (`dist < 5.0` from
  entity position to building position via direct Euclidean distance), computes
  `damage = entity.combat.atk`, returns a `StateUpdate` with one `BuildingUpdate(hp_delta=-damage)`.
- `BuildingSabotageSystem` — `src/engine/sabotage.py`. `resolve(state, update)` (lines 18-71):
  scans `update.entity_updates` for entities whose `task_upd.work_kind_set == "SABOTAGE"` (or
  `ENTITY_ACT` with `payload["action"] == "SABOTAGE"`), resolves the target building via
  `SpatialQueryService.get_building_at(state, target_pos)`, applies a **fixed** `damage = 50`
  regardless of attacker stats, and sets `functional_set = (new_hp > 0)`.
- **Caller grep**: `grep -rn "SabotageAction" src/` → only its own file
  (`src/town/sabotage.py:7,11`). `grep -rln "SabotageAction" tests/` →
  `tests/unit/world/test_building_sabotage.py` only (3 unit tests that call `.apply()` directly,
  no pipeline/task-driven path). `grep -rn "BuildingSabotageSystem" src/` → wired at
  `src/engine/pipeline.py:19` (import) and `src/engine/pipeline.py:290`
  (`run_phase("building_sabotage", ...)`), plus a comment reference in
  `src/observability/event_extractor.py:1435`. `grep -rln "BuildingSabotageSystem" tests/` →
  `tests/integration/pipeline/test_strategic_cadence.py`, `tests/integrity/test_logic_guards.py`.
- **Zero production trigger for `SABOTAGE` work_kind found**: `grep -rn "SABOTAGE" src/` outside
  the two sabotage files returns exactly one hit —
  `src/engine/legality.py:138: if action_kind in ["SABOTAGE", "RECRUIT", "THEFT"]:` — a legality
  gate, not an intent generator. No goal scorer, tactical decision system, or quest/opportunity
  system currently emits a `SABOTAGE` task intent, so `BuildingSabotageSystem` itself is wired into
  the pipeline but is also currently unreachable in practice from any AI decision path (a distinct
  gap from this ticket's scope — flagged under Anti-Drift Hazards, not to be fixed here).
- **Disposition: dead duplicate at the class level.** `BuildingSabotageSystem` is the live,
  pipeline-registered, integration-tested implementation of "reduce building HP, disable at 0 HP."
  `SabotageAction` has zero production callers and duplicates the same purpose via a different
  (ATK-scaled, proximity-radius) mechanic. The one genuine behavioral difference —
  `SabotageAction` scales damage with `entity.combat.atk`; `BuildingSabotageSystem` uses a flat 50
  — is not by itself evidence of a distinct *purpose* (both exist purely to "damage/disable a
  building"); it is a design choice that could be folded into `BuildingSabotageSystem` if
  ATK-scaling is wanted, rather than justifying two independently-triggered classes. Recommend
  fold/delete `SabotageAction`, or at minimum do not add it as a second, competing call site
  alongside `BuildingSabotageSystem` — see Anti-Drift Hazards.

#### TCK-20260425-PH7-M4-SABOTAGE historical-closure discrepancy (flagged, not reconciled)

- The closed ticket (`tickets/done/TCK-20260425-PH7-M4-SABOTAGE.md`, DONE, 2026-04-25) Scope/AC
  only claims: "Implement `SabotageAction.apply` for building damage", "Detect building destruction
  in `ApplyPath.apply_generation`", "Propagate `trauma_score` to regions upon building death", and
  lists all 3 acceptance criteria as `[x]` against direct-call unit tests
  (`tests/town/test_building_sabotage.py` — now relocated to
  `tests/unit/world/test_building_sabotage.py`). **It never claims `SabotageAction` was wired into
  any decision/intent pipeline** — the closure is accurate for what it actually delivered
  (a tested `.apply()` function plus `ApplyPath` trauma-propagation integration).
- Its own stored investigation (`stored_artifacts/TCK-20260425-PH7-M4-SABOTAGE/investigation.md`,
  "Requirements" section, line 20) states an aspiration that was never converted into scope/AC:
  *"Strategic Impact: Sabotage should be an authoritative action that can be emitted by 'Raider'
  archetypes."* This aspiration was never fulfilled — no Raider archetype, goal scorer, or task
  generator ever emits a `SabotageAction`-triggering intent, then or now.
  {module docstring: "Phase 8 Implementation") — comes later in the project's numbered phases than
  `SabotageAction`'s Phase 7 M4 label
  (`src/town/sabotage.py` carries no phase header at all; `src/engine/sabotage.py:2` reads
  "# Phase 8 Implementation: Handles Infrastructure Damage and Service Disruption
  (LEG-RPG-001/006)"). This is consistent with `BuildingSabotageSystem` having been built as a
  *later, superseding* implementation reached via task/intent routing, leaving `SabotageAction`
  stranded rather than the historical DONE closure having been wrong at the time it closed.
- **Conclusion (flagged, per Out of Scope — not reconciled further here)**: the DONE closure's own
  claims still hold today (the function works, is unit-tested, and integrates with `ApplyPath`).
  What changed is that a separate, later system (`BuildingSabotageSystem`) became the actual
  production path for the same real-world purpose, without anyone updating or retiring
  `SabotageAction`. Current reality (zero callers) is real and current, not a sign the 2026-04-25
  closure was falsified.

### 4. EmotionUpdateService.update_on_event() — event-emission site

- `EmotionUpdateService.update_on_event(model, event_kind)` — `src/domains/emotion/emotion_service.py:15-51`.
  Pure function, `event_kind` branches on 6 literal strings: `"near_death"`, `"easy_win"`,
  `"repeated_failure"`, `"new_unknown"`, `"successful_goal"`, `"stagnation"`. Returns a new
  `EmotionalModel` via keyword construction (not `dataclasses.replace`, but equivalent effect).
- **Caller grep**: `grep -rn "EmotionUpdateService" src/` → only `emotion_service.py` itself and
  the re-export in `src/domains/emotion/__init__.py:7,13`. Zero callers.
- `AppraisalSystem.evaluate_emotional_state()` (`src/engine/cognition.py:76`) is the unrelated,
  already-wired per-tick tactical appraisal, called from `CognitionDomain.execute_brain()`
  (`src/engine/domain/cognition.py:62`), `src/engine/tactical.py:87`,
  `src/systems/strategic_systems/intelligence.py:967`, and `src/ai/goals/scorers.py:144` — none of
  these call `EmotionUpdateService`.
- **Real candidate event-emission site found**: `NearDeathHardeningPhase.apply()` —
  `src/engine/pipeline_phases/hardening.py:18-95`, run as pipeline phase `"near_death_hardening"`
  (`src/engine/pipeline.py:357`). This phase authoritatively detects the exact "near_death" concept
  (survives a hit with `projected_hp <= 10% of max_hp`, lines 63-74) and already writes a
  `CombatUpdate` consequence (`max_hp_delta=5`, lines 76-85). It is the natural, already-existing
  detection site for the `"near_death"` `event_kind` — distinct from `AppraisalSystem`, which is
  tactical/per-tick, not event-triggered.
- `docs/simulation/domains/emotion_contract.md:40-45` already documents (as design/target state,
  not yet matched by code) that each of the 6 event kinds should route through
  `EmotionUpdateService.update_on_event`, including `near_death` → `EmotionUpdateService` +
  `RecoveryReadinessService.register_near_death`. The doc's language ("Engine event handlers" call
  these) currently overstates reality — no such handler exists yet.
- **Durable-state path**: `entity.cognition.emotion` (`EmotionalModel`, `src/core/cognition.py:218`)
  is part of the durable `CognitionModel` on `EntityState.cognition`
  (`src/core/state.py:690`, serialized in `to_canonical_dict()`). `EntityUpdate` has no per-field
  emotion update type, but it does carry `cognition_bundle_set: Optional[Any]` (whole-`CognitionModel`
  replacement — `src/core/updates.py:655`), which is already applied authoritatively in
  `src/engine/patches.py:665-743` and already has one live production caller:
  `src/domains/memory/phase.py:51` (`replace(entity_up, cognition_bundle_set=new_entity.cognition)`).
  Wiring `EmotionUpdateService` must route through `cognition_bundle_set` (replace
  `entity.cognition` with `entity.cognition` + updated `.emotion` field), not a direct mutation —
  this satisfies the Durable State Rule and has a working precedent to follow.

### 5. ReputationUpdateService.process_witnessed_event() — witnessed-event site

- `ReputationUpdateService.process_witnessed_event(profile, event_kind)` —
  `src/domains/commitment/reputation.py:15-27`. Branches on 3 literal strings:
  `"successful_escort"`, `"betrayal"`, `"clear_camp"`. Returns new `PublicReputationProfile` via
  `dataclasses.replace`.
- **Caller grep**: `grep -rn "ReputationUpdateService" src/` → only its own file and the
  `src/domains/commitment/__init__.py:9,15` re-export. Zero callers.
- **No existing production site fires any of the 3 specific `event_kind` strings it recognizes**:
  - `"successful_escort"` — no `ESCORT` quest kind exists in the live `QuestKind` enum
    (`src/core/models/quests.py:7-12`: `HUNT, GATHER, EXPLORE, LIBERATE, BOUNTY` — no `ESCORT`).
  - `"betrayal"` — the closest live analog is `CooperationLearningService.learn()`
    (`src/domains/cooperation/services.py:329-360`, `out_type == "betrayal"` branch, line 352),
    but `CooperationLearningService` is imported into `CooperationPhase`
    (`src/domains/cooperation/phase.py:18`) and never actually called there
    (`grep -n "CooperationLearningService\." src/domains/cooperation/phase.py` → zero matches) —
    it too is dead code, imported but unused.
  - `"clear_camp"` — no matching quest-kind or event constant exists anywhere in `src/`.
  - A separate, also-orphaned `ReputationService` class exists at
    `src/systems/social_systems/reputation.py:4-29` (`get_impact()`,
    `calculate_caution_modifier()`) with **zero callers anywhere in `src/`** — not part of this
    ticket's 7 mechanisms, but relevant context: this repo currently has *no* live witnessed-event
    → reputation pipeline of any kind.
- **Closest generic analog available**: `QuestResolutionSystem.enforce()`
  (`src/engine/quests.py:154-231`) detects quest completion generically at
  `is_newly_completed = (updated_quest.quest_status == QuestStatus.COMPLETED and
  project.quest_status == QuestStatus.ACTIVE)` (line 195), run from pipeline phase
  `"quest_rewards"` (`src/engine/pipeline.py:319`). This is a real, wired, per-tick detection
  point, but it does not natively distinguish `"successful_escort"` vs. `"clear_camp"` — that would
  require a `quest_kind`-to-`event_kind` mapping that does not exist today (and `ESCORT` does not
  exist as a `QuestKind` at all).
- `docs/simulation/domains/commitment_contract.md:44,84,185,203-205` already documents "Engine
  event handlers — call `ReputationUpdateService.process_witnessed_event()` when a social event is
  witnessed" and specifically references escort/betrayal/camp_clear as the intended event set
  (line 185) — again describing target state that current code does not yet match.
- **Durable-state path**: same as EmotionUpdateService — `entity.cognition.public_reputation`
  (`PublicReputationProfile`, `src/core/cognition.py:529`) is part of durable `CognitionModel`;
  wiring must go through `EntityUpdate.cognition_bundle_set`, following the
  `src/domains/memory/phase.py:51` precedent.
- **This is the most under-specified of the 7 mechanisms**: unlike the other 6, none of its 3
  recognized `event_kind` strings has a real, already-detected production event to attach to
  without also inventing a new quest kind (`ESCORT`) or wiring the currently-dead
  `CooperationLearningService.learn()` betrayal branch first. Flagged as an open question below —
  do not assume an answer.

### 6. compute_elder_attribute_update() — aging-cycle tick call site

- `compute_elder_attribute_update(entity_id, attrs, age_ticks)` —
  `src/domains/demographics/cohort.py:68-106`. Pure function; returns `None` for
  `age_ticks < 7000`, else an `EntityUpdate(entity_id=..., attributes=AttributeUpdate(...))` with
  STR/AGI −30%, VIT/END −50%, WIS/CHA +30% deltas (all as one-shot integer deltas, not
  set-values).
- `get_age_bracket(age_ticks)` — `src/domains/demographics/cohort.py:50-65`. **Caller grep**:
  `grep -rn "get_age_bracket" src/` → only inside `cohort.py` itself (definition +
  `compute_elder_attribute_update`'s internal check at line 95) and one *comment* reference in
  `src/ai/life_stage.py:45-50`. **`get_age_bracket()` has zero real callers anywhere outside its
  own module.** The ticket's premise ("Call `compute_elder_attribute_update()` once per
  aging-cycle tick where `get_age_bracket()` is already invoked") is based on a false premise —
  there is no such existing call site.
- **Real analogous call site found**: `LifeStageService.get_stage_for_age(age_ticks)` —
  `src/ai/life_stage.py:41-56` — deliberately *duplicates* `get_age_bracket()`'s exact 3000/7000
  boundaries under a different enum (`LifeStage.CHILD/ADULT/ELDER` vs. `"young"/"adult"/"elder"`
  strings), per the module's own comment (lines 45-50) citing
  `WORLD-DEMO-003` and `TCK-20260824-LIFE-STAGE-TRANSITIONS` as the reason for the deliberate
  duplication (separate vocabularies for separate subsystems). It is called once per entity per
  tick from `LifecycleSystem.resolve_lifecycle()` —
  `src/systems/lifecycle_systems/lifecycle.py:55-60` (via the `src/systems/lifecycle.py` re-export
  shim), which runs every tick as pipeline phase `"lifecycle"` (`src/engine/pipeline.py:361`, no
  interval gate). This is the true insertion point: the per-entity aging-tick site already reading
  `entity.lifecycle.age_ticks` and producing an `EntityUpdate` for that entity, immediately
  adjacent to the existing life-stage transition block (lines 51-60).
- **Risk — application cadence**: `compute_elder_attribute_update()` returns *delta* modifiers
  (e.g. `strength_delta=-int(attrs.strength*0.3)`), not idempotent set-values. `LifecycleSystem.resolve_lifecycle()`
  runs every tick unconditionally. If wired to fire every tick for every elder entity (rather than
  once, on the same forward-only transition edge `LifeStageService.is_forward_transition()` already
  guards for the parallel `life_stage` field), the modifier would compound every tick and drive
  attributes to zero/negative within a handful of ticks. The existing `is_forward_transition()`
  guard (line 56) is the correct pattern to mirror — apply once, on the tick `age_ticks` crosses
  into the elder bracket, not unconditionally. This is not addressed by the ticket's own AC
  wording and must be treated as a design decision for planning, not assumed.
- Parity ledger `WORLD-DEMO-004` (`docs/parity_ledger/world_dynamics.yaml:1143-1153`) is currently
  marked `status: verified` with `v2_evidence: 'src/domains/demographics/cohort.py
  (compute_elder_attribute_update); src/core/updates.py (AttributeUpdate, EntityUpdate)'` and
  `test_path: tests/unit/world/test_demographics.py::test_elder_modifier_reduces_combat_effectiveness`
  — this verifies the pure function's correctness in isolation only; it does **not** verify the
  function fires from any real tick. The "verified" status currently overstates what is actually
  wired. This entry's `v2_evidence`/`test_path` will need updating once (if) this ticket adds a
  real call site and integration test.
- `docs/mechanics/01_entity_anatomy.md` (§ 4 "Biological Laws (Decay & Needs)") has **no mention of
  "elder" anywhere** (`grep -n -i "elder" docs/mechanics/01_entity_anatomy.md` → zero matches),
  despite `WORLD-DEMO-004`'s text citing these exact modifiers as Mechanics-Bible-grounded and the
  closed `TCK-20260619-E52C-AGE-ADVANCEMENT` ticket instructing "Verify
  `docs/mechanics/01_entity_anatomy.md` § Biological Pressures for attribute modifier ranges before
  setting values" — that verification step appears to have been skipped or the doc was never
  actually updated to record the elder modifier formulas it approved.

### 7. consequence_events.py — social-encounter entry point

- `evaluate_social_consequence(entity, faction_id, campaign_state, tick=0)` —
  `src/systems/social_systems/consequence_events.py:61-176`. Pure, read-only function
  (module docstring, lines 16-21, explicitly forbids `src.engine`/`src.core.state` imports at
  module level; duck-types `entity`/`campaign_state`). Reads
  `campaign_state.faction_social_memories` and `campaign_state.social_memories`, returns up to 3
  `SimulationEvent`s (`KNOWN_TRAITOR_SPOTTED`, `LEGENDARY_ARRIVAL`, `OLD_DEBT_COLLECTED`).
  Docstring (lines 69-71): "Called at the start of a social encounter when an entity enters or
  interacts with a faction context... callers are responsible for emitting them via the
  authoritative pipeline."
- **Caller grep**: `grep -rn "evaluate_social_consequence" src/` → only its own definition. Zero
  callers.
- **No per-tick "social encounter" pipeline phase exists**: `grep -rln "faction_social_memories"
  src/` → only `src/domains/campaigns/state.py` (field definition, `CampaignState.faction_social_memories`,
  line 293) and `consequence_events.py` itself. `CampaignState` is a **cross-episode meta-state**
  object (`src/domains/campaigns/state.py:273`), separate from the per-tick `AuthoritativeState`
  that `src/engine/pipeline.py`'s phases operate on — it is never read from within
  `src/engine/pipeline.py` or any `pipeline_phases/*.py` file.
- **Real candidate site**: `CampaignOrchestrator._build_initial_state(episode_seed)` —
  `src/domains/campaigns/orchestrator.py:575-714` — constructs the `AuthoritativeState` for a new
  episode from `CampaignState` (via `_get_spawn_entities()`, `_get_spawn_factions()`, and related
  carry-forward extraction methods). This is the actual point where entities newly enter a
  faction's episode-context and where `campaign_state` (containing `faction_social_memories`) is
  already in scope — the natural place to evaluate `evaluate_social_consequence()` per spawned
  entity and append the returned events to whatever authoritative event-emission path the episode
  init already uses (needs a plan-time decision: emit via `world_events_add`/`SimulationEvent`
  queue that the observability layer already consumes, mirroring how `EventExtractor` /
  `WorldEvent` emission works elsewhere — see `DemographicCycleService.process_demographics()`,
  `src/domains/demographics/cohort.py:328-410`, for the established `world_events_add` pattern).
  This is a campaign/episode-boundary call site, not a per-tick pipeline phase — genuinely
  different in kind from the other 6 mechanisms' insertion points.
- Parity ledger `SOC-CROSS-EP-005` (`docs/parity_ledger/social_narrative.yaml:2609+`) already
  documents `evaluate_social_consequence()`'s pure-function behavior as `status: verified` (full
  entry not re-quoted here; text matches the function's current docstring/thresholds exactly) —
  again verifying the pure function in isolation, not any wired call site.
- The closed `TCK-20260619-E43E-CONSEQUENCE-EVENTS` ticket's own Scope explicitly said "In the
  social encounter phase (find where entity-NPC encounter evaluations happen)" but its Files
  Changed section shows only `consequence_events.py`, `events.py`, tests, and docs were touched —
  no wiring was ever done, matching current reality exactly (not a discrepancy, just confirms the
  orphaned status was known and deferred at closure time).

## Mechanics / Engine Constraints

- **Durable State Rule / Authoritative Application** (CLAUDE.md Architecture Rule; also
  `docs/core/state.md` immutability law): all 7 mechanisms already comply at the pure-function
  level (no direct state mutation, return typed records). The wiring step for #4 (Emotion) and #5
  (Reputation) must route their returned `EmotionalModel`/`PublicReputationProfile` through
  `EntityUpdate.cognition_bundle_set` (`src/core/updates.py:655`, applied in
  `src/engine/patches.py:742-743`) — the only existing typed path from a decision-layer service
  back into durable `entity.cognition` state, with a working precedent at
  `src/domains/memory/phase.py:51`. There is no per-field `emotion_set`/`public_reputation_set`
  update type; using `cognition_bundle_set` (whole-bundle replace) is the only architecturally
  sound option today.
- **#6 (compute_elder_attribute_update)** must respect the "never via direct mutation of frozen
  EntityState" language already recorded in `WORLD-DEMO-004`'s parity text — it already returns an
  `EntityUpdate`/`AttributeUpdate`, so this is satisfied mechanically; the open question is cadence
  (once-per-transition vs. every tick), not the update-typing mechanism.
- **#3 (SabotageAction/BuildingSabotageSystem)**: `docs/engine/authoritative_mutation_pipeline_contract.md`
  governs building mutation via the apply path — both classes already emit `BuildingUpdate`
  correctly; the constraint here is purely the duplicate-avoidance decision (Duplicate-Check B),
  not a new mutation-law concern.
- **#2 (EvolutionSystem/EvolutionService)**: `docs/mechanics/01_entity_anatomy.md` § "Progression &
  Growth" (XP curve, level-up rewards) is the governing chapter for evolution/level-up mechanics;
  `EvolutionSystem` (the live system) is already the parity-verified implementation
  (`docs/parity_ledger/progression.yaml`, `PROG-001`/`PROG-026`/`PROG-034` etc., all citing
  `src/engine/evolution.py`). `EvolutionService`'s conflicting thresholds (20 vs. 25 for the
  second stage) would directly violate the single-source-of-truth expectation these entries already
  assert if it were wired as a second live path.
- **#1 (InformationNeedDetector)**: `docs/mechanics/04_strategic_cognition.md` (Goal hierarchy,
  knowledge management) is the governing chapter; `STRAT-229` already documents the intended
  behavior at the pure-function level.

## Docs Requiring Update

- `docs/parity_ledger/world_dynamics.yaml`: `WORLD-DEMO-004`'s `v2_evidence`/`test_path` currently
  cite only the isolated unit test; once `compute_elder_attribute_update()` is wired into
  `LifecycleSystem.resolve_lifecycle()`, this entry needs a real call-site citation and (if a new
  integration test is added) an updated `test_path`.
- `docs/mechanics/01_entity_anatomy.md`: has zero mention of "elder" attribute modifiers anywhere
  in § Biological Laws, despite `WORLD-DEMO-004` and the closed `TCK-20260619-E52C-AGE-ADVANCEMENT`
  ticket both treating this as Mechanics-Bible-grounded behavior. This gap predates this ticket but
  becomes load-bearing once the modifier actually fires in production — the Mechanics Bible should
  record the formula once it is live, not only in the parity ledger.
- `docs/parity_ledger/strategic_cognition.yaml`: `STRAT-229`'s `v2_evidence`/`test_path` verify
  `detect_and_generate()` in isolation only; once wired into `CognitionDomain.execute_brain()`,
  this entry (or a new one) needs evidence of the real call site and, if added, a Kernel-run-backed
  test path per this ticket's own AC #1 wording.

The following docs were considered and are **not** required to change as part of this ticket
(Format 2 — prose only, no leading bullet):

`docs/parity_ledger/social_narrative.yaml`'s `SOC-CROSS-EP-005` entry already accurately describes
`evaluate_social_consequence()`'s pure-function behavior and does not misstate wiring status (its
text never claims the function is called from anywhere) — it does not need edits for this ticket
regardless of whether #7 is wired, unless the actual insertion point changes the function's
signature or return contract, which is out of scope here.

`docs/simulation/domains/emotion_contract.md` and `docs/simulation/domains/commitment_contract.md`
already describe the target-state call sites ("Engine event handlers — call
`EmotionUpdateService.update_on_event`" / "...`ReputationUpdateService.process_witnessed_event`")
in language that will become accurate once wiring lands; they do not need textual correction as a
result of this ticket, though a follow-on doc-updater pass replacing the generic "Engine event
handlers" phrasing with the concrete file:line citation (e.g.
`NearDeathHardeningPhase.apply()`) would be a nice-to-have, not a requirement — the doc's
factual claims would not be false either way once #4/#5 land.

`docs/parity_ledger/progression.yaml` is not required to change for the `EvolutionService`
fold/delete recommendation: none of its existing entries (`PROG-001`, `PROG-026`, `PROG-034`, etc.)
cite `src/progression/evolution.py` or `EvolutionService` anywhere — they already correctly cite
only `src/engine/evolution.py`/`EvolutionSystem` as the v2_evidence, so deleting the dead duplicate
does not orphan any parity claim.

## Parity Ledger Overlap

- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-229` (P1, `verified`): covers
  `InformationNeedDetector.detect_and_generate()` in isolation. Not P0; no test currently proves
  the Kernel-run wiring this ticket's AC demands.
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-DEMO-003` (P1, `verified`, `get_age_bracket`)
  and `WORLD-DEMO-004` (P1, `verified`, `compute_elder_attribute_update`). Neither is P0, so no
  hard test-path gate blocks this ticket, but `WORLD-DEMO-004`'s evidence needs updating per Docs
  Requiring Update above.
- `docs/parity_ledger/social_narrative.yaml` — `SOC-CROSS-EP-005` (status/priority not fully
  re-quoted; verified at the pure-function level, matches `evaluate_social_consequence()` exactly).
- `docs/parity_ledger/progression.yaml` — multiple `PROG-*` entries already cite
  `src/engine/evolution.py`/`EvolutionSystem` as the live evidence; none cite `EvolutionService`.
- **No parity ledger entries exist anywhere for `EmotionUpdateService` or `ReputationUpdateService`**
  (`grep -rln "EmotionUpdateService\|ReputationUpdateService" docs/parity_ledger/` → zero results).
  Wiring #4 and #5 will require **new** parity ledger entries (not status updates to existing
  ones) in `docs/parity_ledger/social_narrative.yaml` and/or a commitment/emotion-appropriate file,
  per the Authoritative Mechanics Rule ("If no entry exists, add one").
- No P0 entries are implicated by this ticket's scope — none of the touched entries carry
  `priority: P0`, so no entry strictly requires a passing `test_path` before this ticket can close,
  though adding real integration coverage is still expected under the Testing Rule.

## Prior Work

- `TCK-20260619-E42A-INFO-NEED` (implied by `STRAT-229`'s "(E42A)" tagging and
  `InformationNeedDetector`'s own docstring "Logic ID: E42A-001") — built the detector as a pure
  function; wiring was always deferred (matches current state exactly).
- `TCK-20260619-E43E-CONSEQUENCE-EVENTS` (`tickets/done/`) — built `evaluate_social_consequence()`
  and its 3 event kinds; its own Scope said to find and wire the social encounter phase, but Files
  Changed shows this was never done. Confirms #7's orphaned status was a known, accepted deferral,
  not a regression.
- `TCK-20260619-E52C-AGE-ADVANCEMENT` (`tickets/done/`) — built `get_age_bracket()` and
  `compute_elder_attribute_update()`; Scope explicitly said "Wire bracket-based modifiers into
  biological/attribute update phase," but Files Changed shows only `cohort.py`, tests, and the
  parity ledger were touched — the wiring line item in scope was never delivered, despite the
  ticket closing DONE and the parity ledger marking `WORLD-DEMO-004` "verified."
- `TCK-20260425-PH7-M4-SABOTAGE` (`tickets/done/`) — see Duplicate-Check B subsection above for
  the full historical-closure analysis. Not reconciled here per this ticket's Out of Scope.
- `TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE` — title suggests prior
  awareness of progression-domain reachability gaps; not directly read in full for this
  investigation (out of the explicit Related Code Areas list) but its existence corroborates that
  `src/progression/` has a known pattern of built-but-unreachable code, consistent with
  `EvolutionService`'s status found here.
- `TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING` — confirmed non-overlapping: its subject
  (`MemoryUpdatePhase` / route scoring informed by memory) does not touch any of
  `InformationNeedDetector`, `EvolutionService`/`EvolutionSystem`, `SabotageAction`/
  `BuildingSabotageSystem`, `EmotionUpdateService`, `ReputationUpdateService`,
  `compute_elder_attribute_update`, or `consequence_events.py` — no file or class overlap found in
  any of the source reads above.
- `TCK-20260618-AUDIT-D11-DEAD` — likely the origin audit that first flagged some or all of these
  orphaned mechanisms (title pattern matches a dead-code audit); not re-read in full since the
  current investigation independently re-verified every caller-count claim from source directly,
  per the Hard Rule against assuming prior research substitutes for a fresh check.

## Risks and Open Questions

1. **#1 insertion point is not literally where the docstring says it is.** `CognitionDomain.execute_brain()`
   has no "project evaluation" or "route scoring" steps inside it — those happen at the
   pipeline/`StrategicIntelligenceSystem`/`LeadRoutingSystem` level, outside `execute_brain()`.
   Planning must decide whether to (a) call `detect_and_generate()` inside `execute_brain()`
   anyway, near the emotional-appraisal/tactical-intent boundary (closest literal match to "after
   project eval, before route scoring" given execute_brain's actual two-step structure), or
   (b) treat the docstring's "in CognitionDomain.execute_brain()" as approximate and place the call
   in `StrategicIntelligenceSystem.fused_strategic_pass()` instead, where real project
   evaluation/route scoring actually live. This is a genuine open question requiring a planning
   decision, not something to assume.
2. **#5 (ReputationUpdateService) has no real production event for any of its 3 recognized
   `event_kind` strings.** Wiring it meaningfully requires either inventing new detection logic
   (e.g., a new `ESCORT` `QuestKind`, or activating the currently-dead `CooperationLearningService.learn()`
   betrayal branch) or accepting a looser mapping (e.g., generic quest completion → some
   `event_kind`) that doesn't match the literal strings the function currently branches on. This
   is the single riskiest item of the 7 and should not be assumed away in planning.
3. **#6 (compute_elder_attribute_update) cadence risk**: firing every tick (rather than once, on
   the bracket-entry transition edge) would compound the attribute deltas indefinitely. The plan
   must explicitly gate this the same way `LifeStageService.is_forward_transition()` gates the
   parallel `life_stage` field, or risk a real gameplay-breaking bug, not just a scope miss.
4. **#7's insertion point is architecturally different in kind from the other 6** — it's an
   episode/campaign-boundary call (`CampaignOrchestrator._build_initial_state()`), not a per-tick
   pipeline phase. This ticket's `layer: engine` framing (chosen for the per-tick pipeline
   majority) may not cleanly fit #7; flag for planning whether #7 needs different
   test/verification tooling (episode-level test harness vs. Kernel-tick test).
5. **EvolutionService/SabotageAction fold-or-delete is a judgment call this investigation
   recommends but does not execute.** Both dispositions (dead duplicate, recommend fold/delete)
   are evidence-backed but the actual deletion/consolidation is an implementation decision for
   planning — investigation does not delete files.

## Anti-Drift Hazards

- **Do not wire `SabotageAction` as a second, independently-triggered call site alongside
  `BuildingSabotageSystem`.** Two live paths that both reduce building HP via different damage
  formulas (ATK-scaled vs. flat 50) would silently double-apply damage if ever both matched the
  same entity/tick, and would make `BuildingSabotageSystem`'s existing integration tests
  (`tests/integration/pipeline/test_strategic_cadence.py`, `tests/integrity/test_logic_guards.py`)
  no longer describe the complete sabotage behavior.
- **Do not wire `EvolutionService` alongside `EvolutionSystem`.** Their conflicting second-stage
  thresholds (20 vs. 25) would make `goblin_1→goblin_2` evolution timing non-deterministic
  depending on which code path runs first, directly violating the "Do not break determinism" Hard
  Rule.
- **`compute_elder_attribute_update()` must not be applied on top of the existing `life_stage`
  transition indiscriminately** — see Risk #3. An unconditional per-tick application is an easy,
  large-blast-radius mistake (every elder entity's combat stats trend to zero over time).
- **`ReputationUpdateService`/`EmotionUpdateService` wiring must use `cognition_bundle_set`, not a
  new ad-hoc mutation path.** Given no per-field update type exists for `emotion`/`public_reputation`,
  it would be tempting to invent a shortcut (e.g., mutating `entity.cognition` directly in a
  decision-layer function) — this would violate "Do not mutate durable state outside authoritative
  flows." Follow the `src/domains/memory/phase.py:51` precedent exactly.
- **Do not conflate `ReputationService`(`src/systems/social_systems/reputation.py`) or
  `CooperationLearningService` with this ticket's scope.** Both are separately dead/orphaned code
  discovered during this investigation but are not in the ticket's 7-item Scope list — touching
  them would be scope creep beyond what Acceptance Criteria demand, even though they are
  thematically adjacent (reputation/cooperation).
- **`get_age_bracket()`/`LifeStageService.get_stage_for_age()` duplication is intentional per
  existing design decision** (see `src/ai/life_stage.py:44-50` comment citing
  `TCK-20260824-LIFE-STAGE-TRANSITIONS`) — do not "fix" this duplication as part of wiring #6; it
  is a deliberately separate vocabulary for a different subsystem, not a bug.

## Atomicity Recommendation

Per-mechanism complexity/risk estimate (lines touched is an order-of-magnitude estimate for the
call-site wiring only, not including any new tests):

| # | Mechanism | Est. lines | Call site isolation | Existing test coverage of target fn | Risk |
|---|---|---|---|---|---|
| 1 | InformationNeedDetector | ~5-15 | Insertion point itself is ambiguous (see Risk 1) | Yes, isolated (`STRAT-229`) | Medium — needs a planning decision on where "in `execute_brain()`" actually means |
| 2 | EvolutionService dup-check | 0 (delete) or ~5 | N/A — recommend delete, not wire | None (zero tests exist) | Low — decision is clear-cut, execution is trivial (delete a 30-line file) |
| 3 | SabotageAction dup-check | 0 (delete) or ~5 | N/A — recommend delete/fold, not wire as 2nd path | 3 direct-call unit tests only | Low-Medium — decision is clear-cut; deleting requires confirming nothing else imports `src/town/sabotage.py` |
| 4 | EmotionUpdateService | ~10-20 | Clean, isolated (`NearDeathHardeningPhase.apply()`) | Yes, isolated (`tests/unit/domains/emotion/test_phase16_emotion_update_service.py`) | Medium — first real use of `cognition_bundle_set` from a new call site; only 1 of 6 event kinds (`near_death`) has a confirmed real trigger site, the other 5 (`easy_win`, `repeated_failure`, `new_unknown`, `successful_goal`, `stagnation`) have no confirmed site found in this investigation |
| 5 | ReputationUpdateService | Unclear — depends on decision | No clean existing site for any of its 3 event kinds | Yes, isolated (`tests/unit/domains/commitment/test_phase15_reputation_update.py`) | **High** — see Risk 2; may require new detection logic beyond a simple call-site insertion |
| 6 | compute_elder_attribute_update | ~10-15 | Clean, isolated (`LifecycleSystem.resolve_lifecycle()`) | Yes, isolated (`tests/unit/world/test_demographics.py`) | Medium — cadence/transition-gating risk (Risk 3) must be designed correctly, not just inserted |
| 7 | consequence_events | ~15-30 | Different call-site kind (episode boundary, not per-tick phase) | Yes, isolated (`tests/unit/social/test_social_memory.py` per closed E43E ticket) | Medium-High — architecturally distinct insertion point, may need its own event-emission plumbing decision |

**Recommendation: split into separate child tickets rather than landing all 7 atomically in one
ticket.** Reasoning:

- Items 2 and 3 (the two duplicate-checks) are now resolved by this investigation with a clear
  recommended disposition (dead duplicate, fold/delete) that is fundamentally different work from
  "wire a call site" — a deletion/consolidation PR is a different shape of change (and different
  reviewer attention: verifying nothing else depends on the deleted code) than the other 5, which
  are additive call-site insertions. Bundling a deletion with 5 additive insertions in one diff
  increases review risk without a compensating benefit.
- Item 5 (ReputationUpdateService) has materially higher uncertainty than the other 6 — it may
  require new domain logic (a quest kind, or activating dead cooperation code) that the ticket's
  original Scope did not anticipate. Landing it atomically with the other 6 risks either scope
  creep (quietly adding a new `QuestKind`) or a half-wired result (calling the service with an
  event_kind that can never actually fire in practice, which would satisfy the letter of AC #5 but
  not its substance).
- Item 7 (consequence_events) has a structurally different insertion point (episode/campaign
  boundary vs. per-tick pipeline phase) from items 1, 4, and 6, which all insert into the
  Kernel's per-tick `AuthoritativeApplyPipeline`. Different verification tooling likely applies
  (episode-level harness vs. `pytest` Kernel-run), which is a natural ticket boundary.
- Items 1, 4, and 6 are the most homogeneous: all three are per-tick pipeline call-site insertions
  with clean existing target-function test coverage and confirmed real event-detection sites
  (modulo Risk 1's ambiguity for #1, and the caveat that only 1 of #4's 6 event kinds has a
  confirmed trigger). These three could reasonably land together in one ticket if the orchestrator
  prefers fewer child tickets, but even here #1's insertion-point ambiguity is a planning decision
  that should be resolved and documented before implementation, not discovered mid-diff.

Suggested split (for orchestrator's final call): **(a)** duplicate-check resolution ticket
(EvolutionService + SabotageAction fold/delete — items 2+3), **(b)** per-tick pipeline wiring
ticket (InformationNeedDetector + EmotionUpdateService + compute_elder_attribute_update — items
1+4+6), **(c)** ReputationUpdateService ticket (item 5, scoped down to whatever event-kind mapping
planning decides is realistic, possibly re-scoping away from the 3 literal strings if no real
event exists for them), **(d)** consequence_events episode-boundary wiring ticket (item 7). This
investigation supplies the evidence; the split itself is the orchestrator's call per the ticket's
own Assumptions/Open Questions section.
