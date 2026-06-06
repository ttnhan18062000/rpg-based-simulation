# TCK-20260606-PHASE22-3-REPAIR

## Title

Repair World Module v2 normalization count loss

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Fix count loss bug where resources, buildings, services dicts / mappings get converted via list(...) in normalizer, losing counts/quantities. Preserve them as `dict[str, int]` count maps and handle list shorthand normalizing to count `1`.

## Scope

- Create a ticket file and staging artifacts (plan.md, investigation.md, test_plan.md) in `staging_artifacts/TCK-20260606-PHASE22-3-REPAIR/`.
- Update `WorldModuleSpec` in `src/worldmodules/schema.py`:
  - `services` field to accept `Union[Dict[str, int], List[Any]]` instead of only `List[str]`.
- Implement `normalize_count_map` helper in `src/worldmodules/normalizer.py`.
- Update `NormalizedWorldModule` in `src/worldmodules/normalizer.py`:
  - Change `resources`, `buildings`, `services` to `dict[str, int]` (preserving counts).
  - Change `biomes`, `ecologies`, `populations`, `relationships`, `factions` to `tuple[str, ...]` or similar typed sequences.
- Update `ResolvedModuleContribution` in `src/worldassembly/schema.py`:
  - Change `resource_refs`, `building_refs`, `service_refs` to `dict[str, int]`.
  - Change biome, ecology, population, relationship, faction ref fields to `tuple[str, ...]` or `List[str]`.
- Update `WorldAssemblyResolver.resolve_module_contribution` and the merge loop in `WorldAssemblyResolver.assemble` to consume the resolved dict counts.
- Add comprehensive test cases in `tests/unit/worldmodules/test_modules.py` and/or `tests/unit/worldassembly/test_assembly.py`.

## Out of Scope

- Broad rewrite of combat engine or `EntityState`.
- Parsing YAML comments as behavior-determining metadata.

## Acceptance Criteria

- [x] Dict resource counts are preserved.
- [x] Dict building counts are preserved.
- [x] Dict service counts are preserved.
- [x] List shorthand becomes count `1`.
- [x] Invalid counts fail clearly.
- [x] `NormalizedWorldModule` no longer uses `List[Any]` for important v2 refs.
- [x] Existing v1 module tests still pass.
- [x] No test accepts count loss as expected behavior.

## Related Tickets

- None

## Related Docs

- `world_phase_20_28_repair.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldmodules/schema.py`
- `src/worldmodules/normalizer.py`
- `src/worldassembly/schema.py`
- `src/worldassembly/resolver.py`
- `tests/unit/worldmodules/test_modules.py`
- `tests/unit/worldassembly/test_assembly.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- We implemented `normalize_count_map` helper to correctly validate integer values and types, and fail-closed on zero, negative numbers, non-string keys, and duplicate items in a list shorthand.
- `WorldAssemblyResolver.assemble` was updated to iterate on count map items when reconstructing v2 resources/buildings instead of using list checks on raw specs.

## Test Summary

- Added 7 unit tests in `tests/unit/worldmodules/test_modules.py` covering dict normalization, list normalization, duplicate checking, zero checking, and negative value checking.
- Updated `test_v2_module_resolution_and_heuristics` in `tests/unit/worldassembly/test_assembly.py` to assert correct count preservation during end-to-end resolution.

## Files Changed

- `src/worldmodules/schema.py`
- `src/worldmodules/normalizer.py`
- `src/worldassembly/schema.py`
- `src/worldassembly/resolver.py`
- `tests/unit/worldmodules/test_modules.py`
- `tests/unit/worldassembly/test_assembly.py`

## Completion Summary

- Clean implementation of v2 normalizer count preservation is completed. All unit and integration tests pass successfully.
