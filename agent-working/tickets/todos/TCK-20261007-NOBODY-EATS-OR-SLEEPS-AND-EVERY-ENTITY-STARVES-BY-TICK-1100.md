---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100
phase: open
date: 2026-10-07
tags: [strategy, cognition, bug]
---

# TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100

## Title
Nobody eats or sleeps in 2000 ticks and every entity starves between tick 950 and tick 1100 (a never-worked defect, a chain of breaks)

## Status
INPROGRESS

## Tier
epic

## Type
bug

## Priority
P1

## Request Summary
Measured 2026-10-07 on main `f8f1b69fd` / `cc3f00a11` (seed 42, `audit_mode`, budget off, `LocalSequentialExecutor`, each run twice with identical results, `frontier_living_world` and `crowded_frontier`): eat completions = 0 and sleep completions = 0 in every 100-tick bucket of 2000 ticks (a completion is a live entity's hunger or sleep debt dropping between ticks). Mean hunger is exactly t/10, so the 95 starvation line (`apply.py:100`) is reached at about t=950. STARVATION is 36 of 51 deaths in `frontier_living_world` and 30 of 39 in `crowded_frontier`; everyone alive at t=900 is dead by t=1100 (alive 0 at t=1100 and t=1200), including undead (catalog hunger none). A few new spawns appear from t about 1300 and have not eaten by t=2000. Eating has never worked in any compiled corpus world that can be probed: eat is already 0 at `6e25d4f28` (2026-07-02, the earliest commit where these worlds compile) and at `29d78798a` (2026-08-14); commits before 07-02 cannot load the worlds. So this is a never-worked defect, not a regression. Whether it explains the `behavioral_5k` alive collapse (13.3 to 5.5) is unverified: it depends on whether that bench's horizon passes tick about 950.

## The chain (file:line, measured)
1. **Hunger has no target.** `EatScorer` (`src/ai/goals/scorers.py:60-74`) targets only the nearest `tavern`. None of the 24 worlds has one (buildings: town_hall, shop, blacksmith, inn, healer_hut, mine_entrance, watchtower; `BuildingRegistry` has no TAVERN template, `src/town/buildings.py:17-24`; only `src/perf/scenarios.py:410` builds one). The arbiter skips any goal without a target (`intelligence.py` about 1593-1596). Hunger goals with utility >= 20 and no target: 145 of 145 at t<=300 and 100% in every bucket to t=1000. HUNGER wins 0 times. **Held for the designer (SURV-06, which sustenance paths a humanoid has).**
2. **The capacity gate counted finished projects** (fixed by `TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START`): fatigue won 1 to 5 evaluations per 100 ticks from t about 400 and was dropped because the winner held 3 of 3 stored projects, all `COMPLETED` or `ABANDONED`.
3. **After break 2 is fixed, fatigue projects start but nobody rests** (measured on the fix tree, `crowded_frontier`, 700 ticks): entities now walk to the inn (entity 31: inn distance 17 at t=414 down to 1 at t=434) and hold a fatigue project, but `REST` is decided only twice in 700 ticks (`tactical.decided.REST` 1 in t 500-600 and 1 in t 600-700, both legal), the fatigue project is replaced by `resolve_blocker` after about 10 to 20 ticks next to the inn (entity 31 at t=454, entity 32 at t=513, entity 3 at t=542), and no sleep debt ever drops. Two candidate causes, read from code and not yet traced: (a) `CoreActions.execute_survival` `REST` (`src/engine/domain/core_actions.py:45-52`) changes only `rest_pressure` (`-30`), not `sleep_debt`; the `SLEEP` action (`-20` sleep debt) is the one that reduces it; (b) the town path (`src/engine/town_resolution.py:100-112`) reduces sleep debt (`-5`) and charges 10 gold only when the entity stands ON the inn tile (`building_tiles` keyed by the tile, `building_type in ("inn","home")`), but the tactical dispatch fires at distance <= 1 (adjacent), so it may never be on the tile.
3b. **Why `REST` is decided so rarely beside the inn** (traced 2026-10-07, fixed by `TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED`): the walk targets the inn's own tile, which is in `blocked_tiles`; beside it `resolve_move` rejected the step (`path_not_found`) and its orthogonal sidestep moved the entity to distance 2, and the planner moved it back, so it alternated between distance 1 and 2 every tick. The tactical building branch dispatches only at `dist <= 1.0` on a brain tick (every 10 ticks) and sampled distance 2. After the fix (arrival ends the walk) `REST` decisions in frontier_living_world go from 0 to 34, but sleep debt still never drops: `CoreActions` REST changes only `rest_pressure`, and the town path in `town_resolution.py:100-112` needs the entity ON the building tile while `state.building_tiles` is empty in every compiled world (building footprints are in `blocked_tiles`), so it cannot match. Both are Lane B's. The fatigue project is also replaced by a flat-80 `resolve_blocker` (95.3 after modifiers, `scorers.py:205-248`) after its 10-tick lock, because the project's stored score (its creation-time utility) is never refreshed (planner ruling: refresh it, engineering) and a standing need cannot outrank a flat-80 goal (a rule question, with the designer).
3c. **The stale-score half of the replacement is fixed** (`TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE`): the switch comparison now sees the current project's live utility, so a project no longer replaces itself with a same-kind duplicate (16 and 20 such switches become 0 and 0). It does not keep the fatigue project: stored 50.5 against live 52.5 to 53.5 is a small gap, and the flat-80 `resolve_blocker` (95.3 after modifiers) still outranks a fatigue need of about 52, so the project is still replaced after its 10-tick lock. Whether a standing biological need may outrank a flat-80 goal is the rule question with the designer; the scorer magnitudes are unchanged.
4. **Hunger even with a tavern and capacity fixed** (counterfactual, probe monkeypatches, `crowded_frontier`, 1100 ticks): tavern alone 0 eats; capacity alone 0 eats; both 9 eat events (7 in t 750-1000, 2 in t 1000-1100), 0 sleep, 27 of 30 starved. So hunger has more breaks downstream (movement to the building, the gold check at `town_resolution.py:114-119` which charges 5 gold and needs the entity on a town tile, the same project-replacement interruption). Not traced.

## Scope
- Track the children: the capacity gate (done, `TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START`), hunger's target (designer ruling SURV-06 first), the rest path and project interruption (break 3), the downstream hunger breaks (break 4).
- Re-run the funnel (`funnel.py`-style: goal scores, projects started, tactical survival decisions, legality, `execute_survival`, state change) after each fix to find the next break.

## Out of Scope
- Tuning hunger or sleep rates; adding taverns or a targetless eat fallback before the SURV-06 ruling.

## Acceptance Criteria
- [ ] In `frontier_living_world` and `crowded_frontier` (seed 42, 2000 ticks, `audit_mode`) entities eat and sleep: eat and sleep completions > 0 in the buckets after the thresholds are crossed
- [ ] STARVATION is no longer the majority cause of death, and the population does not go extinct by t=1100
- [ ] The `behavioral_5k` alive collapse is re-measured and its horizon against tick about 950 is stated

## Related Tickets
- TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START (done: break 2)
- TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES (every alive entity has hunger exactly t/10 at t=500)
- TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS (the decision-core epic)

## Related Docs
- `docs/world_rules/life-body/survival-needs.md` (SURV-02, SURV-06); `docs/mechanics/04_strategic_cognition.md`; `docs/guidelines/intentional_divergences.md` 2.77

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START/investigation.md`

## Related Code Areas
- `src/ai/goals/scorers.py`, `src/systems/strategic_systems/intelligence.py`, `src/engine/tactical.py` (building dispatch at about 303-325), `src/engine/town_resolution.py`, `src/engine/domain/core_actions.py`, `src/engine/apply.py:90-91`

## Assumptions / Open Questions
- Measured with the probe's state-difference definition of "eat" and "sleep": it counts completed state changes, not attempted actions.
- Open: how the pre-2026-07-02 path let entities eat; why only 9 eat events with both breaks lifted; whether `REST` is meant to reduce sleep debt.

## Implementation Notes
Diagnosis only so far; the first fix is `TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START`.

## Test Summary
None yet.

## Files Changed
None yet.

## Completion Summary
None yet.
