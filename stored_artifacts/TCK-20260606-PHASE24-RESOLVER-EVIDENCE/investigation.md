# Investigation - Phase 24 Resolver layer claims and evidence fields

## Current State Analysis

1. **Resolver-only family states**:
   - Families like `living/need_profiles`, `living/sense_profiles`, `living/drive_profiles`, `living/body_models`, `foundation/relationship_axes` do not affect runtime simulation behavior directly yet.
   - We must make sure they are set to `RESOLVED_PARTIALLY` inside `CONTENT_USAGE_MATRIX` in `src/content/matrix.py`.
   - Let's check what their current implementation state is. Many might already be `RESOLVED_PARTIALLY`, but we need to ensure none are set to `RUNTIME_AUTHORITATIVE` without real runtime consumer tests.

2. **Matrix entry schema fields**:
   - Currently, `ContentFamilyMatrixEntry` does not contain `resolver_evidence` and `runtime_consumer_evidence` as explicit separate fields.
   - We will add them:
     - `resolver_evidence: Optional[str] = Field(None)`
     - `runtime_consumer_evidence: Optional[str] = Field(None)`
   - We will update `generate_matrix_report` to include these columns.
