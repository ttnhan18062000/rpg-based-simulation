---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT
artifact_type: test_plan
tags: [strategy, cognition]
---

# Test plan

- `tests/unit/strategic/test_contract_objective.py` (31): the scorer guard (own-sourced scores 0; the other party still scores and targets the source; an own-sourced contract does not hide another); the evaluator materializes only the counterparty contract with the builder id; the project-id round trip; every contract status mapped to its outcome; the combined predicate; closure through the real `evaluate_strategic_intent`; work-queue scheduling.
- Disabling controls: scorer guard removed (3 fail), contract predicate disabled (13 fail), work queue entity-only (1 fails).
- Scoped sweep: strategic, social, AI, work-queue, cooperation, architecture, regression, certification and the two mechanism-registry checks.
- Corpus: `probes/social_contract_exposure.py` over 4 worlds x 2000 ticks, before (twice) and after.

## Proof Plan

- Level: unit with constructed cases, plus a real-kernel corpus measurement.
- Proof kind: regression with disabling controls; the corpus measurement shows the self-targeted projects no longer form.
- Oracle source: the planner's ruling (option A) and `docs/mechanics/04_strategic_cognition.md`.
- Expected effect: no contract project is created for a contract the holder sourced; a contract project ends when its contract is no longer ACTIVE.
- Selected commands: `pytest tests/unit/strategic/test_contract_objective.py`; `probes/sc_measure.sh`.
