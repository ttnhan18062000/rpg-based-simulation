---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING
artifact_type: plan
tags: [strategy, simulation-quality, progression]
---

# plan.md — TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING

## Ordered Steps

1. `src/domains/optimization/feature_flags.py`: add `"ENABLE_GUILD_QUEST_GENERATION":
   FeatureMode.OFF` to `FeatureFlagManager.__init__`'s `_flags` dict (must be present here for
   `set_flag_mode`'s guard to accept a `state.feature_flags` override at all).
2. `src/core/strategic.py`: add `GUILD = "guild"` to `GoalKind`.
3. `src/ai/goals/scorers.py`: add `GuildNeedScorer`, flag-gated internally (returns
   `utility=0.0` immediately if `ENABLE_GUILD_QUEST_GENERATION` isn't `"ON"`), using
   `SpatialQueryService.nearest_building(state, pos, "town_hall")` and spare-project-capacity
   utility.
4. `src/ai/goals/__init__.py`: `GoalRegistry.register(GoalKind.GUILD, GuildNeedScorer())`.
5. `src/engine/pipeline_phases/guild_visit.py` (new file): `GuildVisitPhase.resolve(state,
   update) -> StateUpdate` — arrival detection + `GuildAction.visit()` call + project completion,
   using `EntityUpdate.merge()` to compose safely with any existing update for the same entity
   this tick.
6. `src/engine/pipeline.py`: wire `run_phase("guild_visit", update, lambda u:
   GuildVisitPhase.resolve(state, u), "ENABLE_GUILD_QUEST_GENERATION")`, placed after
   `quest_rewards` (Economy & Evolution phase group) — new project completion/lead generation is
   conceptually adjacent to quest reward resolution, not earlier trust/validity phases.
7. `docs/guides/feature_flags.md`: new flag row.
8. `docs/simulation/quest_contract.md`: note `GuildVisitPhase` as the new live entry point,
   distinct from the pre-existing Objective Reward stage.
9. `docs/parity_ledger/strategic_cognition.yaml`: new entry.
10. File `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG` into `tickets/todos/tech-debt/`
    (investigation.md's disclosed, deferred finding).
11. Unit tests: `GuildNeedScorer` (flag OFF → utility 0; flag ON + spare capacity + nearby
    town_hall → real GoalScore; flag ON + no spare capacity → utility 0), `GuildVisitPhase`
    (arrival triggers visit + project completion; not-yet-arrived → no-op; flag OFF → no-op even
    with an active guild project).
12. Real-kernel verification: `hero_guild_routing`/`urban_political` (both have `town_hall`),
    flag ON, confirm real `QuestState` instances now appear in `entity.strategic.projects`
    (repeating `TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE`'s own real-kernel scan, which
    previously found zero).

## Files to Change

- `src/domains/optimization/feature_flags.py`
- `src/core/strategic.py`
- `src/ai/goals/scorers.py`
- `src/ai/goals/__init__.py`
- `src/engine/pipeline_phases/guild_visit.py` (new)
- `src/engine/pipeline.py`
- `docs/guides/feature_flags.md`
- `docs/simulation/quest_contract.md`
- `docs/parity_ledger/strategic_cognition.yaml`
- `tickets/todos/tech-debt/TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG.md` (new)
- `tests/unit/ai/test_guild_need_scorer.py` (new)
- `tests/unit/engine/test_guild_visit_phase.py` (new)

## Scope Guards

- Do NOT touch `tactical.py` or `ActionRouter`/`CoreActions` — `GuildVisitPhase`'s own
  independent arrival-check makes this unnecessary, and avoids the WorkerPacket/concurrent-worker
  risk entirely.
- Do NOT touch `_resolve_target_position`/`TownScorer` — separate, disclosed, deferred finding.
- Do NOT touch `InnAction`/`ClassHallAction`/`HomeAction` — each needs its own investigation.
- Do NOT touch `QuestResolutionSystem`'s evaluators (`GATHER`/`BOUNTY`/`LIBERATE`) — sibling
  ticket's own scope.
- Do NOT modify `docs/systems/buildings_and_economy.md` — confirmed stale/legacy-V1, out of
  scope to rewrite; not cited as a source of truth by this ticket's own doc updates.

## Dependency Map

Steps 1-4 must land together (scorer references the flag and GoalKind). Step 5 depends on 1-2.
Step 6 depends on 5. Steps 7-9 depend on 1-6's final shape. Step 10 is independent. Step 11
depends on 1-6. Step 12 depends on 11's real pass.

## Acceptance Criteria Map

- AC "investigation.md confirms the exact wiring gap and shared-pattern check" →
  investigation.md (done) — found InnAction/ClassHallAction/HomeAction share the pattern, decided
  not to fix them here
- AC "a real quest is confirmed generated and attached to an entity in a real kernel run" →
  step 12
- AC "at least one HUNT or EXPLORE quest reaches REWARDED in a real run" → step 12 (extended —
  needs enough ticks; document actual observed outcome honestly, not assumed)
- AC "docs/parity_ledger/progression.yaml updated" → superseded: new behavior lives in
  `strategic_cognition.yaml` (GoalKind/scorer architecture), not progression — step 9
- AC "grade_anchors.json recalibrated if any scenario's grade shifts" → checked post-step-12
- AC "scoped pytest run passes" → step 11's real run
