---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE
artifact_type: test_plan
tags: [simulation-quality, progression]
---

# test_plan.md — TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE

## Regression Surface

None — this ticket makes no `src/` changes. Investigation-only; the diagnostic evidence below
substitutes for a pytest run since there is no code diff to regression-test.

## Evidence gathered (real, non-mocked — not new automated tests, per this ticket's own
## investigation-only conclusion)

1. Real `Kernel.tick_once()` × 300 on `dungeon_crawl` and `hero_guild_routing` (seed 42), scanning
   every entity's every `strategic.projects` entry for a `QuestState` instance: 0 found in either
   world. All observed projects are `GoalKind`-typed AI strategic goals.
2. `calibrate_simq.py` real engine runs, 2000 ticks each, `dungeon_crawl`/`sandbox_world`/
   `hero_guild_routing` (seed 42), raw `simulation_events.jsonl` preserved and grepped:
   `quest_reward_dispensed` count = 0 in all three, at every tick depth up to 2000.
3. Static trace: zero callers of `GuildAction` (`src/town/guild.py`) anywhere in `src/` outside its
   own file and one docstring reference; `ActionRouter.execute_action()` has no dispatch case for
   any guild-visit action verb.
4. Static trace: `QuestResolutionSystem` (`src/engine/quests.py`) has `evaluate_explore()` and
   `evaluate_combat_victory()` (HUNT-only) — no evaluator exists for `GATHER`/`BOUNTY`/`LIBERATE`.
5. Static trace + raw JSONL cross-check: `event_extractor.py:768-782`'s quest-event block has no
   `isinstance(qstate, QuestState)` filter; confirmed via raw event `quest_id` values from the
   2000-tick runs above (`proj_town_return_*`, `proj_combat_engage_*`, `proj_harvesting_*`,
   `proj_fatigue_*`) — all `GoalKind`-typed non-quest projects.

## New Tests Required

None in this ticket. Each of the 3 follow-up tickets filed (see the parent ticket's Completion
Summary) will own its own test-coverage obligations for its specific fix.

## Scoped Pytest Commands

None run — no `src/` diff to test. `implement-ticket.js`'s Test phase for this ticket confirms
`files_changed` contains no `src/` path, so no pytest command applies.

## Anti-Drift Test Guards

Any future ticket that wires `GuildAction` into the live action space, adds `GATHER`/`BOUNTY`/
`LIBERATE` evaluators, or filters `event_extractor.py`'s quest-event block by type must re-run this
ticket's own real-kernel scan pattern (entities' `strategic.projects` for `QuestState` instances,
plus a real multi-thousand-tick `quest_reward_dispensed` corpus check) as part of its own
verification — a passing unit-test suite alone would not have caught any of this investigation's 3
findings, since all 3 are reachability/wiring gaps invisible to isolated unit tests.
