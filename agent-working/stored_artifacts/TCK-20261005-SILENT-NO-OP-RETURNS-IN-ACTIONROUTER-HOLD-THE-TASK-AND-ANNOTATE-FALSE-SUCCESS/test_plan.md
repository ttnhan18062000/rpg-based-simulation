---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS
artifact_type: test_plan
tags: [engine, combat, observability]
---

# Test plan

`tests/unit/actions/test_action_routing_withheld_action.py` (16 tests; with `tests/unit/actions` 25 in all). Disabling controls, each restored with `git checkout`:
- Posture reporting removed from the router (run over `tests/unit/actions` plus the posture scenario): exactly 6 fail (4 postures, SKILL,
  the router return-shape test); 21 others pass, including `tests/mechanic_scenarios/test_combat_judgement_withdrawal.py`.
- Stale-reason filter removed: exactly `test_stale_annotation_reason_does_not_survive_into_a_later_success` fails; 24 pass.
- Any-action clear removed from `actions.py`: exactly 6 fail (4 postures, SKILL, unsupported action); 19 pass.
Must-not-change pins: 4 risk-accepted postures still dispatch; absent posture and other-target posture do not withhold; a decision-time
`reason` without an `outcome` is kept; the dead-target branch still clears.
Regression: `tests/unit/actions tests/unit/combat tests/unit/engine tests/mechanic_scenarios tests/architecture -m "not slow"`:
629 passed, 1 skipped, 4 deselected (`probes/regress.sh`).
Instrument checks: `withheld_exposure.py` recomputes the gate's own condition before delegating, so it is valid before and after the change;
the before and after runs each repeated and matched.
