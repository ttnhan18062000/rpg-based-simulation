---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-TEST-IMPACT-REPORT-V0
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-TEST-IMPACT-REPORT-V0

## Title
Impact report v0: changed paths to domains, recommended levels, tests and lanes, with reasons and impact-unknown

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Given changed paths, report impacted domains/components with reasons, recommended levels, tests and lanes, and an explicit `impact-unknown` list. Never removes a lane; reports selected, lane-triggered and executed separately.

## Scope
- Tool under `tools/test_architecture/`, inputs: ownership map (design notes §3.1), static import graph, content/config rules for `data/worlds/**` and `config/**`.
- `impact-unknown` triggers the PR-eligible fallback described in roadmap §4.3 (nightly-only jobs reported separately).
- "Tactical navigation" has no code root: flagged as `impact-unknown`, no root invented.
- Docstring/doc states the output must never be used to skip a test; no output field designed for skipping.
- No CI wiring.

## Out of Scope
- Any use of the report to skip tests; CI integration.
- Part 2 of the parent epic (scenario-lane CI rule, `HOLD — pending D-R2`); no `.github/workflows/` change.
- Bulk classification of existing tests; feature-specific proof commitments.

## Acceptance Criteria
1. Run on 5 sample changes (local rule, shared substrate, cross-domain, content/config, unmapped) it gives the expected domains and lanes with reasons.
2. The unmapped sample is flagged `impact-unknown`.
3. Selected / lane-triggered / executed are separate fields; no lane is ever removed.
4. The tactical-navigation gap is flagged.

## Related Tickets
- Parent epic: `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (parts 1 and 3 only).
- Depends on TCK-20260930-TEST-TAXONOMY-LEVEL-CONTRACTS (level vocabulary).

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §4
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §3–4 (non-binding)
- `docs/testing/test_taxonomy.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tools/test_architecture/`; `tests/unit/tools/`

## Assumptions / Open Questions
- Lane triggers are read from `.github/workflows/test.yml`, not modified.

## Implementation Notes
Ownership roots come from `core_rpg_report.DOMAIN_IMPORT_PREFIXES` (not restated). Lane-triggered facts are computed from the `changed-files` path filters parsed from the workflow. Reports selected / lane_triggered / executed separately; docstring states it must never be used to skip. Tactical navigation gap flagged in `known_gaps`.

## Test Summary
`pytest tests/unit/tools/test_impact_report.py`: 10 passed (local rule, shared substrate, cross-domain, content/config, unmapped, docs-only, three-fact separation, no-lane-removal, docstring, CLI).

## Files Changed
tools/test_architecture/impact_report.py; tests/unit/tools/test_impact_report.py

## Completion Summary
Impact report v0 added, recommendation only, no CI wiring. Part 2 of the parent epic (D-R2) untouched.
