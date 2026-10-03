---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260824-HOTFIX-GHA-NODE20-DEPRECATION-BUMP
phase: done
date: 2026-08-24
tags: [testing]
---

# TCK-20260824-HOTFIX-GHA-NODE20-DEPRECATION-BUMP

## Title
Bump `actions/checkout` and `actions/setup-python` pins in test.yml to clear the Node20-deprecation warning

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Every job in `.github/workflows/test.yml` currently emits a GitHub Actions deprecation warning: "Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5." This is a pure version-string bump of the two pinned action refs to their current major versions, which natively support Node24 per GitHub's Node20-runner deprecation notice (github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/). No job logic, inputs, or outputs change.

## Scope
- In `.github/workflows/test.yml`, replace all 13 occurrences of `actions/checkout@v4` with `actions/checkout@v5`.
- In `.github/workflows/test.yml`, replace all 12 occurrences of `actions/setup-python@v5` with `actions/setup-python@v6`.
- No other lines in the file change.

## Out of Scope
- `actions/upload-artifact@v4` (1 occurrence, line 584) — not flagged by the Node20 deprecation warning; left untouched, do not bump speculatively.
- Any other workflow file under `.github/workflows/` (this ticket scopes to `test.yml` only, per the reported warning).
- Any change to job logic, step ordering, inputs/outputs, matrix definitions, or the new-vs-existing test-split / step-summary reporting features landed by the two sibling tickets below.
- Any further action-version audit beyond the two refs named in the warning.

## Acceptance Criteria
- [x] `grep -c "actions/checkout@v4" .github/workflows/test.yml` returns 0.
- [x] `grep -c "actions/checkout@v5" .github/workflows/test.yml` returns 13.
- [x] `grep -c "actions/setup-python@v5" .github/workflows/test.yml` returns 0.
- [x] `grep -c "actions/setup-python@v6" .github/workflows/test.yml` returns 12.
- [x] `grep -c "actions/upload-artifact@v4" .github/workflows/test.yml` still returns 1 (unchanged).
- [ ] A subsequent CI run of `test.yml` (via an open PR) no longer emits the "Node.js 20 is deprecated" warning banner, and all jobs pass with the same pass/fail outcome as before the bump (no behavior change). (Not verifiable locally — requires an open PR to actually run CI; not yet pushed/opened as part of this implementation step.)
- [x] No other line in `.github/workflows/test.yml` differs from the pre-change version (diff limited to the 25 pin-version lines — verified via `git diff`, exactly 25 additions / 25 deletions, all matching the two action-pin substitutions).

## Related Tickets
- TCK-20260823-CI-STEP-SUMMARY-REPORTING — done; added the per-job `$GITHUB_STEP_SUMMARY` reporting that this ticket's CI run will exercise. Related context only, not overlapping scope (that ticket touched step bodies, not action-version pins).
- TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT — done; extended the same jobs' summary reporting with new-vs-existing test counts. Related context only, not overlapping scope. This bump was discovered while verifying CI for these two tickets.

## Related Docs
None. Pure CI/process tooling change; no Mechanics Bible or Engine Contract constraint applies. Confirmed via read of `.github/workflows/test.yml` and `docs/parity_ledger/infrastructure.yaml` — no doc governs GitHub Actions version pins specifically.

## Related Stored Artifacts
None found under `stored_artifacts/` covering GitHub Actions version pinning or this Node20 deprecation warning.

## Related Code Areas
- `.github/workflows/test.yml`

## Assumptions / Open Questions
- Assumes `actions/checkout@v5` and `actions/setup-python@v6` are drop-in replacements requiring no input/output changes for this repo's usage (both are documented as backward-compatible major bumps whose only headline change is the Node24 runtime target). If either introduces a breaking input/output change for this repo's specific usage pattern, that would invalidate the "pure version bump" framing and this ticket's hotfix tier.
- `layer: testing` chosen to match the two sibling CI-reporting tickets (both also `layer: testing`) since this change lives in the same CI test-workflow file, even though the change itself is process/tooling rather than test-logic. No better-fitting registered layer exists for GitHub Actions workflow-pin maintenance.
- Priority set to P3 per request (cosmetic warning, not a build failure) — no job currently fails because of this warning.

## Implementation Notes
Ran `sed -i 's|actions/checkout@v4|actions/checkout@v5|g; s|actions/setup-python@v5|actions/setup-python@v6|g'` against `.github/workflows/test.yml`. This is a pure find/replace across the whole file, so it necessarily also touched the 13 `checkout` and 12 `setup-python` occurrences uniformly — no per-job editing was needed since every occurrence in scope needed the same substitution and no other action pin in the file matched either pattern (`actions/upload-artifact@v4` does not match `actions/checkout@v4` or `actions/setup-python@v5`, so it was correctly left untouched by construction, not by exclusion logic).

Before applying the bump, checked the actual GitHub release notes for both actions (`actions/checkout` v5.0.0, `actions/setup-python` v6.0.0) per the ticket's own request to verify no breaking behavior change was introduced beyond the Node20→Node24 runtime target itself. Neither release documents any removed/changed input, output, or step behavior — the only stated requirement is a runner version of v2.327.1+, which GitHub-hosted runners already satisfy. This confirms the "pure version bump" framing in the ticket's Assumptions section and justifies `behavior_changed: false`.

### Discovered-during-Test collateral fix: stale hardcoded pins in structural guard tests
The Test phase found that `tests/static/test_ci_step_summary_reporting.py` — authored by the two
sibling tickets referenced above (TCK-20260823-CI-STEP-SUMMARY-REPORTING and
TCK-20260824-CI-NEW-EXISTING-TEST-SPLIT) — hardcodes the *old* action-pin versions as static
baseline constants used to assert the workflow file is otherwise unchanged:
- `_PRE_EXISTING_USES` (a set of allowed `uses:` values, used by
  `test_no_new_requirements_txt_entry_and_no_new_marketplace_action` to fail on any *new*
  `uses:` reference appearing anywhere in the workflow).
- `_EXPECTED_MIGRATION_LANES_YAML` and `_EXPECTED_SLOW_YAML` (full expected-job-body literals,
  used by `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` to assert those two
  deliberately-out-of-scope jobs are byte-for-byte unchanged by *their* ticket).

This ticket's version bump correctly changed every `uses:` line in `test.yml` (including inside
the `migration-lanes` and `slow` job bodies), so these baselines were now stale and 3 tests failed
(`test_no_new_requirements_txt_entry_and_no_new_marketplace_action`,
`test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`,
`test_no_new_requirements_txt_entry_for_new_existing_split`, the last of which just re-invokes the
first). This is not scope creep: this ticket's own AC #6 already requires "No other line in
`.github/workflows/test.yml` differs from the pre-change version" to be *provable*, and the only
mechanism that proves it is these structural guard tests — so keeping them passing (by updating
their literal baselines to the new, now-correct pins, not by weakening what they assert) is
required to satisfy this ticket's own scope, not a separate concern being smuggled in.

Fixed by updating, in `tests/static/test_ci_step_summary_reporting.py`:
1. `_PRE_EXISTING_USES`: `actions/checkout@v4` → `actions/checkout@v5`, `actions/setup-python@v5`
   → `actions/setup-python@v6` (`actions/upload-artifact@v4` unchanged, per this ticket's Out of
   Scope).
2. `_EXPECTED_MIGRATION_LANES_YAML`: same two substitutions inside the embedded YAML literal,
   confirmed against the actual current `migration-lanes` job body in `.github/workflows/test.yml`
   (read directly, not assumed).
3. `_EXPECTED_SLOW_YAML`: same two substitutions inside the embedded YAML literal for the `slow`
   job body (this constant is also used by the same
   `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket` test but was not called out by
   name in the failure list — found by reading the full file rather than only the 3 named
   failures).

Also grepped `tests/static/` and `tests/tools/` for any other stale `actions/checkout@v4` /
`actions/setup-python@v5` references. Found one incidental hit outside the 3 failing tests: a
comment (not an assertion) in `tests/tools/test_parity_index_baseline.py` line 229 referencing
"CI's default actions/checkout@v4 behavior" while explaining shallow-clone semantics. Updated the
comment text to `@v5` for accuracy; it carried no assertion so it was not causing a test failure,
but leaving a stale version number in an explanatory comment would be misleading once this
ticket lands. One further hit was found in `tests/docs/test_prescan_mandate_instruction_draft.py`
(a docstring, also non-asserting) — left untouched as genuinely out of scope: it belongs to an
unrelated ticket (TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-*), lives outside `tests/static/` and
`tests/tools/`, and touching it here would mix unrelated tickets' file ownership.

## Test Summary
`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — passes, file still parses as valid YAML.
Grep verification: `actions/checkout@v4` count 0, `actions/checkout@v5` count 13, `actions/setup-python@v5` count 0, `actions/setup-python@v6` count 12, `actions/upload-artifact@v4` count 1 (unchanged).
`git diff .github/workflows/test.yml` shows exactly 25 line changes (25 insertions / 25 deletions), and every changed line is one of the two targeted substitutions — confirmed via `git diff | grep -E '^[+-]' | sort -u`, which returned only the four expected unique lines (before/after for each action).
Full CI run (via an open PR) was not executed as part of this implementation step — that AC item is left unchecked pending a PR/push, per standard hotfix workflow (push/PR is a separate, user-authorized step).

Collateral-fix verification: `pytest tests/static/test_ci_narrow_path_filtered_jobs.py tests/static/test_ci_step_summary_reporting.py tests/static/test_corpus_diversity_ci_isolation.py tests/static/test_ci_requirements_no_ml_stack.py tests/tools/test_ci_workflow_test_coverage.py -v` — all 54 tests pass, including the 3 that were failing before this fix (`test_no_new_requirements_txt_entry_and_no_new_marketplace_action`, `test_slow_and_migration_lanes_jobs_unchanged_by_this_ticket`, `test_no_new_requirements_txt_entry_for_new_existing_split`).

## Files Changed
- `.github/workflows/test.yml`
- `tests/static/test_ci_step_summary_reporting.py` (collateral fix: `_PRE_EXISTING_USES`, `_EXPECTED_MIGRATION_LANES_YAML`, `_EXPECTED_SLOW_YAML` baselines updated to the new action pins)
- `tests/tools/test_parity_index_baseline.py` (collateral fix: stale `@v4` version number corrected in an explanatory comment; no assertion changed)

## Completion Summary
Bumped the two pinned GitHub Actions refs in `.github/workflows/test.yml` that were triggering the Node.js 20 deprecation warning: all 13 `actions/checkout@v4` occurrences to `actions/checkout@v5`, and all 12 `actions/setup-python@v5` occurrences to `actions/setup-python@v6`. `actions/upload-artifact@v4` was left untouched (not flagged, out of scope). Verified via release-note check that neither major bump changes inputs/outputs/behavior beyond the Node24 runtime target itself, so this is a pure version-pin change with no observable behavior difference. YAML validity and exact occurrence counts confirmed; the diff touches only the 25 pin-version lines. During Test, discovered and fixed a legitimate collateral regression: two sibling tickets' structural guard tests (`tests/static/test_ci_step_summary_reporting.py`) hardcoded the old action-pin versions as baseline constants; updated those baselines (and one stale comment in `tests/tools/test_parity_index_baseline.py`) to match the new correct pins. All 54 tests in the affected static/tools test files now pass.
