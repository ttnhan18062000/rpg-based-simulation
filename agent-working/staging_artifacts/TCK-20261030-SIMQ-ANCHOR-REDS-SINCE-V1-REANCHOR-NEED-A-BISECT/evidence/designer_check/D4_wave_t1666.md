## Check 2: the parent's t1666 wave, entities 1 and 14, urban_political s42 2000t (D4 probe logs)

### parent a25619971
| tick | entity | position | hp | alive | work / action | nav target | movement mode | faction | project | group |
|---|---|---|---|---|---|---|---|---|---|---|
| 1640 | 1 | [42, 32] | 100 | True | ENTITY_ACT None | [40.0, 31.0] | WANDER | town_council | proj_hunger_1399 | None |
| 1640 | 14 | [58.0, 28.0] | 70 | True | ENTITY_ACT REST | [58.0, 27.0] | REGROUP | bandit_company | proj_fatigue_1426 | None |
| 1660 | 1 | [43, 32] | 100 | True | ENTITY_MOVE None | [47.0, 28.0] | INTERCEPT | town_council | proj_hunger_1399 | None |
| 1660 | 14 | [48.0, 28.0] | 70 | True | ENTITY_ACT None | [25.0, 25.0] | WANDER | bandit_company | proj_resolve_blocker_1646 | None |
| 1665 | 1 | [44, 29] | 100 | True | ENTITY_ACT None | [40.0, 31.0] | INTERCEPT | town_council | proj_hunger_1399 | 10020 |
| 1665 | 14 | [44.0, 28.0] | 70 | True | ENTITY_ACT None | [25.0, 25.0] | WANDER | bandit_company | proj_resolve_blocker_1646 | None |
| 1666 | 1 | [44, 30] | 83 | True | ENTITY_ACT None | [45.0, 29.0] | REGROUP | town_council |  | None |
| 1666 | 14 | [44.0, 27.0] | 69 | True | ENTITY_ACT None | [25.0, 25.0] | WANDER | bandit_company | proj_resolve_blocker_1646 | None |
| 1667 | 1 | [44, 29] | 83 | True | ENTITY_ACT None | [45.0, 30.0] | REGROUP | town_council |  | 10020 |
| 1667 | 14 | [44.0, 28.0] | 69 | True | ENTITY_MOVE None | [44, 30] | PURSUE | bandit_company | proj_combat_engage_1666 | None |
| 1670 | 1 | [45, 28] | 49 | True | ENTITY_MOVE None | [44.0, 28.0] | PURSUE | town_council |  | None |
| 1670 | 14 | [44.0, 28.0] | 69 | True | ENTITY_ACT ATTACK | [45.0, 28.0] | REGROUP | bandit_company |  | None |

bandit_company/town_council pair tension and diplomatic state (tick, tension, state): [(400, 0.33, 'None'), (425, 0.42, 'TENSE'), (500, 0.51, 'TENSE'), (1000, 0.51, 'TENSE'), (1500, 0.51, 'TENSE'), (1666, 0.51, 'TENSE')]
entity 1: first tick not alive [1717]
entity 14: first tick not alive [1809]

### d914bace7
| tick | entity | position | hp | alive | work / action | nav target | movement mode | faction | project | group |
|---|---|---|---|---|---|---|---|---|---|---|
| 1640 | 1 | [42, 32] | 100 | True | ENTITY_ACT None | [40.0, 31.0] | WANDER | town_council | proj_resolve_blocker_1639 | 10022 |
| 1640 | 14 | [17, 32] | 0 | False | ENTITY_ACT ATTACK | [17.0, 32.0] | REGROUP | bandit_company | proj_combat_engage_406 | None |
| 1660 | 1 | [30, 30] | 100 | True | ENTITY_ACT None | [25.0, 25.0] | WANDER | town_council | proj_resolve_blocker_1639 | 10022 |
| 1660 | 14 | [17, 32] | 0 | False | ENTITY_ACT ATTACK | [17.0, 32.0] | REGROUP | bandit_company | proj_combat_engage_406 | None |
| 1665 | 1 | [28, 27] | 100 | True | ENTITY_ACT None | [25.0, 25.0] | WANDER | town_council | proj_resolve_blocker_1639 | 10022 |
| 1665 | 14 | [17, 32] | 0 | False | ENTITY_ACT ATTACK | [17.0, 32.0] | REGROUP | bandit_company | proj_combat_engage_406 | None |
| 1666 | 1 | [27, 27] | 100 | True | ENTITY_ACT None | [25.0, 25.0] | WANDER | town_council | proj_resolve_blocker_1639 | 10022 |
| 1666 | 14 | [17, 32] | 0 | False | ENTITY_ACT ATTACK | [17.0, 32.0] | REGROUP | bandit_company | proj_combat_engage_406 | None |
| 1667 | 1 | [27, 26] | 100 | True | ENTITY_ACT None | [25.0, 25.0] | WANDER | town_council | proj_resolve_blocker_1639 | 10022 |
| 1667 | 14 | [17, 32] | 0 | False | ENTITY_ACT ATTACK | [17.0, 32.0] | REGROUP | bandit_company | proj_combat_engage_406 | None |
| 1670 | 1 | [26, 26] | 100 | True | ENTITY_ACT None | [25.0, 25.0] | WANDER | town_council | proj_resolve_blocker_1639 | 10022 |
| 1670 | 14 | [17, 32] | 0 | False | ENTITY_ACT ATTACK | [17.0, 32.0] | REGROUP | bandit_company | proj_combat_engage_406 | None |

bandit_company/town_council pair tension and diplomatic state (tick, tension, state): [(400, 0.26, 'None'), (425, 0.27, 'None'), (500, 0.31, 'None'), (1000, 0.31, 'None'), (1500, 0.31, 'None'), (1666, 0.31, 'None')]
entity 1: first tick not alive none
entity 14: first tick not alive [452]

Events (simulation_events.jsonl, sweep run dirs): parent t1666 combat_initiated attacker 14 on entity 1 (OPPORTUNITY_ATTACK, both directions, outcome CAUGHT_FLEEING), t1669 world_emergence_event COMBAT_LOSS subject 1; entity_killed in the parent: 160 (e20 by 15), 172 (e18 by 15), 368, 425, 450, 1741 (e25 by 14), 1809 (e14 by 2); entity_killed at d914bace7: 160 (e20 by 15), 242 (e15 by 24), 400 (e12 by 14), 452 (e14 by 8).

## Reading
- Engagement: entity 14 (bandit_company GUARD, hp 70, project proj_resolve_blocker_1646) walks west and meets entity 1 (town_council WORKER, hp 100, project proj_hunger_1399, INTERCEPT) at (44,28)/(44,29) on t1665; they trade OPPORTUNITY_ATTACKs at t1666 (entity 1 has just been caught fleeing). That starts the parent's second wave (kills at t1741 and t1809, world_emergence COMBAT_LOSS events).
- Preconditions shown at the parent: both alive and in the same place; bandit_company/town_council diplomatic state TENSE since t417 (tension 0.42 at t425, 0.51 from t450).
- At d914bace7: entity 14 is dead since t452 (killed by entity 8; its hp is 0 and it is not alive from t452), so the pair cannot meet; entity 1 is alive and idle at (27,27) in group 10022; pair tension stays 0.31 and the diplomatic state is never TENSE.
- Shown: both preconditions (entity 14 alive; tension above the line) are absent at d914bace7, so it does not fire. Not shown: why entity 14 dies at t452 in d914bace7 (killer entity 8) and not in the parent (it survives to t1809); that is one more trajectory split after the t42 retreat, not traced here. Not shown: that the parent's hostility needs the TENSE state (hostility is catalog-driven, src/content_semantics/faction.py are_entities_hostile; the TENSE state is present in the parent and absent at d914bace7, so it is a co-occurring precondition, not a demonstrated requirement).

