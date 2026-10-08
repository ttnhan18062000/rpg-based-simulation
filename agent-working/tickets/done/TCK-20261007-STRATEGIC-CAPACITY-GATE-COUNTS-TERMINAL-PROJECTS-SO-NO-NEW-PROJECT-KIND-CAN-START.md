---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START
phase: done
date: 2026-10-07
tags: [strategy, cognition, bug]
---

# TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START

## Title
The strategic capacity gate counts finished projects, so an entity that has held `max_active_projects` projects can never start a new kind of project

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while diagnosing `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`. The capacity gate (`evaluate_strategic_intent`, `at_capacity = len(strat.projects) >= max_active_projects`) counted every stored project, `COMPLETED` and `ABANDONED` ones included, and nothing removes those. `DetourSuggestionSystem.enforce_bandwidth` (`len > max`) and `CapacityEnforcementPhase` (lowest score first) used the same count with a different comparison, and `GuildNeedScorer` and `GuildAction.visit` read it as spare capacity. An entity that had ever held `max_active_projects` (3) projects in any status could never start a project of a kind it had no record of: the fatigue goal won 1 to 5 evaluations per 100 ticks from t about 400 and was dropped (the winner held 3 of 3 stored projects, all finished; `evaluate_project_switch` was never called for it). Planner ruling 2026-10-07: fix now, one shared predicate for the gate and the trim; the hunger target is held for the designer (SURV-06).

## Scope
- One predicate for which projects count (`is_live_project`, `live_projects`, `has_project_capacity` in `src/core/strategic.py`): `ACTIVE` and `SUSPENDED`.
- The gate, `enforce_bandwidth`, `CapacityEnforcementPhase`, `GuildNeedScorer` and `GuildAction.visit` all read it.
- Tests that fail with each old behaviour; divergence 2.77, the Bible 04 section 4 note and parity STRAT-278; a before and after measurement on one tree.

## Out of Scope
- Hunger's target (no tavern exists in any world): held for the designer (SURV-06).
- The downstream breaks after a fatigue project starts (the rest path, movement to the building, the gold check): `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`.
- Pruning finished projects out of `StrategicComponent.projects` (they still accumulate).

## Acceptance Criteria
- [x] An entity holding only finished projects can start a project of a new kind (a fatigue project, in the test and in the corpus)
- [x] An entity holding `max_active_projects` live projects still cannot start a new kind
- [x] The gate and the trim use one shared predicate (the `>=` against `>` mismatch is gone); a trim never evicts a live project for a finished record
- [x] Measured before and after on one tree: project-kind wins, projects started, eat and sleep events, deaths by cause (divergence 2.77); the campaign tests pass
- [x] Filed `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100` carrying the full diagnosis, open

## Related Tickets
- TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100 (umbrella, open)
- TCK-20260527-COG-CAPACITY-ENFORCEMENT (introduced the trim)

## Related Docs
- `docs/guidelines/intentional_divergences.md` 2.77; `docs/mechanics/04_strategic_cognition.md` section 4

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START/`

## Related Code Areas
- `src/core/strategic.py`, `src/systems/strategic_systems/intelligence.py`, `src/systems/strategic_systems/detour.py`, `src/engine/pipeline_phases/capacity_enforcement.py`, `src/ai/goals/scorers.py`, `src/town/guild.py`

## Assumptions / Open Questions
- `SUSPENDED` counts as live (it can be resumed); `COMPLETED` and `ABANDONED` do not. Finished records are left in place, so a goal whose kind already has a record still passes the gate as before.

## Implementation Notes
- `src/core/strategic.py`: `LIVE_PROJECT_STATUSES`, `is_live_project`, `live_projects`, `has_project_capacity`.
- `intelligence.py`: `at_capacity = not has_project_capacity(...)`. `detour.py`: the trim sorts and trims only live projects. `capacity_enforcement.py`: trims `live_projects(all_projects)`, so a new project is not dropped for finished records with higher scores. `scorers.py` and `guild.py`: spare capacity is live capacity.

## Test Summary
- New `tests/unit/strategic/test_project_capacity_counts_live_projects.py` (16 tests). Disabling controls: the old gate fails the finished-only test, the old trim fails two trim tests, the old phase fails the phase test.
- Corpus before and after (see divergence 2.77): fatigue projects started 0 / 0 to 4 / 0; eat and sleep 0 to 0; STARVATION 30 / 36 to 30 / 34. The fix does not stop the starvation.
- CI directory lists, run locally with `-m "not slow and not extra_slow"` on the branch: unit-core 1839 passed, 1 skipped; unit-domain 1467 passed, 1 skipped; integration plus `tests/integrity` plus `tests/architecture` 1225 passed, 7 skipped, 1 xfailed (the known strict deliberate-attack xfail); unit-infra (domains, observability, rendering, lab, lab_agent, api, cli, views, perf, entity, entities, cognition, docs, certification, tools and the two loose files) 3330 passed, 1 skipped. `tests/integration/campaigns` (slow, outside those lists): 28 passed, 1 xfailed (the deliberate-attack test); the campaign episode is unchanged by this fix (cooperation share 0.4962 and 0.3562, deliberate attack attempts 2 and 2, seeds 42 and 1337). Not run locally: the full Tools job's remaining files and the slow suites.
- Gates (scratch venv): code-health ratchet 0 new, 0 worse (an inline comprehension in `enforce_bandwidth` first raised its cognitive complexity from 20 to 22; replaced by the shared `live_projects` helper); parity-ledger schema 0 rose, 0 new; mypy baseline nothing in the changed files. CI is the first real run.

## Files Changed
`src/core/strategic.py`, `src/systems/strategic_systems/intelligence.py`, `src/systems/strategic_systems/detour.py`, `src/engine/pipeline_phases/capacity_enforcement.py`, `src/ai/goals/scorers.py`, `src/town/guild.py`; the new test; `docs/guidelines/intentional_divergences.md`, `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`; this ticket, its artifacts and `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`.

## Completion Summary
Finished projects no longer count against `max_active_projects`; the gate, the trim, the enforcement phase and the guild readers share one predicate. Entities that used to be locked out of new project kinds can now start them (fatigue projects appear). Survival is unchanged: eat and sleep stay at 0, because the hunger goal has no target and the rest path is a separate defect (`TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`).
