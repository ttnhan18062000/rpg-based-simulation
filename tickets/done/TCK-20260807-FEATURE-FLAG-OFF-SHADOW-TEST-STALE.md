---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE
phase: done
date: 2026-08-07
tags: [observability, simulation-quality]
---

# TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE

## Title
`test_all_enhancement_flags_default_to_off_or_shadow` is stale — fails against `ENABLE_PUSH_EVENT_SHAPERS`'s deliberate `ON` default

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/unit/config/test_phase10_feature_flags.py::test_all_enhancement_flags_default_to_off_or_shadow`
asserts every flag in `FeatureFlagManager` defaults to `OFF` or `SHADOW`. `TCK-20260806-PUSH-
CUTOVER-COMBAT-ECONOMY-FACTION` (Phase 1's cutover, DONE) deliberately, and with documentation,
flipped `ENABLE_PUSH_EVENT_SHAPERS`'s default to `ON` — a real, reasoned exception to DEV-002
policy (validated replacement, not speculative rollout; see that ticket's comment block in
`feature_flags.py`). That ticket's own Test phase only ran `tests/unit/observability/`, not
`tests/unit/config/`, so this generic guard's breakage was never caught.

Found incidentally by `TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY` (Phase 2, DONE) while running a
broader test sweep after adding a new flag of its own
(`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, correctly defaults `OFF` — confirmed not the cause).

## Scope
Either:
1. Update the test to allow a small, explicit, named allowlist of deliberate `ON`-default flags
   (documented exceptions, not a blanket relaxation), or
2. Confirm with the test's original intent (git blame / related ticket) whether it should instead
   assert something narrower that doesn't collide with a deliberately-cutover flag.

Pick whichever preserves the test's real intent (catching *accidental* ON defaults) without
permanently red-flagging a real, working, documented exception.

## Out of Scope
- Reconsidering `ENABLE_PUSH_EVENT_SHAPERS`'s `ON` default itself — already decided and validated
  by Phase 1's cutover.

## Acceptance Criteria
- [x] `test_all_enhancement_flags_default_to_off_or_shadow` passes again
- [x] The fix doesn't silently permit a genuinely-accidental future `ON` default to slip through
      — option 1 (explicit named allowlist), plus a dedicated new test isolating the
      allowlist-gating logic itself against a synthetic non-allowlisted `ON` default

## Related Tickets
- TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION (DONE — introduced the `ON` default this test
  didn't anticipate)
- TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY (DONE — found this gap incidentally)

## Related Docs
- `docs/guides/feature_flags.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/unit/config/test_phase10_feature_flags.py`
- `src/domains/optimization/feature_flags.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Chose option 1 (explicit named allowlist) over option 2 — both flags' `ON` defaults are real,
documented, validated cutovers (confirmed by re-reading `feature_flags.py`'s own comment blocks
at each definition site), not accidental drift, so narrowing the test's own assertion scope
instead would have lost real coverage for the general "no accidental ON default" case. The
allowlist is a `frozenset` of exactly 2 flag names, each with an inline comment citing the ticket
that cut it over — adding a third entry requires the same real justification, not a casual
addition. Also strengthened the check: allowlisted flags must actually equal `ON` (not just be
*permitted* to), so a future revert of either flag's default is also caught, not just additions.

Found during Investigate: `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (cut over by
`TCK-20260806-PUSH-CUTOVER-PHASE2`, after this ticket was originally filed) also needed
allowlisting — the ticket's own Request Summary only named `ENABLE_PUSH_EVENT_SHAPERS`, written
before Phase 2 existed. Included both, not just the one originally named.

## Test Summary
`tests/unit/config/test_phase10_feature_flags.py`: 7 tests (was 6) — the fixed original test plus
1 new test (`test_allowlist_does_not_silently_permit_an_accidental_on_default`) isolating the
allowlist logic against a synthetic flag map, proving AC2 directly rather than relying on
production defaults happening to stay correct. Scoped run (`tests/unit/config/`): 17 passed.

## Files Changed
- `tests/unit/config/test_phase10_feature_flags.py`

## Completion Summary
Fixed the stale test by adding an explicit, named, documented allowlist of the 2 real
cutover-validated `ON`-default flags (`ENABLE_PUSH_EVENT_SHAPERS`,
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`), rather than relaxing the check generally — any other flag
defaulting to `ON` still fails the test. Added a dedicated isolated test proving the allowlist
logic itself still rejects a non-allowlisted `ON` default.
