# TCK-20260608-ADAPTER-HEURISTIC-USAGE

## Title
Add AdapterHeuristicUsage dataclass; replace heuristic_count with heuristic_usages tuple

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
AdapterProjectionResult currently exposes only heuristic_count (int), making it impossible to audit which records used heuristics, which adapter triggered them, or whether the heuristic type is compatible with the selected runtime mode. This task introduces a new frozen AdapterHeuristicUsage dataclass capturing record_id, family, adapter, heuristic_type, reason, and mode, then replaces heuristic_count in AdapterProjectionResult with heuristic_usages: tuple[AdapterHeuristicUsage, ...]. A compatibility property heuristic_count = len(heuristic_usages) may be retained. All four adapter classes must emit AdapterHeuristicUsage entries for every heuristic inference they perform.

## Scope
- Define frozen dataclass AdapterHeuristicUsage with fields: record_id, family, adapter, heuristic_type, reason, mode: RuntimeContentMode
- Replace heuristic_count: int in AdapterProjectionResult with heuristic_usages: tuple[AdapterHeuristicUsage, ...]
- Add optional compatibility property heuristic_count returning len(heuristic_usages)
- Update CatalogToItemRegistryAdapter to emit AdapterHeuristicUsage for use_kind inference and class_fit inference
- Update CatalogToServiceRegistryAdapter to emit AdapterHeuristicUsage for generated-service heuristic
- Update CatalogToResourceRegistryAdapter to emit AdapterHeuristicUsage for required_tool and base_difficulty defaults
- Update ArchetypeToEnemyRegistryAdapter to emit AdapterHeuristicUsage for fallback enemy entries if applicable
- Add tests/unit/content/test_adapter_heuristic_reporting.py covering all adapter heuristic cases

## Out of Scope
- Removing legacy fallback logic
- Changing heuristic inference logic or adding new heuristics
- Modifying CATALOG_STRICT rejection behavior (covered in RUNTIME-MODE-EXPLICIT ticket)

## Acceptance Criteria
- [ ] AdapterHeuristicUsage frozen dataclass exists with all six fields (record_id, family, adapter, heuristic_type, reason, mode)
- [ ] AdapterProjectionResult.heuristic_usages is a tuple[AdapterHeuristicUsage, ...] not an int
- [ ] heuristic_count property returns len(heuristic_usages) as a compatibility shim
- [ ] Item adapter records use_kind heuristic with the record_id of the inferred item
- [ ] Item adapter records class_fit heuristic with the record_id
- [ ] Resource adapter records required_tool default heuristic
- [ ] Resource adapter records base_difficulty default heuristic
- [ ] Service adapter records generated-service heuristic
- [ ] CATALOG_STRICT mode fails if heuristic_usages is non-empty
- [ ] CATALOG_WITH_COMPATIBILITY mode returns populated heuristic_usages
- [ ] Tests in test_adapter_heuristic_reporting.py cover all of the above

## Related Tickets
- TCK-20260607-RUNTIME-CONTENT-MODE (predecessor — created AdapterProjectionResult with heuristic_count)
- TCK-20260608-RUNTIME-MODE-EXPLICIT (dependency — CATALOG_STRICT rejection logic lives there)

## Related Docs
- docs/engine/authoritative_pipeline.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/modes.py
- src/core/registries.py
- tests/unit/content/test_adapter_heuristic_reporting.py

## Assumptions / Open Questions
- ArchetypeToEnemyRegistryAdapter may or may not perform heuristic projection; must inspect source before deciding whether to emit usage records from it
- heuristic_count as a compatibility property is acceptable; it must not be the source of truth

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
