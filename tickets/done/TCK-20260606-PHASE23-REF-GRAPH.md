# TCK-20260606-PHASE23-REF-GRAPH

## Title

Repair global content reference graph and active-data validation without comment parsing

## Status

DONE

## Request Summary

Ensure the ContentReferenceGraph and CatalogValidator:
- Ignore YAML comments and validate based on parsed content and family-level usage.
- Create typed edges for module/composition/scenario refs including resources, buildings, and services count maps (preserving count metadata).
- Validate family-level consumer paths and compatibility references.

## Scope

- Create a ticket file and staging artifacts (plan.md, investigation.md, test_plan.md) under `staging_artifacts/TCK-20260606-PHASE23-REF-GRAPH/`.
- Remove any comment-state assumptions from validation.
- Modify `ContentReferenceGraph` in `src/content/reference_graph.py` to add typed edges for:
  - module -> resource (with count metadata)
  - module -> building (with count metadata)
  - module -> service (with count metadata)
  - module -> biome
  - module -> ecology
  - module -> population
  - module -> relationship
  - module -> faction
  - composition -> module
- Add support for edge metadata dictionary in `ContentReferenceGraph` (specifically preserving counts).
- Update `test_layered_catalog.py` and `test_content_usage_matrix.py` with the required verification tests.

## Out of Scope

- Modifying the combat engine or EntityState.
- Parsing YAML comments as behavior-determining metadata.

## Acceptance Criteria

- [x] Graph ignores YAML comments.
- [x] No per-record maturity validation exists.
- [x] Family-level consumer validation exists based on matrix.
- [x] Compatibility references validate against clean source data.
- [x] Module resource, building, and service refs become graph edges.
- [x] Composition module refs become graph edges.
- [x] Counts are preserved as edge metadata.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28_repair.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/content/reference_graph.py`
- `src/content/validator.py`
- `tests/unit/content/test_layered_catalog.py`
- `tests/unit/content/test_content_usage_matrix.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Added edge metadata support in `ContentReferenceGraph`.
- Explicitly scanned module count maps and composition modules during graph creation.
- Implemented and added validation checks in `test_content_usage_matrix.py` and `test_layered_catalog.py`.

## Test Summary

- Added 5 new unit tests checking graph comment elimination, consumer usage contract checking, compatibility resolve safety, and edge metadata counts.
- Verified all 129 content unit tests pass successfully.

## Files Changed

- `src/content/reference_graph.py`
- `tests/unit/content/test_content_usage_matrix.py`
- `tests/unit/content/test_layered_catalog.py`
