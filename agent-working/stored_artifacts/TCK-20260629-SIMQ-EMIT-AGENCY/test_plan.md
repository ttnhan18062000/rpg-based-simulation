---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-AGENCY
artifact_type: test_plan
tags: [simq, agency, event-extractor]
---

# Test Plan: TCK-20260629-SIMQ-EMIT-AGENCY

## New Tests (tests/unit/observability/test_event_extractor_agency.py)

- `test_route_selected_emitted_when_property_set` — entity_update has last_routing_family → route_selected emitted
- `test_action_executed_emitted_when_route_committed` — same condition → action_executed emitted
- `test_route_selected_payload_family` — payload["family"] matches last_routing_family value
- `test_route_selected_not_emitted_without_routing_property` — property_updates missing/empty → no event
- `test_action_executed_not_emitted_without_routing_property` — same negative case
- `test_defer_gap_documented` — document that DEFER produces no entity_update (comment test)

## Scoped Pytest Commands

pytest tests/unit/observability/test_event_extractor_agency.py -q
pytest tests/unit/observability/ -q --no-header -m "not slow"
