# TCK-20260609-PRESERVE-ASSEMBLY-TESTS

## Title
Audit and guard existing worldassembly tests against duplication by new strict matrix

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Existing worldassembly tests already verify region merging, WorldSpec cleanliness, duplicate region collision, deterministic provenance manifests, CompileContext serialization, and CLI integration. New strict matrix tests (Phase 31) must not duplicate these behaviors. This task audits existing test coverage, documents what is owned by which suite, and adds guards (comments/markers) so reviewers and future agents can identify ownership boundaries without scanning all tests.

## Scope
- Review existing tests in tests/unit/worldassembly/, tests/integration/worldassembly/, tests/certification/, tests/arena/
- Identify which behaviors are already tested (region merge, WorldSpec, provenance, CompileContext, CLI)
- Add pytest markers to existing worldassembly tests where not already marked (worldassembly marker)
- Update docs/testing/v2_test_taxonomy.md to include the ownership boundary for worldassembly vs strict matrix tests
- Confirm no duplicate "basic assembly works" or "basic catalog loads" tests exist in the new test files

## Out of Scope
- Modifying existing test logic
- Rewriting any test
- Creating new test files

## Acceptance Criteria
- [ ] Existing worldassembly tests remain unchanged in behavior
- [ ] pytest worldassembly marker is applied to relevant existing tests
- [ ] docs/testing/v2_test_taxonomy.md notes the worldassembly test ownership boundary
- [ ] No duplicate "basic assembly works" or "basic catalog loads" test is added as part of this ticket

## Related Tickets
- TCK-20260609-STRICT-WORLD-MATRIX (successor — must respect these boundaries)

## Related Docs
- docs/testing/v2_test_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/unit/worldassembly/
- tests/integration/worldassembly/
- docs/testing/v2_test_taxonomy.md

## Assumptions / Open Questions
- docs/testing/v2_test_taxonomy.md exists from earlier phases

## Implementation Notes
- Added `worldassembly` marker to pyproject.toml markers list
- Added `pytestmark = pytest.mark.worldassembly` at module level in all 7 worldassembly test files
- No test logic was changed — only marker added
- Pre-existing CAT-REL-099 failures in 9 tests are unchanged (moon_cult_ruins pre-existing defect)
- Updated v2_test_taxonomy.md with ownership boundary table and strict-matrix duplication rule

## Test Summary
No new tests added (hotfix tier). Existing worldassembly tests: 33 pass, 9 fail pre-existing.
Marker collection: 52 tests collected with `-m worldassembly`.

## Files Changed
- `pyproject.toml` (worldassembly marker added)
- `tests/unit/worldassembly/test_assembly.py` (pytestmark)
- `tests/unit/worldassembly/test_provenance.py` (pytestmark)
- `tests/unit/worldassembly/test_resolver.py` (pytestmark)
- `tests/unit/worldassembly/test_archetype_preservation.py` (pytestmark)
- `tests/integration/worldassembly/test_real_content_world_modules.py` (pytestmark)
- `tests/integration/worldassembly/test_real_content_world_compositions.py` (pytestmark)
- `tests/integration/worldassembly/test_real_module_normalized_snapshot.py` (pytestmark)
- `docs/testing/v2_test_taxonomy.md` (ownership boundary section)

## Completion Summary
All worldassembly test files now carry the worldassembly marker. Ownership boundaries documented
in v2_test_taxonomy.md. No test behavior changed. Pre-existing CAT-REL-099 failures unaffected.
