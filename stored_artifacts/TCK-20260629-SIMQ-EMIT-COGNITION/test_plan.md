---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-COGNITION
artifact_type: test_plan
tags: [simq, cognition, event-extractor]
---

# Test Plan: TCK-20260629-SIMQ-EMIT-COGNITION

## New Tests (tests/unit/observability/test_event_extractor_cognition.py)

- `test_self_model_updated_emitted_when_bundle_set` — e_upd.self_model_bundle_set is set
- `test_self_model_updated_not_emitted_when_bundle_not_set` — bundle is None
- `test_belief_assimilated_emitted_when_tick_matches` — last_assimilated_tick == current tick
- `test_belief_updated_emitted_with_belief_assimilated` — both emitted at same condition
- `test_belief_subject_in_payload` — payload["subject"] matches last_assimilated_subject
- `test_belief_not_emitted_when_tick_stale` — last_assimilated_tick is old tick
- `test_paid_information_transaction_emitted` — resource_transfers has INFORMATION_PURCHASE
- `test_paid_information_gold_cost_in_payload` — payload["gold_cost"] matches intent
- `test_paid_information_not_emitted_for_other_transfer` — source_kind != INFORMATION_PURCHASE
- `test_lead_certainty_changed_emitted_when_certainty_differs` — lead certainty changed
- `test_lead_certainty_payload` — from_certainty and to_certainty in payload
- `test_lead_certainty_not_emitted_for_new_lead` — lead not in prior → no event
- `test_lead_certainty_not_emitted_when_unchanged` — same certainty → no event

## Scoped Pytest Commands

pytest tests/unit/observability/test_event_extractor_cognition.py -q
pytest tests/unit/observability/ -q --no-header -m "not slow"
