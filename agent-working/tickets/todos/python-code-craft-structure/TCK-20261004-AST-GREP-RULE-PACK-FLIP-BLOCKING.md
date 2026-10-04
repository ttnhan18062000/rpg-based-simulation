---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING
phase: blocked
date: 2026-10-04
tags: [architecture, delivery]
---

# TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING

## Title
M5f: After its own two-week soak, make the ast-grep rules (N3, N4, E3) block new violations

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Roadmap decision 8.10: a new check is advisory for two weeks before it blocks. The `ast_grep` tool joined the code-health ratchet under `TCK-20261004-AST-GREP-RULE-PACK-ADVISORY`; the M4 flip (`TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`, 2026-10-17) excludes it. This ticket promotes it to blocking. BLOCKED until its soak ends: soak start is the merge date of the PR carrying the rule pack, end is start + 14 days; both are written here at that merge.

## Scope
- Soak review first: false positives per rule (N3 counts imported names, E3 counts `except` bodies of only `pass`), rows deleted as debt was paid, how many `ast_grep` rows were reseeded or added
- Remove the exclusion of `ast_grep` from the blocking set the M4 flip created (the ratchet then fails a PR on a new or worse `ast_grep` finding)
- Ask the owner to confirm the required-check setting (owner action; record it)
- Announce the date to the other planners before flipping: it makes N3, N4 and E3 violations in new code fail a PR for every domain that edits `src/`
- Decide whether the SARIF changed-line feedback should include `ast_grep` (it builds ruff and complexipy only today; a structural change)

## Out of Scope
- Any file under src/
- New rules, T3, autofix

## Acceptance Criteria
- [ ] Soak start and end dates recorded here
- [ ] Soak review written with dates, counts and dispositions
- [ ] A PR that adds a new `ast_grep` violation fails and one that does not passes (demonstrated on real PR runs)
- [ ] Owner confirmed the required-check setting
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/guidelines/python_code_standard.md (N3, N4, E3)

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/rules/
- codebase/health/
- .github/workflows/test.yml

## Assumptions / Open Questions
- Soak start and end: unknown until the rule pack's PR merges; written here at that merge
- N4 leaves a trailing digit to the reviewer; the standard's Enforcement cell says so

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
