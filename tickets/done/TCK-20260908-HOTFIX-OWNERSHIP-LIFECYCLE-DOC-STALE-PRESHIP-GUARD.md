---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260908-HOTFIX-OWNERSHIP-LIFECYCLE-DOC-STALE-PRESHIP-GUARD
phase: done
date: 2026-09-08
tags: [ai, governance, testing]
---

# TCK-20260908-HOTFIX-OWNERSHIP-LIFECYCLE-DOC-STALE-PRESHIP-GUARD

## Title
Update stale pre-ship guard test in test_subsystem_ownership_lifecycle_doc.py for the now-shipped Bash secret-scan hook

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260904-BASH-SECRET-SCAN-HOOK` (PR #149) legitimately shipped the Bash secret-exposure
advisory hook, updating `docs/guidelines/subsystem_ownership_lifecycle.md`: removed the
"Bash secret-exposure advisory hook" bullet from `## Excluded Subsystems` and added a real
ownership-table row for it (per that ticket's own approved plan Step 6). CI on PR #149 failed
`tests/docs/test_subsystem_ownership_lifecycle_doc.py::test_bash_secret_scan_hook_not_given_shipped_style_row`
— a real, pre-existing test from a different, already-closed ticket
(`TCK-20260904-OWNERSHIP-LIFECYCLE-DOC`) that hard-asserts this exact subsystem's table row must
contain `"BLOCKED"` or `"not yet built"`, and that the `## Excluded Subsystems` section must still
mention `TCK-20260904-BASH-SECRET-SCAN-HOOK` with `"BLOCKED"`. Both assertions encode the
*pre-ship* state — a guard against someone prematurely writing a shipped-style row before the hook
actually existed. That guard's job is now done differently: the hook legitimately shipped, exactly
as `governance_capability_policy_epic.md`'s M4 always intended, so requiring the row to still say
"BLOCKED" would be asserting something now false.

## Scope
- Update `test_bash_secret_scan_hook_not_given_shipped_style_row` in
  `tests/docs/test_subsystem_ownership_lifecycle_doc.py` to reflect the shipped state: the table
  row should NOT be required to say "BLOCKED"/"not yet built" now that the hook is real; the
  `## Excluded Subsystems` section should NOT be required to still mention this ticket, since it
  correctly no longer does.
- Confirm the row's actual content (already shipped by `TCK-20260904-BASH-SECRET-SCAN-HOOK`) is
  a legitimate, well-formed table row per the same shape every other row in the table uses (5
  columns: Subsystem, Accountable role, Update trigger, Staleness signal, Removal condition) —
  the test should assert this positively, not just remove the now-false pre-ship assertion.
- Rename the test function if its name (`..._not_given_shipped_style_row`) no longer describes
  what it checks — a name is not itself load-bearing, but a misleading name left in place after
  this fix would confuse a future reader.

## Out of Scope
- Any change to `docs/guidelines/subsystem_ownership_lifecycle.md` itself — already correctly
  updated by `TCK-20260904-BASH-SECRET-SCAN-HOOK`; this ticket only updates the stale test.
- Any change to the Bash secret-scan hook itself, `.claude/settings.json`, or
  `tools/write_path_guard.py` — unrelated to this fix.
- Re-litigating whether the hook should have shipped — already decided and shipped by the ratified
  ticket; this is purely a test-currency fix.

## Acceptance Criteria
- [x] `pytest tests/docs/test_subsystem_ownership_lifecycle_doc.py -v` passes in full
- [x] The updated test positively asserts the shipped row's real shape/content rather than merely
      deleting the now-false pre-ship assertions
- [x] No other test in the file is touched

## Related Tickets
- `TCK-20260904-BASH-SECRET-SCAN-HOOK` (done, PR #149) — shipped the hook and the doc update that
  made this test's pre-ship assertion obsolete.
- `TCK-20260904-OWNERSHIP-LIFECYCLE-DOC` (done) — original author of the now-stale test.

## Related Docs
- `docs/guidelines/subsystem_ownership_lifecycle.md`

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `tests/docs/test_subsystem_ownership_lifecycle_doc.py`

## Assumptions / Open Questions
None — self-evident scope, single test function to update, real CI failure with a clear root
cause already confirmed via real CI logs (not guessed).

## Implementation Notes

Renamed `test_bash_secret_scan_hook_not_given_shipped_style_row` to
`test_bash_secret_scan_hook_has_real_shipped_row` in
`tests/docs/test_subsystem_ownership_lifecycle_doc.py`, inverting its assertions to check the
now-true post-ship state instead of the now-false pre-ship state: the matching table row must
exist (was: optional), must NOT contain "BLOCKED"/"not yet built" (was: must), must cite
`TCK-20260904-BASH-SECRET-SCAN-HOOK`, must have 5 well-formed non-empty cells with a real
vocabulary role in the Accountable-role column, and the `## Excluded Subsystems` section must no
longer mention this ticket (was: must). Added a docstring explaining why the test changed and
pointing to this hotfix ticket. No other test function, and no other file, was touched —
`docs/guidelines/subsystem_ownership_lifecycle.md` itself was already correct (shipped by
`TCK-20260904-BASH-SECRET-SCAN-HOOK`); only the stale test needed to catch up to reality.

## Test Summary

`pytest tests/docs/test_subsystem_ownership_lifecycle_doc.py -v`: 11/11 pass. Re-ran the exact
CI-scoped command that originally failed on PR #149 —
`pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow and
not extra_slow" -q`: 237 passed, 2 skipped, 1 deselected, 2 xfailed, 0 failed (previously 235
passed / 1 failed). Independently re-verified by a fresh `done-checker` dispatch, which also
confirmed the new assertions are actually true against the real doc content, not just internally
consistent with themselves.

## Files Changed

- `tests/docs/test_subsystem_ownership_lifecycle_doc.py` — one test function renamed and rewritten
  (+31/-9 lines); no other function touched.

## Completion Summary

Fixed a real CI failure on PR #149 caused by a stale pre-existing test (from a different,
already-closed ticket, `TCK-20260904-OWNERSHIP-LIFECYCLE-DOC`) that hard-asserted the Bash
secret-scan hook subsystem must still read as speculative/pre-ship, now that it has legitimately
shipped. Updated the test to assert the correct post-ship state instead of deleting or weakening
it — the fix makes the test stricter in the direction that matters (positively verifying the
shipped row's real shape) rather than merely removing the now-false assertion. Verified against
real doc content, not just internal test consistency. `docs/guidelines/subsystem_ownership_lifecycle.md`
itself required no change.
