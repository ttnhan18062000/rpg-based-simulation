---
status: active
artifact_type: investigation
ticket_id: TCK-20260627-P3D-CATALOG-BROWSER
date: 2026-06-27
---

# Investigation — TCK-20260627-P3D-CATALOG-BROWSER

## Summary

Both deliverables in this ticket have well-prepared foundations in the codebase.
No architectural gaps need to be resolved before implementation.

---

## 1. Catalog Browser

### `CatalogRepository.get_all_ids_by_type()` already exists

`src/content/repository.py` lines 516–554 expose:

```python
def get_all_ids_by_type(self, type_name: str) -> List[str]:
```

The method accepts a type key (e.g. `"biome"`, `"ecology"`, `"population"`, `"faction"`,
`"region"`) and returns the list of registered IDs from the in-memory index.
The full mapping covers 34 catalog types.

**No new method on `CatalogRepository` is required.** The implementation calls
`load_all()` then iterates `get_all_ids_by_type()` for the catalog-relevant types.

### Types to expose in `make catalog-list`

From D16 Task 1 and the catalog reference fields table in `docs/content/authoring_guide.md`
Section 3, the types module authors actually need to look up are:

| Key | Repository attribute |
|---|---|
| `biome` | `repo.biomes` |
| `ecology` | `repo.ecologies` |
| `population` | `repo.populations` |
| `faction` | `repo.factions` |
| `region` | `repo.regions` |

Additional informational types (terrain, buildings, resources) can be included as
a bonus but are not in scope per ticket.

### `load_all()` is safe to call outside a kernel tick

`CatalogRepository.load_all()` raises `ContentHotPathViolation` only when called
while `_tick_context_active` is set. A standalone CLI script has no kernel context,
so `load_all()` is safe to call unconditionally.

### `CANONICAL_FAMILIES` lists all registered paths

`src/content/repository.py` lines 91–140. Biomes: `world/biomes.yaml`,
ecologies: `world/ecologies.yaml`, populations: `entities/populations.yaml`,
factions: `social/factions.yaml`, regions: `world/runtime_regions.yaml`.
All are marked `required=True`.

---

## 2. Scenario Templates

### 10 templates confirmed in `src/scenarios/templates.py`

| Template ID | Required World Features | Perspective Types |
|---|---|---|
| `territorial_pressure` | faction_territory, ecology_module | territorial |
| `raider_conflict` | faction_territory, combat_module | militant, defensive |
| `trade_route_risk` | trade_route, faction_territory | merchant, defensive |
| `resource_recovery` | resource_node, ecology_module | resource_seeker, territorial |
| `settlement_defense` | settlement, faction_territory, combat_module | defensive, militant |
| `cult_ritual_pressure` | ruins_ecology, cult_faction | investigative, defensive |
| `undead_containment` | undead_ecology, battlefield_terrain | defensive, militant |
| `wildlife_intrusion` | wildlife_ecology, ecology_module | territorial, defensive |
| `caravan_escort` | trade_route, faction_territory | merchant, defensive, militant |
| `mine_reopening` | resource_node, faction_territory | resource_seeker, defensive |

### `docs/content/authoring_guide.md` already exists — append there

The file (P2-L work) is complete at 362 lines. Section 8 (FAQ) already references
this ticket explicitly:

> "A catalog browser tool is planned (TCK-20260627-P3D-CATALOG-BROWSER)."

The template documentation and catalog browser note will both be added to this file.
No new doc file is needed, so `docs/REGISTRY.yaml` does not require an update.

---

## 3. Makefile Patterns

All existing targets use `python3 -m ...` for module invocations or
`python3 tools/<script>.py` for standalone scripts. The `make catalog-list`
target will follow the script pattern:

```makefile
catalog-list: ## List catalog IDs by type (biomes, ecologies, populations, factions, regions)
	python3 tools/catalog_list.py
```

Script at `tools/catalog_list.py` — reads the catalog via `CatalogRepository.load_all()`
and prints IDs grouped by type. Clean stdout output suitable for piping/grepping.

---

## 4. No Conflicts

- No existing `catalog-list` or `content-browse` target in Makefile.
- No parity ledger entry affected (tooling addition only).
- No engine behavior changes; DoD does not require parity update.
- `docs/REGISTRY.yaml` update not required (appending to existing doc).
