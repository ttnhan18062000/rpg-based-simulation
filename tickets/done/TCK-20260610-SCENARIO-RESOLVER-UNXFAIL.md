# TCK-20260610-SCENARIO-RESOLVER-UNXFAIL

## Title
Convert ScenarioSetupResolver happy-path xfails to passing tests after CAT-REL-099 fix

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`ScenarioSetupResolver` (Phase 30) has its full happy-path integration tests marked xfail due to the CAT-REL-099 catalog defect. The schema, modifier layer, and partial behavior tests pass, but the end-to-end scenario resolution is not proven. Once CAT-REL-099 is fixed, these xfails must be verified and removed. This ticket is the verification and closure step for Phase 30.

## Scope
- After TCK-20260610-CAT-REL-099-FIX is merged: run the scenario setup resolver integration suite
- Confirm all previously xfailed happy-path tests now pass
- Remove xfail markers and associated CAT-REL-099 reason comments
- If any tests still fail for reasons other than CAT-REL-099, document them separately without removing those xfail markers

## Out of Scope
- Changes to `ScenarioSetupResolver` logic or schema
- Adding new scenario test cases beyond what exists

## Acceptance Criteria
- [x] All scenario setup resolver happy-path tests that were xfailed due to CAT-REL-099 now pass without xfail marker
- [x] `ScenarioSetupResolver` can fully resolve at least one scenario end-to-end in strict catalog mode
- [x] Modifier application tests continue to pass
- [x] No xfail markers remain unless they reference a different, separately tracked defect

## Related Tickets
- TCK-20260610-CAT-REL-099-FIX (must be completed first — this ticket is blocked on it)

## Related Docs
- `docs/engine/authoritative_pipeline.md`

## Related Code Areas
- `tests/integration/scenarios/test_scenario_setup_resolver.py`

## Assumptions / Open Questions
- xfail removal was done as part of TCK-20260610-CAT-REL-099-FIX. No markers remain.

## Implementation Notes
No additional code changes needed. xfail markers (`_PREEXISTING_CAT_BUG`) were removed from `tests/integration/scenarios/test_scenario_setup_resolver.py` during TCK-20260610-CAT-REL-099-FIX. This ticket verified that all tests pass.

## Test Summary
10/10 tests pass in `tests/integration/scenarios/test_scenario_setup_resolver.py`. All happy-path, modifier, and architecture guard tests green.

## Files Changed
- None (all changes made in TCK-20260610-CAT-REL-099-FIX)

## Completion Summary
Verified 10/10 scenario setup resolver tests pass. xfail markers were already removed in TCK-20260610-CAT-REL-099-FIX. Ticket closed as verification-only.
