---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY
phase: done
date: 2026-08-17
tags: [cognition, bug]
---

# TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY

## Title
A low-severity, unresolvable blocker can permanently starve a hunger project — real strategic
interruption-resistance/blocker-lifecycle gap, not a regression

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on the "Integration" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496):
`tests/integration/scenarios/test_hunger_satiation.py::test_hunger_satiation_resolves_in_food_world`
— no HUNGER project reaches COMPLETED status in 400 ticks.

Confirmed via live instrumentation (fully deterministic, seed=42): an entity picks up a transient
movement-oscillation "access" blocker (congestion) near a settlement boundary. `ResolveBlockerScorer`
returns a flat, un-decaying `utility=80.0` for ANY unresolved blocker, winning the goal-arbitration
switch over the entity's suspended hunger project. `resolve_blocker` — unlike every other GoalKind
with a project completion condition (hunger/fatigue/harvesting/shopping) — had no completion
condition at all, so once the entity reaches its unreachable fallback target it just idles
forever, permanently occupying `current_project_id` and starving hunger for the rest of the run.
Confirmed unrelated to any recent commit (both `ResolveBlockerScorer` and the detour lead-gating
are unchanged since before `29d78798`) — a genuine, pre-existing latent bug.

## Scope
Per this repo's Strategic/Tactical Rule (fix at the strategic blocker-lifecycle layer, not by
tweaking the scorer's utility formula):
- `src/core/strategic.py`: `BlockerState.suppression_until_tick: int = 0`, mirroring `LeadState`'s
  existing, already-proven identical field.
- `src/systems/strategic_systems/intelligence.py`: a `resolve_blocker` timeout/abandon branch
  (50 ticks, matching this project kind's own creation-time `lock_until_tick` ceiling), setting
  `suppression_until_tick = current_tick + 100` on the specific blocker it failed to resolve.
- `src/ai/goals/scorers.py`: `ResolveBlockerScorer.score()` excludes suppressed blockers.

## Out of Scope
- `ResolveBlockerScorer`'s own `utility=80.0` flat floor — already documented (parity ledger
  `STRAT-257` addendum) as intentional/known-dominant for an unrelated investigation; unchanged.
- `DetourSuggestionSystem.suggest_detours()`'s lead-gating — confirmed correct, not touched.
- `ProjectKind`/`GoalKind` vocabulary unification — a separate, pre-existing, already-noted
  architectural item; out of scope.
- Any other ticket in this batch.

## Acceptance Criteria
- [x] `test_hunger_satiation_resolves_in_food_world` passes.
- [x] A bare timeout alone is insufficient and is not what was shipped — blocker suppression
      (closing the abandon-recreate loop) is also required and tested separately.
- [x] No regression across the strategic/goals/integration-scenario test surface.
- [x] Parity ledger entry added (`STRAT-258`), since this is a real engine behavior change under
      `docs/mechanics/04_strategic_cognition.md`'s domain.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
- `docs/parity_ledger/strategic_cognition.yaml` (new entry `STRAT-258`)

## Related Stored Artifacts
`stored_artifacts/TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY/`

## Related Code Areas
- `src/core/strategic.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/ai/goals/scorers.py`
- `tests/unit/strategic/test_strategic_detour_ph6.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Discovered while designing the fix (not in the original CI-log-driven investigation): blocker-
resolution + suspended-project resumption already exists as a fully generic mechanism
(`intelligence.py:1483-1491` — any winning `best_candidate.kind` matching an existing SUSPENDED
project's kind auto-resumes it), so the real fix only needed to (a) make `resolve_blocker`
relinquish `current_project_id` on a timeout and (b) stop the same blocker from immediately
re-winning at its flat utility right after — no new resumption logic needed, and no change to the
scorer's own utility value. Added 2 focused unit tests covering both halves of the fix separately
(timeout+suppression-application, and the scorer's suppression-aware filtering across all 3 states:
not-yet-suppressed, suppressed, suppression-elapsed), since a bare timeout alone would have looked
like a fix while still leaving the starvation bug fully intact.

## Test Summary
- `pytest tests/integration/scenarios/test_hunger_satiation.py -q`: 1 passed (was failing).
- `pytest tests/unit/strategic/test_strategic_detour_ph6.py -v`: 3 passed (1 existing + 2 new).
- `pytest tests/unit/strategic tests/unit/ai/goals tests/strategic tests/integration/scenarios
  tests/integration/pipeline/test_strategic_cadence.py -m "not slow and not extra_slow" -q`: 440
  passed, 1 skipped, 24 deselected — no regressions.

## Files Changed
- `src/core/strategic.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/ai/goals/scorers.py`
- `tests/unit/strategic/test_strategic_detour_ph6.py`
- `docs/parity_ledger/strategic_cognition.yaml`

## Completion Summary
Fixed a real, pre-existing strategic interruption-resistance gap: a low-severity, unresolvable
blocker could permanently starve a biological-need project, because `resolve_blocker` was the only
GoalKind with no completion condition, and even a bare timeout would have looped forever against
the scorer's own flat utility. Fixed at the strategic blocker-lifecycle layer (a new
`BlockerState.suppression_until_tick` field, mirroring an already-proven `LeadState` pattern) per
this repo's Strategic/Tactical Rule, not by adjusting tactical scoring. Documented in the parity
ledger since this is a real, durable engine behavior change.
