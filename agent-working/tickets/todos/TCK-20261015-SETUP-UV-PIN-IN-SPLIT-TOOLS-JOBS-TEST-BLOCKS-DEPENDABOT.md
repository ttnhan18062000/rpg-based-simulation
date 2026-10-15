---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261015-SETUP-UV-PIN-IN-SPLIT-TOOLS-JOBS-TEST-BLOCKS-DEPENDABOT
phase: open
date: 2026-10-15
tags: [testing]
---

# TCK-20261015-SETUP-UV-PIN-IN-SPLIT-TOOLS-JOBS-TEST-BLOCKS-DEPENDABOT

## Title
`test_every_new_job_installs_with_uv_from_the_lockfile` compares the setup-uv action by name, not by its exact version

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
platform-planner found (2026-10-15) that `tests/tools/test_ci_split_tools_jobs.py:108` asserts `s.get("uses") == "astral-sh/setup-uv@v10.2.0"`. Dependabot PR #571 bumps setup-uv to v10.3.0 (and codeql upload-sarif to v4.38.3), so it fails the Tools · a–e job, although the bump is otherwise fine. #588 (TCK-20261014-ACTIONS-MAJORS-COMBINED) made the `tests/static` pins compare names but missed this one. The user wants #571 checked now.

The test is about "every new job installs with uv", not about which setup-uv version is used. Version choice belongs to Dependabot and platform. A sweep of `tests/` on main for `owner/action@vN` literals found no other assertion: the other hits are comments or synthetic fixtures (`test_core_rpg_report.py`, `test_aseprite_licence_guard.py`).

## Scope
1. Line 108: match the action by name. Strip the `@ref` and compare against `astral-sh/setup-uv`. Use the same approach as #588's `_action_name` in `tests/static/test_ci_step_summary_reporting.py`, either reusing it or with a local one-liner. A bare `startswith("astral-sh/setup-uv@")` is also acceptable.
2. Add a regression case showing that `astral-sh/setup-uv@v99` passes and that a different action, or a step with no setup-uv, fails.

## Out of Scope
- Any workflow change, including the setup-uv version itself (Dependabot #571 brings that in).
- Other tests.

## Acceptance Criteria
- [ ] AC1: the assertion no longer contains a version literal. The test still fails if a new job has no `astral-sh/setup-uv` step.
- [ ] AC2: there is a regression case for the version-agnostic match, as in Scope 2.
- [ ] AC3: `pytest tests/tools/test_ci_split_tools_jobs.py` passes on main.
- [ ] AC4: after merge, `@dependabot rebase` on #571 turns Tools · a–e green. Record the run in Completion Summary, or note that the user or platform did the rebase.

## Related Tickets
- TCK-20261014-ACTIONS-MAJORS-COMBINED (#588, made the tests/static pins name-based)
- TCK-20261002-UV-REMAINING-CI-JOBS (wrote the assertion)

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- tests/tools/test_ci_split_tools_jobs.py
- tests/static/test_ci_step_summary_reporting.py (`_action_name`, read-only reference)

## Assumptions / Open Questions
- None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
