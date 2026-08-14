---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG
artifact_type: investigation
tags: [strategy, simulation-quality]
---

# Investigation: TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG

## Confirmed root cause

`TownScorer.score()` (`src/ai/goals/scorers.py:79-98`) returns
`GoalScore(kind=GoalKind.TOWN_RETURN, target_id="town_center", target_pos=state.town_center)`.
`evaluate_strategic_intent()` (`src/systems/strategic_systems/intelligence.py:1327-1331`) builds
the resulting `ObjectiveState(target=best_candidate.target_id, target_position=best_candidate.target_pos, ...)`
— so the objective ends up with `target="town_center"` (a bare, non-parseable string) AND
`target_position=state.town_center` (the real, correct tuple) simultaneously.

`TacticalDecisionSystem._resolve_target_position()` (`src/engine/tactical.py:694-728`, prior to
this fix) only ever read `obj.target` — tried `int(obj.target)` (fails, `ValueError`), then
`ast.literal_eval(obj.target)` (fails on `"town_center"`, `ValueError`) — and returned
`(None, None, None)`. `obj.target_position` was never consulted at all. The caller's own guard
(`if target_pos:`) then silently no-ops the entire arrival-dispatch/navigation block — no error,
no log, just a permanently inert project.

Confirmed empirically (not assumed) via a direct call sequence exercising the real production
functions: `StrategicIntelligenceSystem.evaluate_strategic_intent()` (creates the TOWN_RETURN
project with a high-hunger/high-sleep-debt entity) → manually attach the resulting project/
objective to a fresh `EntityState` → `TacticalDecisionSystem.evaluate_entity_intent()`. Before the
fix, this produced `navigation=None`. After the fix, `navigation=NavigationUpdate(target_set=(0.0,
0.0), ...)` — matching `state.town_center`. See `tests/unit/strategic/test_expanded_goals.py`'s
`test_town_return_project_now_produces_real_navigation` for the permanent regression test that
codifies this same sequence.

`RecoverScorer`'s no-inn fallback (`scorers.py:186`, `target_id="town_center"`) and
`ResolveBlockerScorer`'s general case (`scorers.py:197`, `target_id=str(blocker.id)` — a blocker
ID like `"b1"`, not int-castable and not a coordinate string) are affected by the exact same root
cause: whatever they set `target_id` to, when it's neither int-castable-and-resolvable nor a
coordinate string, `_resolve_target_position` returned `None` even though `target_position` had
already been set correctly.

## Chosen fix — option (a), as the ticket's own Scope section already recommended

Added a fallback inside `_resolve_target_position`: after the existing int-parse and
coordinate-string-parse attempts both fail to yield a `target_pos`, fall back to
`obj.target_position` if it is set. This mirrors
`StrategicIntelligenceSystem._resolve_active_objective()`'s own pre-existing "detour" case
(`intelligence.py:1030-1044`), which already preferred `target_position` this exact way — the two
"resolve an objective's position" implementations are now aligned rather than diverged.

**Why fallback order matters**: unlike the detour case (which only ever needs a position, no
ID), `_resolve_target_position` also needs to yield `node_id`/`building_id` for the currently-
working `HarvestScorer`/`EatScorer`/`SleepScorer`/`GuildNeedScorer` paths, which drive the
INTERACT/EAT/REST arrival-dispatch branches. The int-parse attempt is always tried FIRST and, for
those paths, always succeeds — so the `target_position` fallback never activates for them,
preserving `node_id`/`building_id` exactly as before. The fallback only fires for objectives whose
`target_id` was never parseable to begin with (TOWN_RETURN/RECOVER-no-inn/RESOLVE_BLOCKER),
where `node_id`/`building_id` were always `None` anyway.

## Confirmed unaffected: currently-working int-castable paths

Added a dedicated anti-regression test
(`test_reach_location_target_position_fallback_does_not_override_resolvable_node_id`) that sets a
DELIBERATELY WRONG `target_position` alongside a real, resolvable `target` (resource-node ID), and
confirms the int-parse branch's own correct position wins — proving the fallback genuinely never
overrides the currently-working path rather than just happening to agree with it in the common
case.

## Confirmed open question, disclosed not fixed (per ticket's own Assumptions/Open Questions)

This fix makes `TOWN_RETURN`/`RECOVER`/`RESOLVE_BLOCKER` objectives navigate toward a real
position. It does NOT extend arrival-dispatch for these project kinds — at arrival (Manhattan
distance ≤ 1.0), since `node_id`/`building_id` stay `None` for the `target_position`-only path,
the existing `else: return EntityUpdate(entity_id=entity.id)` branch (tactical.py:252) fires — a
bare idle update. The entity now purposefully walks to town center / the blocker's location, but
currently does nothing useful once there (same shape as `GUILD` before its own dedicated
`GuildVisitPhase` was added, `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`). Extending
arrival-dispatch for these 3 project kinds is real, deferred future work — not filed as a
follow-up ticket in this pass, since the project kinds' intended arrival behavior (what SHOULD
happen at town center for a `TOWN_RETURN` project — full inventory/quest sell-off? nothing,
since HUNGER/FATIGUE/HARVESTING are separate independent goals that will naturally re-trigger once
the entity is in town?) is itself an open game-design question, not just a wiring gap like
`GUILD`'s was.

## Real-kernel verification

Ran the exact production call sequence described above (not a full multi-tick kernel run, but the
real, unmocked `StrategicIntelligenceSystem.evaluate_strategic_intent()` →
`TacticalDecisionSystem.evaluate_entity_intent()` pipeline pair) with a hero entity at
`hunger=90.0, sleep_debt=90.0` and `state.town_center=(0.0, 0.0)`: confirmed `TownScorer` wins the
goal competition, produces a `TOWN_RETURN` project with `target="town_center"`,
`target_position=(0.0, 0.0)`, and — after this fix — `TacticalDecisionSystem.evaluate_entity_intent()`
returns a real `NavigationUpdate(target_set=(0.0, 0.0), ...)`. Codified as a permanent regression
test.
