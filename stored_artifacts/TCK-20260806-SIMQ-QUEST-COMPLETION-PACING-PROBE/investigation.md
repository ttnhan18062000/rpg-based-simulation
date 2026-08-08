---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE
artifact_type: investigation
tags: [simulation-quality, progression]
---

# investigation.md — TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE

## Current Behavior

**Conclusion: NOT a pacing artifact — three real, independent defects, confirmed via real-kernel
evidence, not code reading alone.**

### Finding 1 (root cause): the real quest system is never exercised in live gameplay at all

Ran a real, non-mocked `Kernel.tick_once()` loop for 300 ticks on `dungeon_crawl` and, separately,
`hero_guild_routing` (seed 42), scanning every entity's every `entity.strategic.projects` entry
for a `QuestState` instance at the end. **Zero found in either world.** All observed projects were
`GoalKind`-typed AI strategic goals (`TOWN_RETURN`, `COMBAT_ENGAGE`, `HARVESTING`,
`RESOLVE_BLOCKER`) — a completely separate, unrelated, and healthily-functioning strategic-goal
system, not quests.

Traced why: the only code path that constructs a real `QuestState` via the documented quest system
(`docs/simulation/quest_contract.md`, `src.quests.generator.QuestGenerator`) is
`GuildAction.visit()` (`src/town/guild.py:16`). Grepped every caller of `GuildAction` across
`src/`: **zero callers exist anywhere except its own file and one docstring reference**
(`src/quests/generator.py:27`, prose only). `ActionRouter.execute_action()`
(`src/engine/domain/action_router.py:20-73`) — the actual action-dispatch mechanism every real
action (`SLEEP`/`EAT`/`REST`/`RECRUIT`/`ALLOCATE_AP`/`TRAIN`/`REPAIR`/`INTERACT`/`ATTACK`/`SKILL`/
`AOE_ATTACK`) goes through — has no case for a guild-visit action at all. `GuildAction` is dead
code: no strategic-decision system ever selects it, no action-execution path ever calls it.

Also confirmed two other quest-construction sites are dead:
`src/systems/world_systems/quest_generator.py`'s `QuestGenerator.generate_for_entity()` (zero
callers of its re-export module `src/systems/quest_generator.py`) and
`src/systems/world_systems/quests.py`'s `quest_to_project()` (zero callers anywhere). Neither
contradicts the conclusion — they're separate, independently-dead code paths, not alternate live
routes.

`src/worldbuilding/compiler.py:401` DOES compile `QuestState` objects from `spec.quest_definitions`
at world-assembly time — but the real-kernel scan (which reads live post-assembly entity state, not
just the compile-time intermediate) found none attached to any entity's `strategic.projects` in
either sampled world, so this declarative path is not currently populating live entity state
either (not traced further — establishing *that* it doesn't reach entities was sufficient to
confirm zero real quests exist at runtime; tracing the exact reason inside compiler.py's own
entity-assignment logic is follow-up-ticket work, not this investigation's job).

### Finding 2 (independent bug): `event_extractor.py`'s "quest_event" has no quest-type filter

`event_extractor.py:768-782`'s "Quest progress lifecycle events" block iterates
`entity.strategic.projects.items()` with **no `isinstance(qstate, QuestState)` check** —
constructing a `QuestEvent` for every strategic project of every kind, quest or not. Confirmed via
raw `simulation_events.jsonl` from 3 real 2000-tick corpus runs (`dungeon_crawl`, `sandbox_world`,
`hero_guild_routing`, seed 42): 182-700 "quest_event" messages per run, with `quest_id` values
like `proj_town_return_267`, `proj_combat_engage_9`, `proj_harvesting_12`, `proj_fatigue_400`,
`proj_resolve_blocker_37`, `proj_combat_retreat_388` — every single one a `GoalKind`-typed AI
strategic goal, none a real quest. This is why the parent ticket's own sample (2 of 650+ messages)
looked like real quest activity: it wasn't sampling widely enough to notice the entire stream is
mislabeled AI-goal churn, not quest telemetry.

Also confirmed: even where the code does compare `prior_qstate.status != qstate.status`
(`event_extractor.py:778`), it reads `.status` (the generic `ProjectState`-inherited
`ProjectStatus` field) — not `.quest_status` (the `QuestStatus` field `QuestService.add_progress()`/
`mark_rewarded()` actually mutate, `src/core/models/quests.py:35-48`). Even if a real `QuestState`
existed and completed, this event stream would never observe it: `QuestService`'s own methods never
touch `.status`, only `.quest_status`, so the `!=` comparison at line 778 would never fire for a
quest's own natural completion — only for something else changing the generic `ProjectStatus`
(e.g. abandonment, already handled separately at lines 786-799).

### Finding 3 (independent gap, currently unreachable given Finding 1): 3 of 5 quest kinds have no
### progress-evaluation wiring

`QuestResolutionSystem` (`src/engine/quests.py`) has exactly two progress-evaluator methods:
`evaluate_explore()` (EXPLORE kind, wired via `movement_actions.py:35` on movement completion) and
`evaluate_combat_victory()` (explicitly filtered to HUNT kind only — `project.quest_kind !=
QuestKind.HUNT: continue`, line 90 — wired via `combat_actions.py:72` and `aoe_actions.py:91` on
kill). **`GATHER`, `BOUNTY`, and `LIBERATE` have no `evaluate_*` method at all** — a quest of any
of these 3 kinds could never progress toward `goal_value`, regardless of tick depth, even if it
were successfully generated. This gap is currently masked/unreachable in practice by Finding 1
(no quests of any kind are ever generated at all), but would become a real blocker the moment
Finding 1's fix (wiring quest generation into the live action space) lands.

## Real-kernel verification (`quest_reward_dispensed`, 3 worlds, 2000 ticks each)

Ran `dungeon_crawl`, `sandbox_world`, `hero_guild_routing` (seed 42, 2000 ticks each) via
`calibrate_simq.py`, preserving raw `simulation_events.jsonl`. Grepped for
`event_type=="quest_reward_dispensed"` in all three: **0 in every world, at every tick up to
2000.** Fully consistent with Finding 1 (no real quests ever exist to be rewarded) — not a pacing
question at all; more ticks cannot produce a completion that has no quest to complete.

## Mechanics/Engine Constraints

`docs/simulation/quest_contract.md` documents the intended quest lifecycle
(`[generated] → ACTIVE → COMPLETED → REWARD_PENDING → REWARDED`) and the Objective Reward stage's
role — both are logically sound and internally consistent; the defect is entirely in the
*reachability* of this system from live gameplay (Finding 1), not in the lifecycle logic itself.
No Mechanics Bible chapter documents quests directly (the quest system lives in
`docs/simulation/quest_contract.md`, not `docs/mechanics/`) — no divergence from an authoritative
formula, so no `intentional_divergences.md` entry is needed for this investigation-only ticket.

## Docs Requiring Update

None. This is a diagnosis, not a fix — no behavior changed, no doc describes the (correct,
unchanged) intended lifecycle inaccurately. The 3 follow-up tickets filed below will each carry
their own doc-update obligations once implemented.

## Parity Ledger Overlap

None touched — no `src/` behavior change in this ticket. `PROG-109` (`docs/parity_ledger/
progression.yaml`, the E23C opportunity-quest reward path) is a distinct, already-working
mechanism (separate `QuestOpportunity`/`state.quest_registry` system, not affected by any finding
here) — confirmed not to overlap, not touched.

## Prior Work

- `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY` (parent — the 2-message sample that
  originally looked like real quest activity, now explained by Finding 2).

## Risks and Open Questions

None left open for this ticket's own scope. Three follow-up tickets are filed for the fix work
(see Completion Summary) — each carries its own open questions in its own ticket file, not
resolved here per the Uncertainty Rule.

## Anti-Drift Hazards

- Any future ticket touching quest generation must re-verify against a real kernel run (as this
  investigation did) rather than trusting `docs/simulation/quest_contract.md`'s description of
  intended behavior alone — the doc accurately describes the lifecycle logic, but says nothing
  about whether that logic is ever actually reached from live gameplay, which is exactly the gap
  this investigation found.
- `GoalKind` (AI strategic goals) and `QuestKind`/`ProjectKind.QUEST` (the quest system) are two
  separate, easily-conflated vocabularies sharing the same `entity.strategic.projects` dict and the
  same `ProjectState` base class — any future observability or scoring work touching "projects"
  must explicitly filter by type/kind, not assume homogeneity, per Finding 2's exact mistake.
