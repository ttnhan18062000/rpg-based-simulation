---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING
phase: inprogress
date: 2026-10-04
tags: [architecture, delivery]
---

# TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING

## Title
M5f: After its own two-week soak, make the package-registry completeness check block a new top-level `src/` package without a row

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Roadmap decision 8.10: a new check is advisory for two weeks before it blocks. `TCK-20261004-PACKAGE-REGISTRY-VALIDATOR` added `python3 -m codebase.structure.packages validate` as an advisory step of the `code-health` job, with two problem classes (`schema`, `completeness`). This ticket promotes the `completeness` class (a tracked top-level `src/` package with no row; a row for a package that is not there) to blocking. BLOCKED until the soak ends: soak start is the merge date of the PR carrying the validator, end is start + 14 days; both are written here at that merge.

## Scope
- Soak review first: how often the advisory step reported a completeness problem, false positives, whether the registry rows were reviewed
- Make the `Package registry` step block (remove its `continue-on-error`) and add a completeness assertion to the real-repo test in `tests/codebase/test_package_registry.py` (today it asserts schema only on purpose)
- Ask the owner to mark the check required in branch protection (owner action; record it)
- Announce the date to the other planners before flipping: it makes a new top-level `src/` package without a registry row fail the PR of any domain

## Out of Scope
- Any file under src/
- Per-package gates driven by `strictness_tier`
- Changing the registry rows beyond what the soak review needs

## Acceptance Criteria
- [ ] Soak start and end dates recorded here
- [ ] Soak review written with dates, counts and dispositions
- [ ] A PR that adds a top-level `src/` package without a row fails, and one with a row passes (demonstrated on real PR runs)
- [ ] Owner confirmed the required-check setting
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/python_code_standard.md (rule M5)

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/structure/
- .github/workflows/test.yml
- tests/codebase/test_package_registry.py

## Assumptions / Open Questions
- Soak start 2026-10-04 (PR #315 merged 2026-10-04T06:26:43Z), end 2026-10-18 (start + 14 days). Roadmap decision 8.18: ships in the one flip batch, merged on or after 2026-10-18; the soak review is drafted now and finalized after the window
- The `Package registry` step has its own `continue-on-error`, so the M4 flip (which removes it from the `code-health` job's ratchet step) does not make this step blocking

## Implementation Notes
- `Package registry` step: `continue-on-error` removed, CI comment rewritten. It is a step of `Code health`, already a required check, so no separate setting is needed (recorded here). Exit 1 (problem) and exit 2 (cannot run) now fail the job; the validator's annotations changed from `::warning::` to `::error::` and "(advisory)" left its summary text.
- The real-repo test now asserts completeness as well as schema (`load_rows(..., (SCHEMA, COMPLETENESS))`); its docstring says it is a second enforcement point, intended at the flip. Mutation proof: removing one registry row fails it with `[completeness] tracked top-level package has no row: src/actions`.
- Static pin: the tolerant steps of `code-health` are exactly `{"Paths this PR changed"}`.
- Live demo (steps 3 and 4 are this ticket's; see ticket TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING for all five): step 3 https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37211037495 failed only at `Package registry` and in `Tools · a–e` on the completeness test; step 4 https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37213113973 passed both.
- Authorization record: each demo push followed a direct owner yes (AskUserQuestion). For step 3 the push command ran after the yes, but its output was lost in a session interruption; the retried command reported "Everything up-to-date", so the push had already happened. That the first execution of the same command did it is an inference, not something the record shows.
- Precondition: `validate` on `origin/main` 053f459e4 gives 0 problems over 36 rows (2026-10-04). Repeat right before merge.

## Test Summary

## Files Changed

## Completion Summary
