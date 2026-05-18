# TCK-20260512-PERF-PROFILES

## Title
Implement performance-oriented RuntimeProfiles

## Status
DONE

## Request Summary
Create a dedicated location for performance profiles as specified in `performance_implementation.md`.

## Scope
- [x] Create `src/perf/profiles.py`.
- [x] Implement `make_perf_profile` helper function.
- [x] Define `PERF_PROFILES` dictionary with 8 profiles.

## Out of Scope
- Implementation of scenarios or harness enhancements.

## Acceptance Criteria
- `src/perf/profiles.py` exists and contains all required profiles.
- Profiles adhere to the `RuntimeProfile` model from `src/config/profiles.py`.
- No lint errors in the new file.

## Related Tickets
- TCK-20260512-PERF-INVESTIGATION (Done)

## Related Docs
- [performance_implementation.md](file:///home/vboxuser/Work/rpg-based-simulation/performance_implementation.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `src/perf/`
- `src/config/profiles.py`

## Implementation Notes
- Follow the structure suggested in Phase 1 of `performance_implementation.md`.

## Test Summary
- Verify importability of the new module.

## Files Changed
- [NEW] src/perf/profiles.py

## Completion Summary
- N/A
