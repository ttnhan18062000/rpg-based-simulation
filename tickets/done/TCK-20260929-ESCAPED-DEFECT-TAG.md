---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-ESCAPED-DEFECT-TAG
phase: done
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-ESCAPED-DEFECT-TAG

## Title
Register the `escaped-defect` ticket tag and document its use

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Epic A needs a count of defects that reached `main` past green tests. Registers the tag and documents
the `Failure class:` line; the monthly count is built by the report (Epic A batch 2).

Child of `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` (Epic A), criterion 5 (tag half).

## Scope
- `python3 tools/tag_registry.py add escaped-defect` (process-skill-signal).
- A short usage section in `docs/guides/ticket_tagging.md` pointing at roadmap §4.5 for failure classes.

## Out of Scope
- The monthly count in the report; the mutation record.
- Back-tagging historical tickets.

## Acceptance Criteria
1. `escaped-defect` appears in `tools/tag_registry.py list`.
2. The guide states when to use it and where the failure classes are defined (not duplicated).

## Related Tickets
- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §4.5, §4.7
- `docs/guides/ticket_tagging.md`

## Related Stored Artifacts
None.

## Related Code Areas
`registries/tag_registry.jsonl`; `docs/guides/ticket_tagging.md`.

## Assumptions / Open Questions
None.

## Implementation Notes
Registry is append-only; category chosen as process-skill-signal (a process signal, not a subsystem).

## Test Summary
Tag registered and listed; frontmatter validator run on the new tickets.

## Files Changed
`registries/tag_registry.jsonl`; `docs/guides/ticket_tagging.md`.

## Completion Summary
Tag registered append-only; guide section added without duplicating the failure-class definitions. Monthly count is built by the report in Epic A batch 2. Gate note: the bare done_checker_static CLI reports [precheck] and docs_to_update_coverage FAILs after closure; these are known false positives tracked in TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS. `--part finalize` passes.
