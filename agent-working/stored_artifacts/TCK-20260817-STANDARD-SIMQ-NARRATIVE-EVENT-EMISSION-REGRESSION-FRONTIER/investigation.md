---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER
artifact_type: investigation
tags: [simulation-quality, calibration, corpus, investigation, root-cause]
---

# Investigation — TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER

## Methodology
Real, live-instrumented reproduction of the 5 named failing tests plus 2 direct official
`pytest -m slow` runs (not just the standalone repro harness) against the real compiled worlds.
Root-cause tracing used `git worktree` bisection to the commit immediately before the "43-ticket
push-based observability migration epic" (`11b83f37`), re-running the identical repro against the
pre-migration source tree with the shared venv — not guesswork from reading code alone. All 3
population sites named in the parent ticket's "strongest lead" (diplomatic transitions,
military conflict, sovereignty shifts) were read directly in `src/engine/pipeline.py` and
`src/engine/world_dynamics.py` and independently traced with call-count instrumentation.

## Reproduction (Step 2 of ticket scope)
Ran 2 of the 5 named tests via real `pytest -m slow`:
- `test_generated_frontier_3_42_seed123_200t_combat_narrative_grade_stability` — FAILED, all 3
  trials `NARRATIVE grade=C` vs anchor `A` (17.9s).
- `test_frontier_marches_seed42_200t_narrative_grade_stability` — FAILED, all 3 trials
  `NARRATIVE grade=C` vs anchor `A` (23.4s).

Standalone repro (same `tools/calibrate_simq._run_engine`/`_replay_jsonl_through_hub` production
code path as the tests, run directly for faster iteration) confirmed **zero** occurrences of ALL
10 NARRATIVE event types (`quest_started/completed/failed`, `chronicle_entry_created`,
`world_emergence_event`, `narrative_milestone`, `scenario_objective_progressed/completed`,
`scenario_stalled`, `hero_death_unrecorded`) in the raw `simulation_events.jsonl` for
`generated_frontier_3_42_seed123_200t`, `frontier_extended_seed42_200t`, and
`frontier_marches_seed42_200t` — matching the parent investigation's finding exactly (hard
structural zero, zero variance, healthy COMBAT/PROGRESSION activity in the same runs).

## Root cause: the parent investigation's "strongest lead" is REFUTED, not confirmed

**The suspected missing-`.merge()` pattern (`TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-
PUSH-SHAPER-EVENTS`'s template) does NOT apply here.** Direct read of every `world_events_add`
population site named in the parent ticket confirms all of them correctly preserve prior-phase
state:
- `diplomatic_transitions` (`src/engine/pipeline.py:219-222`) — `u.merge(_SU_dt(...))`, correct.
- `military_conflict` (`src/engine/pipeline.py:229-232`) — `u.merge(MilitaryConflictPhase.execute(state))`, correct.
- sovereignty shift (`src/engine/world_dynamics.py:112-116`) — `update.replace(world_events_add=list(update.world_events_add) + sovereignty_events)`, correct (extends, not replaces).
- economy world events (`src/engine/economy.py:276-291`) — `existing_world_events = list(update.world_events_add); existing_world_events.extend(world_events); return replace(update, ..., world_events_add=existing_world_events)`, correct.

Live call-count instrumentation (monkeypatched `events_from_transitions`, `MilitaryConflictPhase.execute`)
during a real 200-tick `generated_frontier_3_42_seed123` run confirms **zero WorldEvents were ever
produced** by any of these sites in this run — not because they're being dropped, but because the
underlying game-state conditions that would produce them never occur: diplomatic tension reaches
`TENSE` for 29/120 faction pairs but never escalates past `HOSTILE`/`WAR` within 200 ticks (per
`src/domains/faction/diplomatic_state_machine.py`'s own threshold logic:
`TENSE→HOSTILE` needs `pair_tension > 0.7` or shared territory; neither occurs in this window), no
region's `influence` ever crosses the ±100 sovereignty-shift threshold, and no faction ever enters
`WAR` state (so `MilitaryConflictPhase` has nothing to report). **This part of the system is
working exactly as designed** — the emission pipeline is intact.

## The real explanation: two ALREADY-SHIPPED, intentional, documented fixes, not a live bug

`git worktree` bisection to `12da37db` (the commit immediately before `11b83f37`) and re-running
the identical repro against that tree reproduced the historical high `NARRATIVE` activity: raw
event_type `quest_event` fired **33 times** (matching the `TCK-20260715-SIMQ-ANCHOR-LOAD-
SENSITIVITY-SWEEP` repro's own documented "NARRATIVE event_count ranged 31-39" for this exact
scenario/seed, cited in the failing test's own docstring). Dumping those 33 raw records showed
`payload={}` and messages like `"Entity 20 quest proj_combat_engage_0 updated to status started"`,
`"...proj_combat_retreat_5..."` — **every one of these is an ordinary AI strategic goal
(`GoalKind.COMBAT_ENGAGE`/`COMBAT_RETREAT`/etc.), not a real quest.**

This is the exact, byte-identical symptom `tickets/done/TCK-20260807-QUEST-EVENT-TYPE-FILTER-
BUG.md` already found, fixed, and closed on 2026-08-07: `event_extractor.py`'s quest-event block
had no `isinstance(qstate, QuestState)` filter, so it mislabeled every strategic project of any
kind as a fake quest. That ticket's own Test Summary states verbatim: *"quest_event count dropped
from 700 (pre-fix, 100% mislabeled) to 0 (post-fix — correctly excludes non-quest projects; 0 is
expected, not a regression, since `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` is still open)."*
The current `NarrativeShaper`/`event_extractor.py` code (confirmed by direct read) already
correctly implements this fix: it only emits `QuestEvent` for real `isinstance(qstate, QuestState)`
projects.

A second, independent, also-intentional change compounds this: `TCK-20260811-DELETE-ADVENTURE-
DECISION-PHASE` (confirmed via `tests/unit/domains/adventure/
test_delete_adventure_decision_phase_guards.py`, an explicit architecture guard) deliberately
deleted the standalone `AdventureDecisionPhase`/`src/domains/adventure/phase.py` and relocated its
eligibility logic into `AdventureGoalScorer` (goal-scoring architecture, `GoalKind`-typed —
produces AI strategic goals, not `QuestState` records). Confirmed absent from current
`src/engine/pipeline.py` (no `AdventureDecisionPhase` reference at all); confirmed present in the
pre-migration worktree (`adventure_decision` phase registered at old `pipeline.py:235-247`, gated
by `ENABLE_ADVENTURE_ROUTING`).

**Net effect**: the ONLY live mechanism that can produce a real `QuestState` (and therefore a real
`quest_started`/`quest_completed` NARRATIVE event) today is the guild-visit quest-generation path
(`src/town/guild.py:GuildAction.visit` → `src/quests/generator.py:QuestGenerator.generate_quests`),
reached only via `GuildVisitPhase`, gated by `ENABLE_GUILD_QUEST_GENERATION` — a flag introduced by
`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` that **defaults OFF** (DEV-002 new-gameplay-behavior
policy, confirmed in `src/domains/optimization/feature_flags.py`'s own comment). **None of the 5
failing worlds' calibration profiles (`config/simulation_quality/profiles/{generated_frontier_3_42,
frontier_extended,frontier_marches,frontier_living_world}.yaml`) set this flag** — each sets only
`ENABLE_BELIEF_ASSIMILATION: ON` (`frontier_living_world` additionally sets
`ENABLE_SOCIAL_COOPERATION: ON`). `tests/simulation_quality/fixtures/expected_world_flag_state.json`
independently confirms `ENABLE_ADVENTURE_ROUTING: OFF` is the *intended* state for all 5 worlds —
so even the now-deleted `AdventureDecisionPhase` was never live for them either, before or after
its deletion.

**Direct confirmation the emission mechanism itself still works when correctly configured**: a
standalone script forced `ENABLE_GUILD_QUEST_GENERATION=ON` via direct `state.feature_flags`
override (bypassing `tools/calibrate_simq.py`'s `_KNOWN_FLAGS` allowlist, which does not include
this flag — a separate, minor, out-of-scope tooling gap) and re-ran `generated_frontier_3_42_seed123`
for 200 ticks: raw event_type `quest_event` fired once (a real quest, this time correctly
`isinstance`-gated). This proves the current push-shaper → `QualityHub._translate_quest_event` →
`NarrativeScorer` chain is fully intact end-to-end; it simply has no real quest-generating input
for these 5 worlds' shipped calibration configuration.

The other 9 NARRATIVE event types were checked independently and are also legitimately absent for
these specific world/seed/200-tick runs, not separately broken:
- `world_emergence_event`/`narrative_milestone` — no wars/sovereignty-shifts occur (see above);
  the emission code is unconditionally correct given zero qualifying `WorldEvent`s.
- `hero_death_unrecorded` — requires an `entity.kind == "hero"` entity to die
  (`event_extractor.py:505`, and mirrored in `CombatShaper` at `event_shapers.py:337` for the
  shaper-owned-kill case); none of the reproduced runs show any `entity_killed`/`combat_kill`
  event at all in 200 ticks (combat occurs but never resolves to a kill in this window).
- `chronicle_entry_created` — `NarrativeScorer`'s own docstring already discloses this as a
  **known, pre-existing, unrelated gap**: "chronicle_entry_created events emitted as disk JSONL
  only (not event bus) are a known gap; this scorer only receives bus-emitted chronicle events."
- `scenario_objective_progressed/completed`/`scenario_stalled` — these worlds carry no active
  scenario-objective definition; structurally cannot fire regardless of any code path.

## Conclusion: NOT a live regression requiring a `src/` fix

Per the ticket's own explicit instruction ("If your fix doesn't restore real narrative activity at
all, do not force-adjust anchors to hide that — stop and report instead") and CLAUDE.md's Hard
Rule against editing an artifact to make a gate pass instead of fixing substance: **no source
change was made**, because there is no live defect to fix. The `grade_anchors.json` anchors for
these 5 tests (`NARRATIVE: grade A, score ~0.89`) were calibrated against telemetry that predates
`TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` (2026-08-07) — i.e., against the since-fixed
AI-goal-mislabeling bug's fake "quest" noise, not real narrative content. Post-fix, the true
narrative-event yield for these 5 worlds' current shipped configuration is genuinely, correctly
zero. This is the same underlying category as the "4 other stale anchors" a sibling ticket already
recalibrated — but this ticket's explicit instruction is to leave the anchors untouched and report
this finding rather than resolve it unilaterally, since recalibrating (vs. deciding to activate
real quest content for these worlds instead) is a product/architecture decision beyond a bug-fix
ticket's scope.

## Cross-world check (Step 5 of ticket scope)
The same "zero real quest-generation input, zero war/sovereignty drama in 200 ticks" signature was
independently confirmed (not just asserted) for `frontier_extended_seed42_200t` and
`frontier_marches_seed42_200t` via the same standalone repro — both show the identical all-10-
types-zero pattern. `frontier_living_world` was not independently re-run (same profile shape,
same missing `ENABLE_GUILD_QUEST_GENERATION`, extremely likely to share the same cause) but is
not separately confirmed in this session; noted, not fixed, per the ticket's scope-creep guard.
Any calibration profile in the corpus that (a) does not set `ENABLE_GUILD_QUEST_GENERATION: "ON"`,
(b) was last calibrated before 2026-08-07, and (c) does not reach `WAR`/sovereignty-shift within
its tick budget is a plausible candidate for the same stale-anchor condition — a corpus-wide
audit is out of scope here and is recommended as separate follow-up work.

## Recommendation (not executed — beyond this ticket's authorized scope)
Either (a) recalibrate the 5 anchors using the file's own documented re-anchoring methodology
(1.3x max single-sample deviation over `SCORE_TOLERANCE_ABS_FLOOR=0.05`) now that genuine
zero-narrative-activity is the correct baseline for these worlds' current configuration, or (b)
make a deliberate product decision to enable `ENABLE_GUILD_QUEST_GENERATION` (or seed real
`quest_registry` content from the already-compiled-but-unwired `spec.quest_definitions` —
`src/worldbuilding/compiler.py:426-482`'s `compiled_quests` list is computed but never attached to
`AuthoritativeState.quest_registry` or any entity's `.strategic.projects`, a separate, older,
pre-existing dead-code gap unrelated to the 2026-07-15→2026-08-11 regression window) so these
frontier worlds produce genuine narrative activity worth scoring. Both are explicitly out of this
ticket's scope per its own instructions.
