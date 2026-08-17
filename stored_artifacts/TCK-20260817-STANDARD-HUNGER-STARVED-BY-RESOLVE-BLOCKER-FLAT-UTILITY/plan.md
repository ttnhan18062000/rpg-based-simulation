---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY
tags: [cognition, bug]
---

# Plan — TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY

## Approach
Per this repo's Strategic/Tactical Rule ("Do not solve strategic problems by stacking more
tactical goal scoring"), fix this at the strategic blocker-lifecycle layer, not by tweaking
`ResolveBlockerScorer`'s utility formula/value. Two changes, both required together (neither alone
is sufficient — see investigation.md's "Structural gap B"):

1. **`src/core/strategic.py`**: add `BlockerState.suppression_until_tick: int = 0`, mirroring
   `LeadState`'s existing, already-proven `suppression_until_tick` field exactly (same name, same
   semantics — "not eligible for consideration until this tick").
2. **`src/systems/strategic_systems/intelligence.py`**: add a `resolve_blocker` completion/timeout
   branch alongside the existing hunger/fatigue/harvesting/shopping checks
   (`evaluate_project_switch`'s "2. Project Abandonment" section). Timeout at 50 ticks since
   `project.created_tick`, matching this project kind's own creation-time
   `lock_until_tick=min(current_tick+10, current_tick+50)` ceiling (not an invented number — the
   project's own natural lifecycle already caps around this window). On timeout: abandon the
   project AND set `suppression_until_tick = current_tick + 100` on the specific blocker
   (extracted from `project.objectives[0].target`, which `ResolveBlockerScorer.score()` already
   populates with `str(blocker.id)`) — 100 ticks (2x the attempt window) gives other needs a real
   chance to win before the same blocker is reconsidered.
3. **`src/ai/goals/scorers.py`**: `ResolveBlockerScorer.score()` filters
   `entity.strategic.blockers` to exclude any blocker with `suppression_until_tick > state.tick`
   before picking `active_blockers[0]`.

## Why this closes the loop without touching the utility value
Once `resolve_blocker` times out and abandons, `current_project_id` clears. The goal-scoring
loop's ALREADY-EXISTING generic resumption path (`intelligence.py:1483-1491`, matches a fresh
`best_candidate.kind` against any existing SUSPENDED project of the same kind and auto-resumes it)
then gets a real chance to run on the next tick. Because the blocker is now suppressed,
`ResolveBlockerScorer` returns `utility=0.0` for it during the suppression window, so hunger (or
whatever else is pending) can actually win and either resume its suspended project or start fresh.

## Out of scope
- `ResolveBlockerScorer`'s own `utility=80.0` flat floor — already documented (parity ledger
  `STRAT-257` addendum) as an intentional, known-dominant design choice for an unrelated
  investigation; not touched.
- `DetourSuggestionSystem.suggest_detours()`'s lead-gating — confirmed unchanged/correct; the
  detour path simply doesn't apply when the entity has no leads yet, which is expected.
- Any change to blocker/lead unification (`ProjectKind`/`GoalKind` vocabulary split) — noted as a
  pre-existing, separately-tracked architectural item in `intelligence.py`'s own comments; out of
  scope here.
