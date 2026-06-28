# Test Plan: TCK-20260627-P2C-ARCHETYPE-DIST
# Add 6–8 archetypes for underrepresented roles

## Regression Surface (existing tests that must pass)

- `tests/integration/content/test_expansion_gate.py` — loads full catalog; will catch invalid profile refs
- `tests/integration/content/test_strict_world_matrix.py` — content matrix integrity
- `tests/integration/worldassembly/test_real_content_world_modules.py` — exercises archetypes through world modules
- `tests/unit/entity/test_entity_archetypes.py` — hero archetype coverage (unaffected; mob-only change)
- `tests/integration/certification/test_catalog_arena_smoke.py` — smoke-tests archetype/catalog loading

## New Tests Required (per AC)

### AC: ≥ 27 total archetype entries
Assert `len(repo.entity_archetypes) >= 27` after loading the catalog.

### AC: Scout/ranger role count ≤ 3/21 proportion in final set  
Assert `count(role in ["scout","ranger"]) / total <= (3/21 * total / total)` — i.e., the scout+ranger fraction has not increased vs baseline.

### AC: Mage role count ≥ 2
Assert `count(role == "mage") >= 2`.

### AC: Each new archetype assigned to a registered faction
The CatalogValidator already enforces this via `_validate_archetype_relations`. Running validator = passing this AC.

### AC: `make world-validate` passes
Run `make world-validate` after implementation (or equivalent pytest scope).

### AC: No ContentUsageMatrix drift
`pytest tests/ -k content -m "not slow"` passes.

## Scoped Pytest Commands

```bash
# Primary scoped run — content catalog tests
pytest tests/integration/content/ -m "not slow" -v

# Archetype-specific unit tests
pytest tests/unit/entity/test_entity_archetypes.py -v

# Broader content regression (if above pass)
pytest tests/integration/ -k "archetype or catalog or content" -m "not slow" -v
```

## Distribution Assertion (manual check)

```python
import yaml
from collections import Counter
data = yaml.safe_load(open("data/content/entities/entity_archetypes.yaml"))
roles = Counter(a["role"] for a in data)
total = sum(roles.values())
print(f"Total: {total}")
print(f"Mage count: {roles['mage']} (need >= 2)")
print(f"Scout+Ranger: {roles['scout'] + roles.get('ranger', 0)} / {total}")
for role, count in roles.most_common():
    pct = count/total*100
    print(f"  {role}: {count} ({pct:.1f}%)")
```

## Anti-Drift Test Guards

- If any profile ID is misspelled in a new archetype, `test_expansion_gate.py` or `test_strict_world_matrix.py` will raise CAT-REL-011 ERROR
- The catalog validator's `_validate_archetype_relations` is the primary referential-integrity guard — runs on every full catalog load
