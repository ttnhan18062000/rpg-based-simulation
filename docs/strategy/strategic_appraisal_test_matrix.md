---
status: active
layer: strategy
authority: P1
audience: developer
---

# Strategic Appraisal Test Matrix

This matrix documents the regression test coverage for the `BoundedStrategicAppraisalService`.

| Test Case | Unit / Integration | Coverage Area | Key Verification |
|-----------|--------------------|---------------|------------------|
| `test_low_profile_entity_has_smaller_active_slice_than_high_profile_entity` | Unit | Slice Limits | `len(candidates)` == 3 for low profile |
| `test_concern_intake_is_capped_by_profile` | Unit | Source Capping | `dropped_concerns_count` logic |
| `test_lead_retention_is_capped_by_profile` | Unit | Source Capping | `lead_retention_limit` logic |
| `test_reserved_current_project_slot_is_used_when_current_project_exists` | Unit | Slot Reservation | Current project stays in slice despite low score |
| `test_dropped_candidate_counts_are_deterministic` | Unit | Determinism | Repeated evaluation returns identical drop counts |
| `test_project_retention_when_rival_is_below_margin` | Unit | Continuity | Switch margin keeps current project |
| `test_project_switch_when_rival_is_above_margin` | Unit | Continuity | Switch margin allows switch for superior rival |
| `test_switch_margin_increases_with_higher_resistance_profile` | Unit | Continuity | Profile resistance affects `switch_margin_used` |
| `test_objective_derivation_precedence_blocker_first` | Unit | Objective Derivation | Blocker takes precedence over objective |
| `test_objective_derivation_precedence_active_objective_if_no_blocker` | Unit | Objective Derivation | Project's active objective is selected |
| `test_objective_derivation_precedence_first_unresolved_if_no_active` | Unit | Objective Derivation | First unresolved objective is selected |

## Determinism Status
All strategic appraisal tests are RNG-independent and rely on fixed input attributes.

## Profile Traceability
Test expectations for `CognitionCapacityProfile` (limits and resistance) are derived directly from the formulas in `CognitionCapacityBuilder.build`.
