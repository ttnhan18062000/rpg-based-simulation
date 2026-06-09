# TCK-20260609-HARDCODED-GAMEPLAY-GUARD

## Title
Add architecture test preventing new gameplay content in Python hardcoded fallback maps

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
There is a risk that new gameplay content (enemies, items, recipes, regions, services) gets added only to Python fallback dicts and never to the catalog, creating a content graveyard that bypasses the new catalog pipeline. This task adds a static architecture test that scans the codebase for hardcoded gameplay IDs, checks them against the migration map, and fails if any new unmapped gameplay ID appears in source fallback maps. Existing fallback records are allowed if they are listed in the migration map.

## Scope
- Add `tests/architecture/test_no_new_hardcoded_gameplay_truth.py`
- Static scan targets: enemy registry fallback maps, item registry fallback maps, recipe registry fallback maps, region fallback maps, service fallback maps, test-only content factories that define gameplay IDs outside test paths
- Cross-reference found IDs against `data/content/compatibility/migration_map.yaml` (from TCK-20260609-MIGRATION-MAP-YAML)
- Allow: enum definitions, test fixture IDs inside test paths, compatibility adapters, migration map entries, non-gameplay constants
- Forbid: new gameplay ID in source fallback map with no catalog/compatibility mapping
- Failure message must name the specific file, ID, and missing migration map entry

## Out of Scope
- Scanning generated artifacts
- Removing existing hardcoded records (migration map handles those)
- Modifying any content files

## Acceptance Criteria
- [ ] tests/architecture/test_no_new_hardcoded_gameplay_truth.py exists and runs in the architecture suite
- [ ] Existing fallback records are allowed if listed in migration_map.yaml
- [ ] New unmapped gameplay IDs in source fallback maps fail the test
- [ ] Test fixture IDs are allowed only in test/ paths
- [ ] Failure message points to migration map or catalog family
- [ ] Guard does not scan generated artifacts or graphify-out/

## Related Tickets
- TCK-20260609-MIGRATION-MAP-YAML (dependency — migration map must exist before guard can use it)
- TCK-20260609-REGISTRY-BOOTSTRAP-MODES (related — bootstrap uses the same fallback detection)

## Related Docs
- docs/architecture/ (ADRs)

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/test_no_new_hardcoded_gameplay_truth.py (new)
- data/content/compatibility/migration_map.yaml
- src/core/registries.py

## Assumptions / Open Questions
- Migration map YAML format is defined in TCK-20260609-MIGRATION-MAP-YAML before this ticket is implemented

## Implementation Notes
Used dict-literal regex `^\s+"([\w_]+)"\s*:\s*(Item|Resource|Enemy|Recipe|Service|Region)Def\s*\(` to distinguish fallback map entries from adapter-style assignments. Pre-existing IDs not in migration_map captured in KNOWN_HARDCODED_BASELINE (29 entries). Stale-baseline guard ensures baseline shrinks as migration_map grows.

## Test Summary
5/5 architecture tests pass. Main gate, two smoke tests, stale baseline guard, migration_map existence check.

## Files Changed
- tests/architecture/test_no_new_hardcoded_gameplay_truth.py (new — 5 tests)

## Completion Summary
All acceptance criteria met. Guard active in architecture suite. New dict-literal gameplay IDs not in migration_map or KNOWN_HARDCODED_BASELINE fail the test. Failure messages name file, ID, family, and remediation path.
