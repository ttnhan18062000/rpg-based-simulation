---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260606-PHASE24-RESOLVER-EVIDENCE
phase: done
date: 2026-06-06
tags: [phase24, resolver, evidence]
---

# TCK-20260606-PHASE24-RESOLVER-EVIDENCE

## Title

Repair resolver layer claims and add evidence fields

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

- Downgrade resolver-only content families to `RESOLVED_PARTIALLY` if their data does not yet affect runtime behavior.
- Add `resolver_evidence` and `runtime_consumer_evidence` fields to the `ContentFamilyMatrixEntry` model and `CONTENT_USAGE_MATRIX` to make this separation clear.
- Update report generator to output these fields.

## Scope

- Create a ticket file and staging artifacts (plan.md, investigation.md, test_plan.md) in `staging_artifacts/TCK-20260606-PHASE24-RESOLVER-EVIDENCE/`.
- Modify `ContentFamilyMatrixEntry` inside `src/content/matrix.py` to add `resolver_evidence` and `runtime_consumer_evidence`.
- Update `CONTENT_USAGE_MATRIX` entries inside `src/content/matrix.py` to:
  - Populate `resolver_evidence` and `runtime_consumer_evidence`.
  - Downgrade foundation/living/social resolver-only families to `RESOLVED_PARTIALLY` if they don't affect runtime.
- Update `generate_matrix_report` in `src/content/matrix.py` to include columns for these new evidence fields.
- Update unit tests in `tests/unit/content/test_content_usage_matrix.py` to verify:
  - `test_living_family_marked_resolved_partially_until_runtime_consumer`
  - `test_foundation_resolver_fetches_known_ids`
  - `test_missing_foundation_id_fails_clearly`
  - `test_social_resolver_resolves_relationships_without_claiming_all_runtime_usage`

## Out of Scope

- Implementing runtime behavioral logic for drive/need/sense profiles.
- Parsing YAML comments as behavior-determining metadata.

## Acceptance Criteria

- [x] Resolver tests prove fetch/merge/default behavior.
- [x] Matrix does not claim runtime behavior prematurely.
- [x] Runtime-authoritative status is reserved for actual consumer tests.
- [x] Resolver evidence and runtime consumer evidence are separate columns in ContentFamilyMatrixEntry and the matrix report.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28_repair.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/content/matrix.py`
- `tests/unit/content/test_content_usage_matrix.py`
- `tests/unit/content/test_resolvers.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Separated resolver and runtime consumer evidence fields cleanly in ContentFamilyMatrixEntry schema.

## Test Summary

- Added `test_living_family_marked_resolved_partially_until_runtime_consumer`, `test_foundation_resolver_fetches_known_ids`, `test_missing_foundation_id_fails_clearly`, and `test_social_resolver_resolves_relationships_without_claiming_all_runtime_usage`.
- All 133 content unit tests passed successfully.

## Files Changed

- `src/content/matrix.py`
- `tests/unit/content/test_content_usage_matrix.py`
- `docs/mechanics/content_usage_matrix.md`

