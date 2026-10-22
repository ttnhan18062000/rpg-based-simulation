---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY
tags: []
---

# test_plan - TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY

## Tests
`tests/integration/observability/test_an_escalated_need_is_never_refused_for_capacity_through_the_real_kernel.py` (real kernel, crowded_frontier seed 45, blacksmith 13 staged with three suspended projects and the inn beside it):
1. hunger past the onset at a full cap gets a hunger project and eats;
2. below the onset the cap still refuses;
3. one project per need kind, nothing evicted or abandoned (150 ticks);
4. an admitted need project that is not current survives both trims;
5. the gate-run blacksmith 13 replay (pins the current scoring, not the rule; named "...pins_current_scoring_not_the_rule" and citing TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95);
6. hunger and sleep switching every 12 ticks for 600 ticks never exceeds the cap plus two live projects (the per-kind bound).
`tests/unit/strategic/test_project_capacity_counts_live_projects.py`: the old test `test_an_entity_holding_max_live_projects_still_cannot_start_a_new_kind` (an entity at the cap can never start a new kind, at any need level) is split into a below-onset-refused test and an at-or-past-onset-admitted test, plus `live_projects_in_the_trim` tests (the exemption, and the pick rule: current else newest per kind). The expectation change was ruled by the designer (planner relay) with the step 2 ruling: an escalated need is admitted at a full cap.

## Other checks
tests/unit/strategic and tests/unit/ai pass (500); lint-imports 17 kept; import_contracts 17 kept; mypy_gate rc 0; mechanism-registry tests pass (scope pin 344 to 345, `escalated_need_wins` bound under `goal_hierarchy`). Full tests/unit serial on the step: 8442 passed, 12 failed, of which 9 are pre-existing SimQ grade anchors (also red on 7b1528861), the pin above (fixed), and two load-sensitive tests that pass when run alone.

## Proof Plan
Proof type: regression, through the real kernel, plus the paired run and V3 on 15 as the effect measurement. Test 1 fails without the change (no hunger project is made at 3 of 3, the entity starves); test 6 fails against the first, unbounded build (13 live projects).
