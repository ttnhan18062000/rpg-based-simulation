---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07
artifact_type: plan
tags: [strategy, cognition]
---

# Plan

1. Commit 1 is the designer's SURV-05/06/07 evidence patch (v3), replacing the earlier cuts.
2. `src/ai/goals/need_pull.py`: the pure curve (raw need plus a smoothstep from 0.6 to 0.85 of the consequence line, +60), evaluated on the arrival level `(need + rate x tiles) / line` with the kind's own rate (`need_rates`, SURV-05). The consequence lines (95, 98) stay here; per-tick rates do not.
3. `src/ai/goals/scorers.py`: `SleepScorer` and `EatScorer` call it with the travel distance to the inn (0 with no inn). Only the need terms change; no other goal's magnitude.
4. `src/ai/goals/present_threat.py` and `scorers_support.py`: the escalation gives way to a present threat (a perceived, catalog-hostile neighbour plus `present_threat_terms`); a wound alone is not a threat.
5. `src/engine/tactical_rest.py` and the tactical hook: rest in place (`REST`, reason `REST_IN_PLACE`) when the bed (`service_tile` over inn and home) cannot be reached before 0.85 of the line, or there is none, and no present threat holds. `_suspend_project_for_threat` extracted from `evaluate_entity_intent` to stay inside the function-length ceiling.
6. Parity: Bible 04 subsection, ledger STRAT-280, divergence 2.81.

Out of scope: the free meal and the poor subject's redirect (Decision 27), the opportunity-attack-per-step defect, any change to `core_actions.py`, `town_resolution.py` or the per-kind need-path integrity check, MOV-07.
