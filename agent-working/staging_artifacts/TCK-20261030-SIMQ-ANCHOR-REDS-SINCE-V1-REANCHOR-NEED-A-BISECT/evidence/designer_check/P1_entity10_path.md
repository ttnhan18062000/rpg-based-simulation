## Check 3: P1 entity 10, t110, d914bace7 (probe5, apply_modifiers and evaluate_project_switch logged)

apply_modifiers raw top scores: [['GoalKind.COMBAT_RETREAT', 139.9972], ['GoalKind.RESOLVE_BLOCKER', 80.0], ['GoalKind.COMBAT_ENGAGE', 70.3891], ['GoalKind.RECOVER', 63.3333], ['GoalKind.TOWN_RETURN', 58.0]]
apply_modifiers modified top scores: [['GoalKind.COMBAT_RETREAT', 121.8165], ['GoalKind.RESOLVE_BLOCKER', 100.7388], ['GoalKind.COMBAT_ENGAGE', 79.5302], ['GoalKind.RECOVER', 63.3333], ['GoalKind.TOWN_RETURN', 58.0]]
entity 10 personality: PersonalityComponent(greed=0.3206508208367447, bravery=0.25972853342346286, sociability=0.7545174442477757, industry=0.8641151292294864) | 9 unresolved social blockers (severity 0.8, subject suitable_partner)
evaluate_project_switch: {'t': 110, 'candidate': 'proj_combat_retreat_110', 'cand_score': 121.81654636033515, 'current': None, 'current_status': None, 'current_score': None, 'lock_until': None, 'result_current_project_id_set': 'proj_combat_retreat_110', 'switched': True}

## Reading
The choice is the ordinary one, with no preemption or bypass. Path at tick 110 (d914bace7 line numbers):
1. `src/ai/goals/scorers.py:238-239`: CombatRetreatScorer applies `retreat_pull` only while `acting_threat_to` holds (raw 88.273 to 139.997).
2. `src/ai/score_modifiers.py:32-68` (ScoreModifierSystem.apply_modifiers: personality bias at lines 36-37, life stage, boredom, learning bias and blocker terms; I did not isolate which term gives each factor): COMBAT_RETREAT x0.870 (139.997 to 121.817), RESOLVE_BLOCKER x1.259 (80.0 to 100.739).
3. `src/systems/strategic_systems/intelligence.py:1586-1593`: the modified list is sorted by utility and the first entry at or above 20 is taken: COMBAT_RETREAT 121.817 beats RESOLVE_BLOCKER 100.739.
4. `intelligence.py:1776` evaluate_project_switch with no current project (`intelligence.py:1072`, `if not current_id`): the candidate is adopted at once, so there is no interruption-resistance or lock test.
Why the parent differs: the parent's raw retreat is 88.273 (no pull). With the same modifier factor (computed, not run: 88.273 x 0.870 = 76.8) it stays below RESOLVE_BLOCKER's 100.739, so the parent keeps resolve_blocker. The raw order (retreat 88.27 above resolve_blocker 80) is what hid this: the modifiers reverse it in the parent and not at d914bace7.
Whether this "fires on retreat_pull alone": the only difference between the two runs is the pull's +51.7 on the raw score, and the pull itself is gated on an acting hostile (`acting_threat_to`); the arbiter has no separate retreat path. It is a score-order change in the normal comparison, not a preemption that bypasses the score. My earlier README line that the project choice is not plain maximum score was wrong: it is plain maximum of the MODIFIED scores; the raw scores I compared were before ScoreModifierSystem.

