---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE
phase: done
date: 2026-08-12
tags: [feature-flags, determinism, testing]
---

# TCK-20260812-DETERMINISM-PARITY-SHADOW-BASELINE-HASH-STALE

## Title
`test_shadow_mode_preserves_baseline_hash` fails against the same deliberate-ON-default flag set
that `TCK-20260811-PUSH-EVENT-SHAPERS-DEFAULT-DEV002-VIOLATION` already fixed elsewhere — third
instance of the same defect class

## Status
DONE

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
- [x] Root cause confirmed: baseline hash computed from an empty list doesn't account for the 4
      deliberately-ON flags
- [x] `test_shadow_mode_preserves_baseline_hash` passes
- [x] No regression in the other tests in `test_phase10_enhanced_determinism_parity.py`
- [x] Fix preserves the test's real intent (SHADOW mode doesn't add features beyond the real
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

**Root cause fix**: Added a `_DELIBERATE_ON_DEFAULT_FLAGS` frozenset to
`tests/certification/test_phase10_enhanced_determinism_parity.py`, copied verbatim (flags + ticket
citation comments) from `tests/unit/config/test_phase10_feature_flags.py` — this is now the third
copy of the allowlist, matching the established pattern (the other two live in
`tests/unit/config/test_phase10_feature_flags.py` and
`tests/integration/test_scenario_feature_flag_defaults.py`).

`test_shadow_mode_preserves_baseline_hash` was rewritten so the baseline hash is computed from a
**live** `enabled_features` list (`[f for f in baseline_ff.get_all_flags() if baseline_ff.is_enabled(f)]`)
taken from a fresh `FeatureFlagManager()` constructed *before* any SHADOW override is applied — not
from an empty list, and not from a hardcoded flag list. This preserves the test's actual intent:
proving SHADOW mode does not add any feature beyond the real default baseline, rather than
comparing against a synthetic "nothing enabled" baseline that was never true in production. Kept
the pre-existing `enabled_features` computation on a *separate* second `FeatureFlagManager()`
instance (after applying the SHADOW override) so the diff stays close to the original test shape
and so the SHADOW-mode object under test is isolated from the baseline object.

Added one extra assertion — `assert set(baseline_features) == _DELIBERATE_ON_DEFAULT_FLAGS` — as a
sanity check that the live-derived baseline still matches the documented allowlist. This does not
weaken the test (the real assertion `shadow_hash == baseline` is unchanged and still derived live);
it only adds an early, clearer failure message if production defaults drift from the three test
files' shared understanding of which flags are deliberately ON, consistent with how the sibling
files use the same frozenset for a similar self-check.

**`ENABLE_SELF_MODEL` vs `ENABLE_SELF_MODEL_COGNITION` — investigated and fixed as (a), a genuine
latent bug in the test's own setup**:
- Confirmed via `src/domains/optimization/feature_flags.py` (read-only, not modified) that no flag
  named `ENABLE_SELF_MODEL` exists; the real flag is `ENABLE_SELF_MODEL_COGNITION`, defaulting to
  `FeatureMode.OFF`.
- `set_flag_mode()` (`if flag in self._flags: ...`) silently no-ops for unknown flag names, so the
  line had zero effect on `ff`'s state either before or after this fix.
- Ruled out (b) "intentionally testing that an unknown flag name is safely ignored": the test's own
  docstring says "Hash under SHADOW mode must equal baseline hash" — nothing about unknown-flag
  safety — and there is no assertion anywhere in the test that checks no-op behavior for an unknown
  name. If that were the intent, the test would assert on the no-op explicitly.
- Ruled out (c) "separate ticket": this is a one-line, same-test, same-file correction with no
  architectural surface and no behavior-changing side effect on the test's *pass/fail* outcome
  (`ENABLE_SELF_MODEL_COGNITION` defaults `OFF`, and `OFF`/`SHADOW` are both excluded from
  `is_enabled()`, so `enabled_features` is identical either way). Filing a separate ticket for a
  same-file one-line typo fix already investigated under this ticket's own explicit scope item
  would be process overhead without benefit.
- Fix: changed `ff.set_flag_mode("ENABLE_SELF_MODEL", FeatureMode.SHADOW)` to
  `ff.set_flag_mode("ENABLE_SELF_MODEL_COGNITION", FeatureMode.SHADOW)` so the test actually
  exercises a real flag under SHADOW mode, matching what its docstring claims to test.

No change to `src/domains/optimization/feature_flags.py` (out of scope, confirmed untouched).

## Test Summary
`.venv/bin/python3 -m pytest tests/certification/test_phase10_enhanced_determinism_parity.py -v`
— all 5 tests pass:
- `test_shadow_mode_preserves_baseline_hash` PASSED
- `test_full_stack_on_is_deterministic_across_runs` PASSED
- `test_provider_budget_skips_are_deterministic` PASSED
- `test_cache_enabled_and_disabled_have_same_authoritative_result_when_expected` PASSED
- `test_semantic_scorecard_deterministic_for_same_seed` PASSED

Also re-ran the two sibling files that share the same `_DELIBERATE_ON_DEFAULT_FLAGS` pattern to
confirm no regression from this change:
`.venv/bin/python3 -m pytest tests/unit/config/test_phase10_feature_flags.py tests/integration/test_scenario_feature_flag_defaults.py -q`
— 52 passed.

## Files Changed
- `tests/certification/test_phase10_enhanced_determinism_parity.py` — added
  `_DELIBERATE_ON_DEFAULT_FLAGS` frozenset; rewrote `test_shadow_mode_preserves_baseline_hash` to
  compute the baseline hash from the real live default `enabled_features` set instead of an empty
  list; fixed `ENABLE_SELF_MODEL` → `ENABLE_SELF_MODEL_COGNITION` typo in the same test.

## Completion Summary
Fixed the third instance of the "unguarded empty/zero-enabled-flags assumption" defect class:
`test_shadow_mode_preserves_baseline_hash` was comparing a SHADOW-mode hash against a baseline
computed from an empty feature list, which can never match now that 4 flags
(`ENABLE_PUSH_EVENT_SHAPERS*`) deliberately default `ON`. The baseline is now derived live from a
fresh `FeatureFlagManager()` instance (mirroring the pattern already used in
`tests/unit/config/test_phase10_feature_flags.py` and
`tests/integration/test_scenario_feature_flag_defaults.py`), preserving the test's real intent
(SHADOW mode adds nothing beyond the true default baseline) rather than weakening the assertion.
Also fixed an adjacent latent typo (`ENABLE_SELF_MODEL` → `ENABLE_SELF_MODEL_COGNITION`) in the
same test after confirming it was a genuine bug, not intentional unknown-flag-safety testing. All
5 tests in the target file pass; the two sibling files using the same allowlist pattern show no
regression.
