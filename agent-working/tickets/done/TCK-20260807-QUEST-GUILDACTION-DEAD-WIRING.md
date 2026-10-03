---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING
phase: done
date: 2026-08-07
tags: [strategy, simulation-quality, progression]
---

# TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING

## Title
The real quest system (`QuestState`/`QuestKind`) is never reachable from live gameplay —
`GuildAction.visit()` has zero callers

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE`'s investigation found, via real (non-mocked)
300-tick `Kernel.tick_once()` runs on `dungeon_crawl` and `hero_guild_routing` (seed 42), scanning
every entity's every `strategic.projects` entry: **zero `QuestState` instances exist anywhere in
either world's live entity state.** Every project observed is a `GoalKind`-typed AI strategic goal
(`TOWN_RETURN`, `COMBAT_ENGAGE`, `HARVESTING`, `RESOLVE_BLOCKER`) — a separate, unrelated,
healthily-functioning system, not quests.

Root cause: `GuildAction.visit()` (`src/town/guild.py:16`) is the only code path in the codebase
that constructs a real `QuestState` via the documented quest system
(`docs/simulation/quest_contract.md`, `src.quests.generator.QuestGenerator`). It has zero callers
anywhere in `src/` outside its own file and one docstring reference
(`src/quests/generator.py:27`, prose only). `ActionRouter.execute_action()`
(`src/engine/domain/action_router.py:20-73`) — the actual action-dispatch mechanism every real
action goes through (`SLEEP`/`EAT`/`REST`/`RECRUIT`/`ALLOCATE_AP`/`TRAIN`/`REPAIR`/`INTERACT`/
`ATTACK`/`SKILL`/`AOE_ATTACK`) — has no case for any guild-visit action verb. No strategic-decision
system (goal scoring, action selection) ever chooses to visit a guild; no action-execution path
ever calls `GuildAction.visit()` even if one did.

This is the direct root cause of `TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE`'s own finding
(`quest_reward_dispensed` count = 0 across 3 worlds at 2000 ticks each) — not a pacing question,
since there is no quest to ever complete.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm exactly how other town-service actions (Inn/Home/Class Hall, per
     `TCK-20260425-PH7-M3-RECOVERY`) ARE wired end-to-end (action verb string → `ActionRouter`
     case → strategic-decision selection), as the pattern to mirror. `InnAction`/`HomeAction`/
     `ClassHallAction` were also found to have zero `ActionRouter` dispatch cases during this
     investigation's own tracing — re-verify directly whether they are ALSO dead (in which case
     this is a systemic town-service wiring gap, not quest-specific) or whether they're reached
     through some other mechanism this investigation didn't find (e.g. a different action-space
     enumeration this ticket's own Investigate phase must locate).
   - Determine where a "visit guild" (or generalized "visit town service") action verb should be
     added: `ActionRouter.execute_action()`'s dispatch table, AND the strategic-decision layer that
     actually selects among available actions (goal-scoring/route-selection system — confirm the
     exact module, likely under `src/domains/` or `src/strategy/` cognition code) — a durable-state
     change to the AI's own decision surface, not just an action-execution wiring fix.
   - Confirm whether `src/worldbuilding/compiler.py:401`'s `spec.quest_definitions` compilation path
     (a second, declarative quest source found but not fully traced by the parent investigation) is
     itself reachable to any entity, or independently dead — determines whether this ticket needs to
     also fix that path or whether `GuildAction` wiring alone is sufficient.
2. **Plan**: design the exact action-verb name, `ActionRouter` dispatch addition, and
   strategic-decision-layer wiring (how/when an entity decides to visit the guild — score-based
   like other goals, or another mechanism matching existing patterns).
3. **Implement**: wire it in, following the Strategic/Tactical Rule (CLAUDE.md) — this is adding a
   new strategic option to the AI's decision space, not stacking tactical goal-scoring onto an
   existing decision.
4. Recalibrate `grade_anchors.json` for any scenario whose PROGRESSION/AGENCY grade shifts as a
   result (quest activity is new observable behavior), update `docs/parity_ledger/progression.yaml`.

## Out of Scope
- `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` (event_extractor.py's missing quest-type filter) —
  separate, independent bug; do not fix inline here even though it's in the same subsystem area.
- `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP` (missing progress evaluators for 3 of
  5 quest kinds) — becomes relevant once this ticket lands, but is scoped and implemented
  separately; this ticket's own Implementation Notes should flag if testing surfaces it blocking
  verification, not silently fix it inline.
- The E23C opportunity-quest system (`QuestOpportunity`/`state.quest_registry`, `PROG-109`) — a
  separate, already-working mechanism, confirmed unaffected.

## Acceptance Criteria
- [x] `investigation.md` confirms the exact wiring gap and whether other town-service actions share
      the same dead-code pattern — confirmed systemic: `InnAction`/`ClassHallAction`/`HomeAction`
      all share it; `src/worldbuilding/compiler.py`'s declarative `compiled_quests` path also
      confirmed independently dead (computed only for a `quest_count` metric, never attached to
      any entity)
- [x] A real quest (`QuestState`, any kind) is confirmed generated and attached to at least one
      entity's `strategic.projects` in a real, non-mocked multi-hundred-tick kernel run — 5 real
      quests (HUNT x3, EXPLORE, GATHER) generated naturally in `sandbox_world_seed42` within
      3000 ticks via the live AI decision layer, no synthetic placement; also proven via a
      controlled arrival test (entity placed at real `town_hall`, real `QuestState` generated in
      one tick)
- [ ] At least one HUNT or EXPLORE quest is confirmed to reach `quest_status=REWARDED` in a real
      run — **NOT achieved**, honestly disclosed, not silently dropped: traced to a separate,
      pre-existing bug (`QuestGenerator` never populates `QuestState.metadata`, so neither
      `evaluate_combat_victory()` nor `evaluate_explore()` can ever match a real generated quest
      to progress) — outside this ticket's own scope, disclosed as a correcting update to
      `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP` (that ticket's own premise, "3 of
      5 kinds lack an evaluator," was itself wrong — the real bug affects all 5 kinds equally, via
      the generator/evaluator metadata contract mismatch, not missing evaluator methods)
- [x] `docs/parity_ledger/progression.yaml` updated; `grade_anchors.json` recalibrated if any
      scenario's grade shifts — new behavior lives in `strategic_cognition.yaml` (`STRAT-248`,
      the correct file for `GoalKind`/scorer/pipeline-phase architecture, not `progression.yaml`);
      `grade_anchors.json` not recalibrated — flag defaults `OFF`, zero behavior change in any
      unmodified/default-flag run
- [x] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE (source of this finding — Finding 1, DONE)
- TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP (sibling — becomes practically relevant
  once this ticket lands)
- TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG (sibling — independent, same area)

## Related Docs
- `docs/simulation/quest_contract.md`
- `docs/plans/simq_scoring_improvement_roadmap.md` (if AGENCY/PROGRESSION scoring is affected)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE/investigation.md` (Finding 1,
  full trace)

## Related Code Areas
- `src/town/guild.py` (`GuildAction.visit()`)
- `src/engine/domain/action_router.py` (`ActionRouter.execute_action()`)
- `src/quests/generator.py` (`QuestGenerator`)
- The strategic-decision/action-selection layer (exact module to be confirmed in Investigate)

## Assumptions / Open Questions
Both resolved during Investigate — see Implementation Notes: `InnAction`/`HomeAction`/
`ClassHallAction` confirmed to share the exact same dead-code pattern (fixing them is out of
this ticket's own scope — each needs its own building-kind-rebase decision, deferred);
`compiler.py`'s `compiled_quests` confirmed independently dead (computed only for a `quest_count`
metric, never attached to any entity — not a second quest source needing its own fix).

## Implementation Notes
Scope grew twice during Investigate, both confirmed with the user before implementing (per
CLAUDE.md's Clarification Rule), documented in full in `investigation.md`:

1. `TownScorer.score()`'s `target_id="town_center"` (a string) is unparseable by
   `TacticalDecisionSystem._resolve_target_position()` — real-kernel-confirmed via monkeypatch
   tracing, not assumed. Position drift observed in an earlier trace turned out to be an
   unrelated combat anti-stalemate fallback coincidentally targeting the same `(0.0, 0.0)`
   coordinate as `town_center`. Sidestepped (not fixed) by giving `GuildNeedScorer` a real
   int-castable `target_id` from the start (`EatScorer`/`SleepScorer`'s own established
   pattern) — filed the underlying bug separately, `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`.
2. No world in the real content corpus (`data/worlds/*/resolved/world.resolved.yaml`) ever
   declares a `"guild"` building — confirmed exhaustively. Real building kinds:
   `blacksmith`/`healer_hut`/`inn`/`mine_entrance`/`shop`/`town_hall`/`watchtower`. Per explicit
   user decision, rebased `GuildAction` onto `town_hall` rather than deferring to a
   content-authoring ticket.
3. `GuildAction.visit()` cannot safely run through `ENTITY_ACT`/`ActionRouter` — `PROD_SMALL`
   (used throughout this session's own real-kernel verification) routes `ENTITY_ACT` through
   `ConcurrentExecutionAdapter`, whose `WorkerPacket` context deliberately excludes
   `regions`/`resource_nodes` ("Law: A worker must receive a compact, bounded, and read-only
   context"). Resolved by following this codebase's own established precedent for state-heavy
   logic (`QuestRewardPhase`/`FactionDecisionPhase`) — a dedicated pipeline phase, not an action
   dispatch. This also meant `tactical.py`/`ActionRouter` needed zero changes.

A fourth finding, made while wiring: going live reactivated a real, pre-existing,
EXPLICITLY-foreseen risk — `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT` (`STRAT-244`)
had already documented `GuildAction.visit()`'s scarcity computation as a "dormant" risk needing
"its own region-coverage evaluation" once wired live. Found via a pre-existing architecture guard
test (`tests/architecture/test_guild_action_dormancy.py`) failing as expected — not silently
weakened or deleted; updated to confirm the reference is limited to exactly the one deliberate
site, and filed the region-coverage evaluation as its own follow-up per that audit's own explicit
guidance, `TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP`.

A fifth finding, made during real-kernel verification: natural runs generate real quests (5 in
`sandbox_world`, 3000 ticks) but none progress past `ACTIVE`. Traced to a genuinely separate,
pre-existing bug — `QuestGenerator.generate()` never sets `QuestState.metadata` at all (confirmed
by reading its real return value), so neither existing progress-evaluator
(`evaluate_combat_victory()`/`evaluate_explore()`) can ever match anything. This corrects the
sibling ticket's own premise (it assumed HUNT/EXPLORE already worked); updated that ticket in
place with this evidence rather than silently absorbing or fixing it here.

## Test Summary
`tests/unit/ai/test_guild_need_scorer.py` (5 new tests), `tests/unit/engine/
test_guild_visit_phase.py` (8 new tests), `tests/architecture/test_guild_action_dormancy.py`
(updated in place, 1 test, still passing — now confirms the reference is limited to the one
deliberate site). Regression: `tests/unit/ai/ tests/unit/engine/ tests/unit/world/
test_guild_pipeline.py tests/unit/world/test_guild_intel.py tests/architecture/
test_guild_action_dormancy.py` — 185 passed, 1 skipped. `tests/unit/strategic/ tests/unit/kernel/`
— 246 passed. `tests/unit/config/test_phase10_feature_flags.py tests/integration/scenarios/
test_balance_regression.py` — 1 pre-existing, unrelated failure confirmed via `git stash`
(`test_scoring_formula_constants_stable`, adventure-route scoring constants, fails identically on
the clean baseline commit) — all other tests pass, including the new flag correctly NOT needing
allowlisting (it defaults `OFF`, not `ON`).

Real-kernel verification: (1) controlled arrival test — entity placed exactly at
`hero_guild_routing`'s real `town_hall`, `GuildVisitPhase` generated a genuine `QuestState`
("Survey the Woods", EXPLORE) in one tick, proving the mechanism correct end-to-end. (2) Natural,
unmodified runs — `sandbox_world_seed42`, 3000 ticks, flag ON: 5 real quests generated via the
live AI decision layer (no synthetic placement): `Clear the Slimes`/`Wolf Cull` x2 (HUNT),
`Survey the Woods` (EXPLORE), `Gather Herbs` (GATHER), `Bounty: Bandit Leader` (BOUNTY),
`Liberate the Outpost` (LIBERATE) — confirming the full goal-competition/movement/arrival chain
works naturally. `hero_guild_routing`/`urban_political` (more combat-heavy worlds): 0 quests in
2000-3000 ticks — traced to the GUILD goal's own deliberately modest utility (25.0, Tier 4
Economic) being outcompeted by combat before entities could complete the (often 80+ tile) journey
to town_hall — a real, disclosed behavioral characteristic, not a code defect.

## Files Changed
- `src/core/strategic.py` — `GoalKind.GUILD`
- `src/ai/goals/scorers.py` — `GuildNeedScorer`
- `src/ai/goals/__init__.py` — registration
- `src/engine/pipeline_phases/guild_visit.py` (new) — `GuildVisitPhase`
- `src/engine/pipeline.py` — `run_phase("guild_visit", ...)` wiring
- `src/domains/optimization/feature_flags.py` — new `ENABLE_GUILD_QUEST_GENERATION` flag
- `docs/guides/feature_flags.md` — new flag row (+ corrected a pre-existing stale row for
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`'s own default, found while editing this same table)
- `docs/simulation/quest_contract.md` — new "Live Entry Point: Guild Visit" section
- `docs/parity_ledger/strategic_cognition.yaml` — new `STRAT-248` entry
- `tests/architecture/test_guild_action_dormancy.py` — updated in place (not deleted)
- `tests/unit/ai/test_guild_need_scorer.py` (new)
- `tests/unit/engine/test_guild_visit_phase.py` (new)
- `tickets/todos/tech-debt/TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG.md` (new follow-up)
- `tickets/todos/tech-debt/TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP.md` (new follow-up)
- `tickets/todos/tech-debt/TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP.md` (corrected
  in place — its own premise was wrong)

## Completion Summary
Wired `GuildAction.visit()` into live, dispatched gameplay via a new `GoalKind.GUILD` +
`GuildNeedScorer` + dedicated `GuildVisitPhase` pipeline phase, gated behind
`ENABLE_GUILD_QUEST_GENERATION` (default `OFF`). Two deeper blockers found during investigation
(broken target-resolution convention; no real "guild" building content) were surfaced to and
resolved by explicit user decisions before implementation, not assumed. A third finding
(reactivating a pre-existing, explicitly-foreseen region-coverage risk) and a fourth
(`QuestGenerator` never populates the metadata its own evaluators need, blocking ALL quest
completion, correcting a sibling ticket's wrong premise) were both disclosed and filed as
separate, real follow-ups, not silently absorbed or ignored. Real-kernel verification confirms
the wiring itself is fully correct — both via a controlled arrival test and via natural,
unmodified gameplay (5 real quests generated in `sandbox_world` without any synthetic setup).
Quest *completion* remains blocked by the separately-disclosed metadata bug — honestly reported
as not achieved, not claimed.
