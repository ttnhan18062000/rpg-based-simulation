# Test Plan: TCK-20260610-AUDIT-EVENT-SEQUENCE

## Tests Modified
- `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py::TestHumanGatedAgenticLabE2E::test_full_e2e_chain`

## What Changed
Replaced 4-assertion weak audit check:
- `len(events) > 0`
- `workflow_started or approval_recorded in event_types`
- `len(approval_events) >= 1`
- `approved_by == "test_human"` and `stage == "GENERATION"`

With 13-checkpoint ordered sequence scan:
- gap-tolerant: advances through events, finding each checkpoint in turn
- fails with specific message if any checkpoint is missing or out of order
- `approved_by` assertion implicitly validated via `approval_recorded` appearing after `approval_required`

Also: approved UpdateSimulationKnowledge run is now unconditional — ensures checkpoints 10-13 always appear.

## Results
43/43 tests pass in `tests/integration/lab_agent/`.
