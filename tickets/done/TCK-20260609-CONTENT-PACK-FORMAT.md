# TCK-20260609-CONTENT-PACK-FORMAT

## Title
Define content pack format and manifest schema for structured horizontal expansion

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Without a defined pack format, new content files appear scattered without integration proof. A content pack bundles foundation additions, living additions, social additions, entity archetypes, populations, world content, modules, and scenarios into a single manifest with state markers, required dependencies, and a strict validation mode result. This prevents content from being added without at least one scenario or composition consuming it.

## Scope
- Define `ContentPackManifest` schema in `src/content/pack_manifest.py` (or equivalent) with fields: pack_id, display_name, version, dependencies (list of pack IDs), included_families (dict of family → list of IDs), state_markers, strict_validation_result, sample_compositions (list of composition IDs)
- Each pack must have at least one composition or scenario consuming it (enforced by manifest validation)
- Pack must be enable/disable-able without breaking other packs
- Add schema validation tests: valid manifest, missing dependency fails, no consuming composition fails
- Document pack format in docs/content/content_pack_format.md

## Out of Scope
- Creating the first actual content pack (that is TCK-20260609-FRONTIER-EXTENDED-PACK)
- Changing existing catalog structure

## Acceptance Criteria
- [ ] ContentPackManifest schema exists with all required fields
- [ ] Pack dependencies are validated (missing dependency fails)
- [ ] Pack can be enabled/disabled
- [ ] Pack with no consuming composition or scenario fails validation
- [ ] Pack does not introduce new mechanisms without explicit design ticket (enforced by schema — no executable fields)
- [ ] Schema validation tests pass
- [ ] docs/content/content_pack_format.md exists

## Related Tickets
- TCK-20260609-CONTENT-EXPANSION-GATE (dependency — gate must pass before packs are added)
- TCK-20260609-FRONTIER-EXTENDED-PACK (successor)

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/content/pack_manifest.py (new)
- tests/unit/content/test_content_pack_manifest.py (new)
- docs/content/content_pack_format.md (new)

## Assumptions / Open Questions
- Pack format is YAML-based, consistent with existing catalog YAML files

## Implementation Notes
ContentPackManifest uses frozen Pydantic BaseModel with extra="forbid". Consumer requirement enforced by @model_validator — no sample_compositions and no sample_scenarios → ValidationError at construction. pack_id enforced via regex pattern=r"^[a-z][a-z0-9_]*$". ContentPackManifestValidator handles dependency checking (runtime, not schema). ContentPackValidationError carries pack_id + errors list.

## Test Summary
17/17 unit tests pass. Covers valid manifests, no-consumer error, unknown fields, frozen model, enabled/disabled, pack_id format, dependency validation.

## Files Changed
- src/content/pack_manifest.py (new — ContentPackManifest, ContentPackManifestValidator, ContentPackValidationError)
- tests/unit/content/test_content_pack_manifest.py (new — 17 tests)
- docs/content/content_pack_format.md (new — YAML format spec)

## Completion Summary
All acceptance criteria met. Schema exists with all required fields. Dependency validation implemented. enabled/disabled support. No-consumer validation. No executable fields possible (Pydantic extra=forbid). Docs created.
