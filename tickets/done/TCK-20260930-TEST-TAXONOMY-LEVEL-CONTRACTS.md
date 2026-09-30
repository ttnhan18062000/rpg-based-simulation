---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-TEST-TAXONOMY-LEVEL-CONTRACTS
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-TEST-TAXONOMY-LEVEL-CONTRACTS

## Title
Rewrite the test taxonomy doc with level contracts, technique criteria, evidence classes, placement and the oracle principle

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/testing/test_taxonomy.md` describes legacy-parity markers only. Agents cannot tell which level, harness or placement fits a change. Rewrite it in place. It is the single definition of the domain/level marker vocabulary that the marker ticket registers.

## Scope
- Level contracts for the five levels (roadmap §4.1; design notes §3.2), each answering: which level and harness, and how it is reported.
- Technique criteria (§3.3), evidence classification (roadmap §4.2), placement, the oracle principle (oracle is a document, not a session).
- A machine-readable marker vocabulary section (domain and level values) as the ONE definition; `pyproject.toml` only registers it.
- Keep the valid worldassembly and performance sections; existing links to the doc still resolve.
- Classify `tests/mutation/baselines/` (data, not tests) on purpose (Epic A handoff).
- Run `make knowledge-index-update`.

## Out of Scope
- Registering markers or writing the check (TCK-20260930-TEST-DOMAIN-LEVEL-MARKERS-ADVISORY-CHECK).
- Part 2 of the parent epic (scenario-lane CI rule, `HOLD — pending D-R2`); no `.github/workflows/` change.
- Bulk classification of existing tests; feature-specific proof commitments.

## Acceptance Criteria
1. The doc answers "which level and harness, and how is it reported" for every level.
2. All existing links to `docs/testing/test_taxonomy.md` resolve.
3. The marker vocabulary is defined once, in a parseable section.
4. `tests/mutation/baselines/` is classified in the doc.
5. Valid worldassembly and performance sections are retained.

## Related Tickets
- Parent epic: `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (parts 1 and 3 only).
- Feeds TCK-20260930-TEST-DOMAIN-LEVEL-MARKERS-ADVISORY-CHECK, TCK-20260930-TEST-SCENARIO-HELPER-AND-REPLAY-DIFF, TCK-20260930-TEST-IMPACT-REPORT-V0.

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §4
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §3–4 (non-binding)
- `docs/testing/test_taxonomy.md`

## Related Stored Artifacts
None.

## Related Code Areas
`docs/testing/`

## Assumptions / Open Questions
- Legacy parity markers stay documented; they are not removed.

## Implementation Notes
Kept §1-§4 (legacy markers, worldassembly, performance) with their numbering so existing references hold; added §5 levels, §6 techniques, §7 evidence classes, §8 placement (incl. `tests/mutation/baselines/` as data), §9 oracle principle, §10 the single machine-readable marker vocabulary block.

## Test Summary
`tests/unit/tools/test_marker_vocabulary.py` parses the §10 block; `validate_frontmatter.py` on the doc: OK.

## Files Changed
docs/testing/test_taxonomy.md

## Completion Summary
Taxonomy doc rewritten in place; vocabulary defined once in §10. Part 2 of the parent epic (D-R2) untouched.
