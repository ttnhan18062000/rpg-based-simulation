---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY
tags: [cognition, bug]
---

# Investigation — TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY

## Failing test
`tests/integration/scenarios/test_hunger_satiation.py::test_hunger_satiation_resolves_in_food_world`
— one of the 5 real Integration-job CI failures (real CI run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496): no HUNGER
project reaches COMPLETED status in 400 ticks.

## Root cause chain (fully deterministic, seed=42, traced via live instrumentation)
1. Entity walks to the tavern and eats once at tick 19 (hunger 61.9→22.0 — just short of the
   20.0 completion threshold, `intelligence.py:1361`).
2. It then oscillates between two tiles at the tavern's interaction boundary
   (`MovementMode.WANDER` jitter), tripping `entity.navigation.oscillation_count >= 3` →
   `infer_blockers()` adds a `blocker_congestion` (kind="access", subject="congestion" — not
   parseable coordinates).
3. `DetourSuggestionSystem.suggest_detours()` requires `usable_leads`; a fresh entity has none, so
   it returns `[]` — the detour path never fires.
4. Falls through to generic goal-scoring: `ResolveBlockerScorer.score()`
   (`src/ai/goals/scorers.py`) returns a flat, un-decaying `utility=80.0` for ANY unresolved
   blocker regardless of severity/age, spawning `proj_resolve_blocker_N` (`GoalKind.RESOLVE_BLOCKER`),
   which wins the switch over the suspended hunger project.
5. **Structural gap A**: unlike hunger/fatigue/harvesting/shopping (`intelligence.py:1358-1378`),
   `resolve_blocker` had NO completion condition at all — once the entity reaches its fallback
   target (`state.town_center`, since `blocker.subject="congestion"` isn't parseable), it just
   idles forever. `proj_resolve_blocker_N` stays ACTIVE permanently, occupying
   `current_project_id`.
6. **Structural gap B** (found while designing the fix, not in the original investigation):
   blocker-resolution + suspended-project resumption already exists as a GENERIC mechanism
   (`intelligence.py:1483-1491` — any `best_candidate.kind` matching an existing SUSPENDED
   project's kind auto-resumes it), triggered whenever the goal-scoring loop gets to pick a fresh
   `best_candidate`. But `resolve_blocker` never relinquishes `current_project_id` (gap A), so
   this generic resumption path never gets a chance to run. Even a bare timeout/abandon (closing
   gap A alone) is insufficient: `ResolveBlockerScorer`'s utility is flat and non-decaying, so an
   unsuppressed blocker would immediately re-win the very next scoring pass and recreate an
   identical project — an infinite abandon-recreate loop that STILL never lets hunger (rising only
   +0.1/tick via natural decay) win, since 80.0 flat >> hunger's slowly-rising utility.

## Confirmed NOT a regression
Diffed `ResolveBlockerScorer.score()` and `DetourSuggestionSystem.suggest_detours()`'s lead-gating
against pre-squash `6e25d4f2` (before commit `29d78798`) — both unchanged. This is latent,
pre-existing behavior, not something introduced this session or by `29d78798`.

## Existing precedent found (informed the fix design)
`LeadState` (`src/core/strategic.py`) already has an almost-identical pattern for a structurally
similar problem: `failure_count: int = 0` and `suppression_until_tick: int = 0`, used to stop a
repeatedly-failing lead from being retried indefinitely. `BlockerState` had no equivalent field.

## Related, already-documented context
`ResolveBlockerScorer`'s flat `utility=80.0` was already known and documented (parity ledger
`STRAT-257`'s addendum, `docs/mechanics/04_strategic_cognition.md`) as "structurally dominant"
over `AdventureGoalScorer` in an unrelated tier-5-competition investigation
(`TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`) — but that investigation's own
scope never covered `ResolveBlockerScorer`'s own permanent-starvation failure mode; only that it
dominates other scorers when it wins.
