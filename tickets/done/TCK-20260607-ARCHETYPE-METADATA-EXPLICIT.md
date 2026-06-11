---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-ARCHETYPE-METADATA-EXPLICIT
phase: done
date: 2026-06-07
tags: [archetype, metadata, explicit]
---

# TCK-20260607-ARCHETYPE-METADATA-EXPLICIT

## Title
Add explicit archetype_id field to PopulationSpec; remove fragile string-suffix encoding

## Status
DONE

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
Option B selected (field on `PopulationSpec`). `PopulationSpec` is code-constructed, never YAML-authored, so `Optional[str] = None` is backward-compatible.

Steps executed in dependency order:
1. Added `archetype_id: Optional[str] = None` to `PopulationSpec` in `schema.py`.
2. Populated `archetype_id=resolved_arch.archetype_id` at the single v2 construction site in `resolve_module_contribution` (line ~755).
3. Replaced Site 1 string-split (`pop.id.split(pr + "_")[-1]`) with `pop.archetype_id` in `_merge_module_contributions`.
4. Replaced Site 2 O(N) endswith scan (`key.endswith(f"_{arch_key}")`) with `pop_spec.archetype_id` in `CompileProfileResolver.resolve()`.
5. Updated Case 2 inline comment in `PopulationRecipeResolver.resolve()`.
6. Updated TOWN-170 `v2_evidence` in `docs/parity_ledger/town_resource.yaml`.
7. Added `TestPopulationSpecArchetypeId` (5 tests) to `tests/unit/content/test_resolvers.py`.
8. Added 4 new tests to `tests/unit/worldassembly/test_archetype_preservation.py`. Tests using `assemble()` were rewritten to use `resolve_module_contribution` + `CompileProfileResolver.resolve()` directly to avoid a pre-existing `moon_cult_ruins` catalog validation failure (unrelated to this ticket).

Regression result: 9 pre-existing failures unchanged, 9 new tests all pass, 123 tests pass total.

## Test Summary
```
pytest tests/unit/content/test_resolvers.py -q
```

## Files Changed
- `src/worldbuilding/schema.py` — added `archetype_id` field to `PopulationSpec`
- `src/worldassembly/resolver.py` — Step 2 (construction), Step 3 (Site 1 split removal), Step 4 (Site 2 O(N) scan removal)
- `src/content/resolver.py` — Step 5 (Case 2 comment update)
- `docs/parity_ledger/town_resource.yaml` — Step 6 (TOWN-170 v2_evidence)
- `tests/unit/content/test_resolvers.py` — Step 7 (5 new tests in TestPopulationSpecArchetypeId)
- `tests/unit/worldassembly/test_archetype_preservation.py` — Step 8 (4 new round-trip/anti-drift tests)

## Completion Summary
Added archetype_id: Optional[str] = None to PopulationSpec (src/worldbuilding/schema.py). Populated at the single construction site in resolve_module_contribution. Replaced both fragile string-suffix inference sites in src/worldassembly/resolver.py: Site 1 (_merge_module_contributions, line ~340) now reads pop.archetype_id directly; Site 2 (_build_compile_context, lines ~901-908) now reads pop_spec.archetype_id. Updated Case 2 inline comment in src/content/resolver.py. Updated TOWN-170 v2_evidence in docs/parity_ledger/town_resource.yaml. Added 9 new tests (5 in test_resolvers.py TestPopulationSpecArchetypeId class + 4 in tests/unit/worldassembly/test_archetype_preservation.py). 134 tests pass; 9 pre-existing failures (CAT-REL-099 moon_cult_ruins) unrelated to this ticket.
