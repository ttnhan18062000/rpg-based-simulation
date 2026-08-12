---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE
phase: open
date: 2026-08-12
tags: [feature-flags, determinism, testing]
---

# TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE

## Title
`test_shadow_mode_preserves_baseline_hash` fails against the same deliberate-ON-default flag set
that `TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION` already fixed elsewhere — third
instance of the same defect class

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found incidentally during `TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION`'s Test phase,
while sweeping for other tests with the same latent issue (any test asserting on
`FeatureFlagManager`'s default state without accounting for the 4 flags that deliberately default
to `FeatureMode.ON`: `ENABLE_PUSH_EVENT_SHAPERS`, `ENABLE_PUSH_EVENT_SHAPERS_PHASE2`,
`ENABLE_PUSH_EVENT_SHAPERS_QUEST`, `ENABLE_PUSH_EVENT_SHAPERS_AGENCY`).

`tests/certification/test_phase10_enhanced_determinism_parity.py::test_shadow_mode_preserves_baseline_hash`
computes a baseline hash from an empty feature list, then computes a "shadow mode" hash from
`[f for f in ff.get_all_flags() if ff.is_enabled(f)]` and asserts the two are equal. Since the 4
push-event-shaper flags default `ON` (not `OFF`/`SHADOW`), `enabled_features` is non-empty, so the
hashes never match. This is the same defect class as
`TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION` (an unguarded assumption that
`FeatureFlagManager()`'s default state has zero enabled flags), via a different assertion mechanism
(hash comparison, not a direct per-flag loop).

**Confirmed pre-existing and unrelated to that ticket's own diff**: `git diff --stat` for
`TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION` touches only
`tests/integration/test_scenario_feature_flag_defaults.py`; `test_phase10_enhanced_determinism_parity.py`
does not import that file, and the failure is driven purely by production defaults in
`src/domains/optimization/feature_flags.py` set by the earlier PUSH-CUTOVER family of tickets.

Also noted (separate, minor, may or may not be in scope for this ticket — Investigate/Scope should
decide): the test calls `ff.set_flag_mode("ENABLE_SELF_MODEL", FeatureMode.SHADOW)`, but no flag
named `ENABLE_SELF_MODEL` exists (the real flag is `ENABLE_SELF_MODEL_COGNITION`) — `set_flag_mode()`
silently no-ops for unknown flag names (`if flag in self._flags: ...`), so this line currently has
zero effect on the test's outcome. May be an unrelated latent bug in the test's own setup, or may be
intentional (testing that an unknown flag is safely ignored) — worth a quick check but likely not
the root cause of the hash mismatch either way.

## Scope
- Determine the correct fix, consistent with the established pattern from
  `TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE` and
  `TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION`: the baseline hash computation itself
  needs to account for the 4 deliberately-ON flags (e.g. compute baseline from the real default
  `enabled_features` set rather than an empty list), not weaken the test's actual intent (verifying
  SHADOW mode doesn't add features beyond the real baseline).
- Check whether `ff.set_flag_mode("ENABLE_SELF_MODEL", FeatureMode.SHADOW)`'s apparent typo
  (`ENABLE_SELF_MODEL` vs. the real `ENABLE_SELF_MODEL_COGNITION`) is relevant to this fix or a
  separate, independent latent bug — fix if in scope, otherwise flag and leave for a separate
  ticket.
- Confirm `test_shadow_mode_preserves_baseline_hash` passes after the fix, and that the other 4
  tests in the same file (`test_full_stack_on_is_deterministic_across_runs` etc.) still pass.

## Out of Scope
- Any change to `src/domains/optimization/feature_flags.py` — the 4 flags' `ON` defaults are
  correct, validated, intentional (same rationale as the 2 prior tickets in this defect family).
- Re-running the full sweep for a 4th instance of this defect class — this ticket's own scope is
  just this one test; if a 4th instance turns up later, it gets its own ticket per the same
  precedent.

## Acceptance Criteria
- [ ] Root cause confirmed: baseline hash computed from an empty list doesn't account for the 4
      deliberately-ON flags
- [ ] `test_shadow_mode_preserves_baseline_hash` passes
- [ ] No regression in the other tests in `test_phase10_enhanced_determinism_parity.py`
- [ ] Fix preserves the test's real intent (SHADOW mode doesn't add features beyond the real
      baseline) rather than trivially weakening the assertion

## Related Tickets
- TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION (DONE — found this during its own Test
  phase sweep; same defect class, different file/mechanism)
- TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE (DONE — the ticket that first solved this defect
  class, for a third test file)

## Related Docs
- docs/guides/feature_flags.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tests/certification/test_phase10_enhanced_determinism_parity.py (lines 13-25)
- src/domains/optimization/feature_flags.py (read-only reference, not modified)

## Assumptions / Open Questions
- Whether the `ENABLE_SELF_MODEL` vs `ENABLE_SELF_MODEL_COGNITION` naming mismatch is in scope for
  this ticket or deserves its own separate filing is not yet decided — Scope/Investigate should make
  this call with real evidence, not assume either way.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
