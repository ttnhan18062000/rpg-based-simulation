---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION
phase: done
date: 2026-08-11
tags: [observability, feature-flags]
---

# TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION

## Title
`ENABLE_PUSH_EVENT_SHAPERS` defaults to `FeatureMode.ON`, violating
`test_feature_flag_defaults_are_stable_across_instances`'s DEV-002 requirement that all flag
defaults be `OFF`

## Status
DONE

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
- Reconsidering any of the 4 flags' `ON` defaults themselves — already decided and validated by
  their respective cutover tickets (see Scope-phase finding below)

## Acceptance Criteria
- [x] Root cause determined: was `FeatureMode.ON` for `ENABLE_PUSH_EVENT_SHAPERS` an intentional
      decision (undocumented in the test) or an unintentional default
- [x] `test_feature_flag_defaults_are_stable_across_instances` passes
- [x] If intentional, the exception is documented consistently with how
      `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (and the 2 other later ON-default flags found at Scope) are
      already handled in the sibling test file, `tests/unit/config/test_phase10_feature_flags.py`

## Related Tickets
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (the ticket whose Test phase discovered this,
  confirmed unrelated to its own changes)
- TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE (DONE — the ticket that already solved this exact
  class of problem once, for a sibling test file; this ticket duplicates that established pattern
  into the second test file that was never given the same treatment)
- TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE (OPEN — filed from this ticket's own
  Test-phase sweep for other latent instances of the same defect class; found a third instance in
  `test_phase10_enhanced_determinism_parity.py`, confirmed pre-existing and out of this ticket's
  diff scope)

## Related Docs
None yet — Investigate should identify the relevant DEV-002 doc/contract reference.

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/optimization/feature_flags.py (line ~31, `ENABLE_PUSH_EVENT_SHAPERS` default)
- tests/integration/test_scenario_feature_flag_defaults.py (the failing test, DEV-002 assertion)

## Assumptions / Open Questions
- **Scope-phase finding (2026-08-12):** Root cause confirmed via `search_docs` before any grep —
  this exact problem class was already solved once, for a different but structurally-identical
  generic OFF-default guard (`tests/unit/config/test_phase10_feature_flags.py::
  test_all_enhancement_flags_default_to_off_or_shadow`), by
  `TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE`: an explicit, named, documented
  `_DELIBERATE_ON_DEFAULT_FLAGS` frozenset allowlist, not a blanket relaxation. Reading
  `src/domains/optimization/feature_flags.py` directly confirms **4** flags (not 1) currently
  default `ON`, each with its own inline comment citing a real, validated cutover ticket:
  `ENABLE_PUSH_EVENT_SHAPERS` (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`),
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` (`TCK-20260806-PUSH-CUTOVER-PHASE2`),
  `ENABLE_PUSH_EVENT_SHAPERS_QUEST` (`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`),
  `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` (`TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP`/
  `TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP`). The sibling test file's own allowlist
  (`tests/unit/config/test_phase10_feature_flags.py`) already lists all 4 — it was kept current as
  each new flag landed. Confirmed by direct pytest run that
  `test_feature_flag_defaults_are_stable_across_instances` fails on `ENABLE_PUSH_EVENT_SHAPERS`
  first (dict-insertion-order `for` loop with individual `assert` statements stops at the first
  failure) — meaning fixing only that one flag would immediately expose the same failure on
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` next. The Out of Scope/AC lines above have been updated from
  the ticket's original (pre-Scope) framing to reflect this — all 4 flags need the same allowlist
  treatment in this test file, mirroring the sibling file's exact pattern, not just the 1 flag named
  in the original failure message.

## Implementation Notes
Root cause was intentional, per Scope-phase finding: 4 flags in
`src/domains/optimization/feature_flags.py` (`ENABLE_PUSH_EVENT_SHAPERS`,
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, `ENABLE_PUSH_EVENT_SHAPERS_QUEST`,
`ENABLE_PUSH_EVENT_SHAPERS_AGENCY`) deliberately default to `FeatureMode.ON`, each backed by a
real, validated cutover ticket cited inline in that file. The sibling test file
(`tests/unit/config/test_phase10_feature_flags.py`) already carries an explicit
`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist for this exact situation (from
`TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-STALE`); `test_scenario_feature_flag_defaults.py` was
never given the same treatment and its `test_feature_flag_defaults_are_stable_across_instances`
test (which iterates the *full* `serialize()` output, unlike the narrower `_ALL_FLAG_NAMES`-based
tests T3/T4/T7 in the same file) failed on the first ON-default flag it hit in insertion order.

Fix applied (test-only, mirrors the sibling file's pattern exactly):
1. Added a locally-scoped `_DELIBERATE_ON_DEFAULT_FLAGS` frozenset constant to
   `tests/integration/test_scenario_feature_flag_defaults.py`, placed after
   `_ADVENTURE_ROUTING_PERSPECTIVES`, with the same 4 flags and the same inline cutover-ticket
   citations copied verbatim from `tests/unit/config/test_phase10_feature_flags.py`.
2. Updated `test_feature_flag_defaults_are_stable_across_instances`'s per-flag loop: allowlisted
   flags must now assert `== FeatureMode.ON.value` (so an accidental revert of a deliberate
   cutover is caught, not just silently permitted); all other flags still assert
   `== FeatureMode.OFF.value` per DEV-002.
3. `_ALL_FLAG_NAMES` (10-flag Phase 10 tuple used by T3/T4/T7) was left untouched — it is a
   narrower, different concept, correctly unaffected by this fix.
4. `src/domains/optimization/feature_flags.py` and
   `tests/unit/config/test_phase10_feature_flags.py` were not touched, per ticket scope.

No deviations from the plan described in the ticket's Assumptions/Open Questions section.

## Test Summary
- `.venv/bin/python3 -m pytest tests/integration/test_scenario_feature_flag_defaults.py -v`:
  45 passed, 0 failed (includes the previously-failing
  `test_feature_flag_defaults_are_stable_across_instances`, and all of T1-T9 parametrized cases —
  no regressions).
- `.venv/bin/python3 -m pytest tests/unit/config/test_phase10_feature_flags.py -v`: 7 passed,
  0 failed (untouched sibling file, confirmed still current/passing).

## Files Changed
- `tests/integration/test_scenario_feature_flag_defaults.py` — added `_DELIBERATE_ON_DEFAULT_FLAGS`
  allowlist constant and updated `test_feature_flag_defaults_are_stable_across_instances`'s
  assertion loop to allow-and-verify the 4 allowlisted flags as `ON` while keeping all others
  required `OFF`.

## Completion Summary
Fixed a stale DEV-002 "all flags OFF" test assertion in
`tests/integration/test_scenario_feature_flag_defaults.py` that had not been updated when 4 push-
event-shaper flags were deliberately cut over to `FeatureMode.ON` by earlier, unrelated migration
tickets. Applied the same named-allowlist pattern already established in the sibling file
`tests/unit/config/test_phase10_feature_flags.py` (by `TCK-20260807-FEATURE-FLAG-OFF-SHADOW-TEST-
STALE`), so the 4 deliberate ON defaults are now explicitly documented and enforced (not just
permitted) while all other flags still must be OFF. Test-only change; no source or sibling-test
files were modified.
