# Implementation Plan - Phase 24 Resolver layer claims and evidence fields

## Proposed Changes

### Content Usage Matrix

#### [MODIFY] [matrix.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content/matrix.py)
- Update `ContentFamilyMatrixEntry` to add:
  - `resolver_evidence: Optional[str] = Field(None, description="Resolver evidence text or None")`
  - `runtime_consumer_evidence: Optional[str] = Field(None, description="Runtime consumer evidence text or None")`
- Update all dictionary entries in `CONTENT_USAGE_MATRIX` to supply these fields:
  - Set `resolver_evidence` to the resolving component and test.
  - Set `runtime_consumer_evidence` to the compile context or runtime consumer if it exists, or `"None"` / `"None yet"`.
  - Ensure all foundation/living/social resolver-only families are marked `RESOLVED_PARTIALLY`.
- Update `generate_matrix_report` to format these two new columns instead of combining them.

### Tests

#### [MODIFY] [test_content_usage_matrix.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/content/test_content_usage_matrix.py)
- Add tests:
  - `test_living_family_marked_resolved_partially_until_runtime_consumer`
  - `test_foundation_resolver_fetches_known_ids`
  - `test_missing_foundation_id_fails_clearly`
  - `test_social_resolver_resolves_relationships_without_claiming_all_runtime_usage`

## Verification Plan

### Automated Tests
- Run content unit tests:
  ```bash
  pytest tests/unit/content/
  ```
