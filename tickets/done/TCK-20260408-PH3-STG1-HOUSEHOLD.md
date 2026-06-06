# Ticket: TCK-20260408-PH3-STG1-HOUSEHOLD
# Title: Phase 3 Stage 1: Household & Home-Role System

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the foundational data structures and services for managing Households and Home anchoring. This allows entities to belong to social groups that share a base of operations (Building) and resources.

## Scope
- [ ] Create `src/core/models/household.py` with `HouseholdRecord`.
- [ ] Update `IdentityAspect` in `src/core/aspects/identity.py` with `household_id` and `home_building_id`.
- [ ] Implement `HouseholdService` for forming and managing households.
- [ ] Update `EntityPresenter` to expose household info to the API.

## Out of Scope
- Inheritance/Succession (Stage 2).
- Regional dynamics (Stage 3).
- Structured daily schedules (Stage 5).

## Acceptance Criteria
- Entities can be assigned to a `household_id`.
- The `HouseholdService` correctly tracks members of a household.
- The inspection UI shows the entity's home building and household affiliation.
- Integrated test `test_household_assignment.py` passes.

## Status
DONE (SUPERSEDED by TCK-20260408-PH3-PASS1-LIVED-MODELS)
