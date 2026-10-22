---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY
tags: []
---

# plan - TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY

## Plan
1. `src/ai/goals/escalation.py` `escalated_need_wins(entity, goal_kind)`: a hunger or fatigue goal at or past `need_is_pressing` (0.6 of its line: hunger 57, sleep debt 58.8) wins admission at a full cap. It lives in the `ai` layer because the import contracts forbid `systems` importing `engine`.
2. `src/systems/strategic_systems/intelligence.py`: the capacity check also reads `not escalated_need_wins(...)`.
3. `src/core/strategic.py` `NEED_PROJECT_KINDS` and `live_projects_in_the_trim(projects, current_project_id)`: ONE live hunger and ONE live sleep project (the current one of that kind, else the newest by `created_tick`) are outside both capacity trims; every other live need project counts and is trimmed like any project (cap plus two at most). Read by `DetourSuggestionSystem.enforce_bandwidth` and `CapacityEnforcementPhase`.
4. Real-kernel tests, the unit capacity test updated, docs (memo row 84 (2), SURV-07, Bible 04 sections 1 and 4, parity STRAT-286, divergence 2.137), the mechanism registry binding under `goal_hierarchy` and the scope pin (345).
5. Measure: V3 on all 15 gate runs, the standard paired run 23fbe0ecf to the step.

## Scope guards
Nothing is evicted, abandoned or resumed to make room. Suspended projects still count as live (divergence 2.77 kept); their expiry or resumption is TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK (after v1).

## Acceptance map
Hungry entity past the onset at a full cap gets a hunger project and eats (test 1); below the onset the cap refuses (test 2); one project per need kind, nothing evicted (test 3); an admitted need project that is not current survives both trims (test 4); the bs13 replay (test 5); hunger and sleep switching for 600 ticks never exceeds the cap plus two (test 6, the bound).
