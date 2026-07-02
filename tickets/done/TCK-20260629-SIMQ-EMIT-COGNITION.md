---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-COGNITION
phase: done
date: 2026-06-29
tags: [simq, observability, event-gap, cognition, belief]
---

# TCK-20260629-SIMQ-EMIT-COGNITION

## Title
SimQ: Emit COGNITION and INFORMATION Pillar Events from Belief and Lead Phases

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
COGNITION and INFORMATION pillars need events from PP-03/04/26/30. All phases are
@staticmethod with no event_recorder — same pattern as AGENCY ticket. Events detected
from EntityUpdate fields and state diff: self_model_updated, belief_assimilated,
belief_updated, paid_information_transaction, lead_certainty_changed.

## Scope
Extended `EventExtractor.extract()` to emit 5 COGNITION/INFORMATION events from
EntityUpdate.self_model_bundle_set, property_updates, resource_transfers, and
strategic.leads state diff.

## Out of Scope
- `knowledge_default_fallback`, `belief_stale`, `decision_diverged_by_belief`,
  `lead_contradiction_resolved`, `paid_info_changed_goal` — require phase hooks

## Acceptance Criteria
- [x] `self_model_updated` emitted when self_model_bundle_set is set in EntityUpdate
- [x] `belief_assimilated` + `belief_updated` emitted when last_assimilated_tick == current tick
- [x] `paid_information_transaction` emitted when resource_transfers has INFORMATION_PURCHASE
- [x] `lead_certainty_changed` emitted from state diff when lead certainty changes
- [x] 14 unit tests pass
- [x] No import of src/simulation_quality/ from observability layer

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (done)
- TCK-20260629-SIMQ-EMIT-STATE-DIFF (done)
- TCK-20260629-SIMQ-EMIT-AGENCY (done)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COGNITION, INFORMATION
- `docs/parity_ledger/infrastructure.yaml` SIMQ-CALIBRATED-001

## Related Stored Artifacts
- `stored_artifacts/TCK-20260629-SIMQ-EMIT-COGNITION/`

## Related Code Areas
- `src/observability/event_extractor.py` — added cognition/info emission block
- `tests/unit/observability/test_event_extractor_cognition.py` — new (14 tests)

## Implementation Notes
All four phases (PP-03/04/26/30) are @staticmethod with no event_recorder. Detection:
- PP-03 → `self_model_bundle_set` on EntityUpdate
- PP-04 → `property_updates["last_assimilated_tick"] == tick`
- PP-26 → `resource_transfers[].source_kind == "INFORMATION_PURCHASE"`
- PP-30 → `entity.strategic.leads[lid].certainty != prior.strategic.leads[lid].certainty`

## Test Summary
14 tests in `tests/unit/observability/test_event_extractor_cognition.py`. 836 total pass.

## Files Changed
- `src/observability/event_extractor.py` — cognition/information block added; agency block refactored
- `tests/unit/observability/test_event_extractor_cognition.py` — new (14 tests)
- `staging_artifacts/TCK-20260629-SIMQ-EMIT-COGNITION/` → `stored_artifacts/`

## Completion Summary
5 COGNITION/INFORMATION events now flowing via EventExtractor. 5 events deferred (require
phase-level hooks). COGNITION and INFORMATION pillars will show non-zero events in next
calibration run.
