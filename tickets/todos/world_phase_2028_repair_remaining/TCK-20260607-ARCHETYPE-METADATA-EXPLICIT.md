# TCK-20260607-ARCHETYPE-METADATA-EXPLICIT

## Title
Add explicit archetype_id field to PopulationSpec; remove fragile string-suffix encoding

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`PopulationSpec` has no `archetype_id` field. When `PopulationRecipeResolver` handles
Case 2 (direct archetype shorthand), the archetype ID is inferred by stripping a generated
suffix from the population ID string. This is fragile — any ID format change silently
breaks the inference without a test failure.

The archetype identity should be an explicit, typed field on `PopulationSpec` or on a
companion `ExpandedPopulationMember` record.

## Scope

### Investigation first
Check whether `PopulationSpec` is deserialized from YAML content files or constructed
programmatically. This determines whether we add a field to the Pydantic model or to
the expanded-member record.

### Option A — Add `archetype_id: Optional[str]` to `PopulationSpec`

If `PopulationSpec` is authored in YAML:
```python
class PopulationSpec(BaseModel):
    archetype_id: Optional[str] = None  # explicit archetype reference
    ...
```

The resolver reads `spec.archetype_id` instead of inferring from string suffix.
YAML authoring docs updated to document the field.

### Option B — Add `archetype_id` to `ExpandedPopulationMember` result

If the archetype ID is an expansion artifact (computed, not authored):
```python
@dataclass(frozen=True)
class ExpandedPopulationMember:
    entity_id: str
    archetype_id: str   # always set; never inferred from string
    count: int
```

The resolver returns this record instead of a raw string, carrying explicit provenance.

### After choosing the option

- Remove string-suffix inference from `PopulationRecipeResolver`
- Update the Case 2 docstring
- Update `test_case2_direct_archetype_id_returns_single_entity` in `test_resolvers.py`
- Add a test: "archetype_id survives round-trip through expand → resolve"

## Out of Scope
- Do not change the `RecipeSpec` schema (handles Case 1 — recipe expansion)
- Do not change the 3-case contract itself (just tighten Case 2 implementation)
- Do not add new YAML fields unless Option A is chosen

## Acceptance Criteria
- [ ] `PopulationSpec` or its expansion record carries explicit `archetype_id`
- [ ] `PopulationRecipeResolver` no longer infers archetype ID from string suffix
- [ ] Updated Case 2 docstring
- [ ] Test covers archetype_id round-trip
- [ ] All existing resolver tests pass

## Related Tickets
- TCK-20260607-RESOLVER-BOUNDARY (companion — typed boundaries)

## Related Docs
- `world_phase_20_28_repair_remaining.md` R4.1, R4.2
- `docs/mechanics/01_entity_anatomy.md` — entity identity

## Related Code Areas
- `src/content/resolver.py` — `PopulationRecipeResolver`
- `src/worldmodules/normalizer.py` — PopulationSpec
- `tests/unit/content/test_resolvers.py`

## Assumptions / Open Questions
- Does `PopulationSpec` come from YAML or is it always constructed in code? Answer determines Option A vs B.
- What is the current string-suffix format? (E.g., `"hungry_wolf_pop_001"` → strip `_pop_001`?)

## Implementation Notes
9-phase standard. Investigation phase must read actual `PopulationSpec` source and find the string-suffix inference logic before selecting Option A or B.

## Test Summary
```
pytest tests/unit/content/test_resolvers.py -q
```

## Files Changed
- `src/content/resolver.py`
- `src/worldmodules/normalizer.py` (possibly)
- `tests/unit/content/test_resolvers.py`

## Completion Summary
(to be filled)
