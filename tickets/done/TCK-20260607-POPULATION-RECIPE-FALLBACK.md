# TCK-20260607-POPULATION-RECIPE-FALLBACK

## Title
Document and harden PopulationRecipeResolver silent archetype fallback

## Status
DONE

## Tier
hotfix

## Type
hardening

## Priority
P2

## Request Summary
`PopulationRecipeResolver.resolve()` in `src/content/resolver.py` silently falls back to treating a recipe ID as a direct archetype ID when no recipe is found in the catalog. This behavior is undocumented, untested, and can mask misconfigurations in world module YAML files — a population_group that references a non-existent recipe ID will silently produce one entity instead of raising an error.

## Scope

### Root Cause

`src/content/resolver.py` lines 574-579 (approximate):
```python
arch = self.catalog.find_archetype(recipe_id)
if arch is None:
    # Silent fallback: treat recipe_id as a direct archetype ID
    return [(recipe_id, 1)], []
```

When `recipe_id` is neither in the recipe catalog nor in the archetype catalog, the resolver returns `[(recipe_id, 1)]` with `[]` errors — a fully silent fallback. Downstream code then tries to instantiate an archetype from this ID and fails at a later stage with a less-informative error, or silently creates a broken entity profile.

### Intended Behavior

The resolver should distinguish three cases:
1. `recipe_id` found in recipe catalog → expand to archetype list (current correct path)
2. `recipe_id` not in recipes, but IS a valid archetype ID → single-entity shortcut (acceptable, but must be documented and tested)
3. `recipe_id` not in recipes AND not a valid archetype → error, should be returned as a resolver warning/error

### Required changes

1. **Document the fallback contract** in a code comment at the fallback site, stating exactly when it applies and that it is intentional.
2. **Validate the fallback**: confirm the archetype ID is valid before returning `[(recipe_id, 1)]`. If invalid, return `([], [ResolverError(f"unknown recipe and archetype id: {recipe_id}")])`.
3. **Add tests** for all three cases above in `tests/unit/content/test_resolver.py`.
4. **Update parity ledger**: add or update the entry in `docs/parity_ledger/town_resource.yaml` for this resolver contract.

### Is the fallback intentional?
Based on the Phase 20-28 repair, world module YAML uses `population_group.population_recipe_id` which should always resolve via the recipe catalog. If a valid archetype ID is also acceptable as a shorthand, this must be stated explicitly. The fix should either:
- Make it a documented, tested, supported shorthand (Option A)
- Or eliminate the fallback and require recipe IDs to always match a recipe (Option B)

Recommendation: **Option A** — the shorthand is a reasonable ergonomic aid. Document and validate it.

## Out of Scope
- Do not change the resolver interface or return type.
- Do not change how valid recipes are resolved.
- Do not modify world module YAML files.

## Acceptance Criteria
- [ ] Fallback to direct archetype ID is explicitly documented with a comment
- [ ] Fallback validates that the archetype ID actually exists; returns a resolver warning if not
- [ ] `test_resolver.py` covers: (1) valid recipe, (2) valid direct archetype, (3) unknown ID → error
- [ ] All existing tests still pass
- [ ] Parity ledger entry exists for this resolver behavior

## Related Tickets
- TCK-20260607-STRICT-MODE-PRODUCTION (same audit session)

## Related Docs
- `docs/mechanics/03_economic_laws.md` — population resolution
- `world_phase_20_28_repair.md` Phase 26 (population group handling)

## Related Stored Artifacts
None

## Related Code Areas
- `src/content/resolver.py` — `PopulationRecipeResolver.resolve()` fallback block
- `tests/unit/content/test_resolver.py`
- `docs/parity_ledger/town_resource.yaml`

## Assumptions / Open Questions
- Does any existing world module YAML use a direct archetype ID instead of a recipe ID? If yes, the fallback is actively relied upon and Option A is mandatory.

## Implementation Notes
Read `data/content/world_modules/*.yaml` and check `population_recipe_id` values against the recipe catalog to determine if the fallback is currently exercised by real data.

## Test Summary
Run `pytest tests/unit/content/test_resolver.py -q`.

## Files Changed
- `src/content/resolver.py` (add fallback validation + comment)
- `tests/unit/content/test_resolver.py` (add three-case coverage)
- `docs/parity_ledger/town_resource.yaml` (add/update entry)

## Completion Summary
Done. 169 tests pass.
