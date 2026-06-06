# TCK-20260419-MC-TASK3-CORE-STARTUP-VALIDATION

## Title
Milestone C - Task 3: Complete Startup Validation and Flag Enforcement

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Harden startup and runtime control behavior to ensure contradictory or unsafe flags are rejected.

## Scope
- Harden `ProfileValidator` and `ConfigValidationError`.
- Implement contradictory flag rejection (SURVIVAL + REPLAY).
- Enforce forbidden overrides (BYPASS_GOVERNOR).

## Acceptance Criteria
- [x] Impossible flag combinations result in `ConfigValidationError`.
- [x] Hard-forbidden flags are rejected at kernel startup.
- [x] Hardware realism remains a warning-only path.

## Implementation Notes
- Implemented `tests/config/test_forbidden_flags.py` to verify rejection of `BYPASS_GOVERNOR` and other contract overrides.
- Verified validation logic for `SURVIVAL_ONLY` vs `REPLAY_ENABLED`.

## Test Summary
- `tests/config/test_forbidden_flags.py` PASS
- `tests/config/test_startup_validation.py` PASS

## Files Changed
- `src/config/validator.py`
- `tests/config/test_forbidden_flags.py`

## Completion Summary
Startup validation is now a hard contract gate for operational safety.
