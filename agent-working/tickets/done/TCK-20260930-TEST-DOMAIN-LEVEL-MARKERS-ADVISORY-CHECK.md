---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-TEST-DOMAIN-LEVEL-MARKERS-ADVISORY-CHECK
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-TEST-DOMAIN-LEVEL-MARKERS-ADVISORY-CHECK

## Title
Register domain/level test markers and an advisory marker-consistency check

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No test declares a domain or level. Register the vocabulary defined in the taxonomy doc and add an advisory check that flags mismatched markers and unmarked new or modified core-RPG tests. Epic A's report picks up marked tests.

## Scope
- Register domain and level markers in `pyproject.toml`; a test asserts they match the taxonomy doc's vocabulary exactly.
- Advisory check (tool under `tools/test_architecture/`): (a) flags a marker that disagrees with the file's classification signals; (b) flags an UNMARKED new or modified core-RPG test, working from the git diff. Report only: no exit-code gate, no CI wiring.
- `core_rpg_report.py` locates and classifies newly marked tests.
- Mark only tests added here, plus fixtures the criterion needs. Existing tests may be listed as proposals, never bulk-marked.

## Out of Scope
- Bulk marking of existing tests.
- Part 2 of the parent epic (scenario-lane CI rule, `HOLD — pending D-R2`); no `.github/workflows/` change.
- Bulk classification of existing tests; feature-specific proof commitments.

## Acceptance Criteria
1. `pyproject.toml` markers match the doc vocabulary exactly (test enforces).
2. A newly marked test is located and classified by the Epic A report.
3. A deliberately mismatched marker is flagged.
4. An unmarked new/modified core-RPG test is flagged from a diff; an unmarked non-core-RPG test is not.
5. The check always exits 0.

## Related Tickets
- Parent epic: `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (parts 1 and 3 only).
- Depends on TCK-20260930-TEST-TAXONOMY-LEVEL-CONTRACTS.

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §4
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §3–4 (non-binding)
- `docs/testing/test_taxonomy.md`

## Related Stored Artifacts
None.

## Related Code Areas
`pyproject.toml`; `tools/test_architecture/`; `tests/unit/tools/`

## Assumptions / Open Questions
- Uses the report's existing directory/import signals for classification.

## Implementation Notes
`domain(name)`/`level(name)` registered in pyproject. `marker_check` reads the vocabulary from the doc, flags unknown-domain, unknown-level, domain-mismatch, level-placement-mismatch and unmarked-core-rpg (from git diff or --files); always exits 0, no CI wiring. `core_rpg_report` now has per-domain import roots (`DOMAIN_IMPORT_PREFIXES`; the gameplay tuple is derived from it) and lists declared markers per file in the classification layer. No existing test was marked.

## Test Summary
`pytest tests/unit/tools/test_marker_check.py tests/unit/tools/test_marker_vocabulary.py tests/unit/tools/test_core_rpg_report.py`: 49 passed.

## Files Changed
pyproject.toml; tools/test_architecture/marker_check.py; tools/test_architecture/core_rpg_report.py; tests/unit/tools/test_marker_check.py; tests/unit/tools/test_marker_vocabulary.py

## Completion Summary
Markers registered, advisory check (both parts) added, report lists declared markers. Part 2 of the parent epic (D-R2) untouched.
