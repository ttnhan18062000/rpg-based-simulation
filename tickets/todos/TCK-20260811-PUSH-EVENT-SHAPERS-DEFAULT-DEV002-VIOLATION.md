---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION
phase: open
date: 2026-08-11
tags: [observability, feature-flags]
---

# TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION

## Title
`ENABLE_PUSH_EVENT_SHAPERS` defaults to `FeatureMode.ON`, violating
`test_feature_flag_defaults_are_stable_across_instances`'s DEV-002 requirement that all flag
defaults be `OFF`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
While running the scoped regression suite for `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` (part
of the adventure-cognition-merge epic), the pre-existing
`tests/integration/test_scenario_feature_flag_defaults.py::test_feature_flag_defaults_are_stable_across_instances`
test failed:

```
AssertionError: Flag 'ENABLE_PUSH_EVENT_SHAPERS' serializes as 'ON' instead of 'OFF'.
Defaults must be FeatureMode.OFF per DEV-002.
```

**Confirmed pre-existing and unrelated to the epic that discovered it**: `git blame` traces
`ENABLE_PUSH_EVENT_SHAPERS: FeatureMode.ON` in `src/domains/optimization/feature_flags.py:31` to
commit `11b83f37` ("Batch commit: 43-ticket push-based observability migration epic..."), dated
2026-08-08 — 3 days before this session, from a wholly unrelated observability migration epic. The
failing test file was never touched by the adventure-cognition-merge epic, and the test fails
identically when run in complete isolation (`pytest tests/integration/test_scenario_feature_flag_defaults.py::test_feature_flag_defaults_are_stable_across_instances -q`
on a clean tree), confirming it is not caused by any adventure-epic change.

## Scope
- Investigate whether `ENABLE_PUSH_EVENT_SHAPERS` defaulting to `ON` was an intentional decision
  by the 43-ticket push-observability epic (in which case the test's DEV-002 assertion needs an
  explicit, disclosed exception — matching the pattern already used for
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, which the same file's own comments show was deliberately kept
  as a separate flag with its own exception handling) or an unintentional oversight (in which case
  the flag default itself should be corrected to `OFF`)
- Fix accordingly: either flip the default to `OFF`, or add a documented, explicit test exception
  matching the codebase's own existing convention for similar cases
- Confirm `test_feature_flag_defaults_are_stable_across_instances` passes after the fix

## Out of Scope
- Any change to the adventure-cognition-merge epic's own tickets — this regression is confirmed
  unrelated to that work
- Any other flag default besides `ENABLE_PUSH_EVENT_SHAPERS` — the test only currently flags this
  one flag

## Acceptance Criteria
- [ ] Root cause determined: was `FeatureMode.ON` for `ENABLE_PUSH_EVENT_SHAPERS` an intentional
      decision (undocumented in the test) or an unintentional default
- [ ] `test_feature_flag_defaults_are_stable_across_instances` passes
- [ ] If intentional, the exception is documented consistently with how
      `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` is already handled in the same file

## Related Tickets
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (the ticket whose Test phase discovered this,
  confirmed unrelated to its own changes)

## Related Docs
None yet — Investigate should identify the relevant DEV-002 doc/contract reference.

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/optimization/feature_flags.py (line ~31, `ENABLE_PUSH_EVENT_SHAPERS` default)
- tests/integration/test_scenario_feature_flag_defaults.py (the failing test, DEV-002 assertion)

## Assumptions / Open Questions
- Root cause is not yet known — this ticket only confirms the regression is real and unrelated to
  the epic that discovered it. Investigate must determine whether the `ON` default was intentional.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
