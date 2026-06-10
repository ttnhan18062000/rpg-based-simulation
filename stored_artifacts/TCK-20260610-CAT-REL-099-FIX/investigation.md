# Investigation — TCK-20260610-CAT-REL-099-FIX

## Current Behavior

`CatalogValidator._validate_reference_graph()` fires rule CAT-REL-099 because:
- `moon_cult_ruins.yaml` declares `populations: ["apprentice_mage"]`
- `WorldModuleNormalizer` converts this to `population_refs=("apprentice_mage",)` (`src/worldmodules/normalizer.py:150`)
- `ContentReferenceGraph.add_module_edges()` adds edge `module:moon_cult_ruins → population:apprentice_mage` (`reference_graph.py:219-220`)
- `population:apprentice_mage` is NOT a node in the graph — `apprentice_mage` is only a **member key** inside `dragon_cult_elite_cell` (populations.yaml:69-70), not a top-level population group
- Validator generates ERROR, which blocks all world assembly via `CATALOG_STRICT` and `CATALOG_WITH_COMPATIBILITY` modes

The `CatalogValidator` sweeps the entire catalog's reference graph, so a single broken edge poisons assembly for all modules (not just moon_cult_ruins).

## Root Cause

`moon_cult_ruins.yaml` mistakenly references an archetype ID (`apprentice_mage`) where it should reference a population group ID. Population groups are top-level entries in `data/content/entities/populations.yaml` with an `id` field and a `members` dict.

## Mechanics/Engine Constraints

- World module `populations` field references population group IDs, not archetype IDs
- Population groups are the unit of world spawning; archetypes are the unit of entity definition
- `CATALOG_STRICT` mode must pass clean validation before any assembly proceeds

## Parity Ledger Overlap

- `substrate.yaml` — world module assembly; check for existing parity entry on population resolution
- No specific P0 parity entry found for population group references from modules

## Prior Work

- `TCK-20260609-STRICT-WORLD-MATRIX` — scaffolded the strict matrix but left full-assembly rows xfailed due to this exact defect
- `TCK-20260609-CONTENT-EXPANSION-GATE` — 11/12 pass; gate item 11 xfailed due to CAT-REL-099
- `TCK-20260609-ARCHETYPE-METADATA-EXPLICIT` — noted 9 pre-existing failures (CAT-REL-099 moon_cult_ruins)

## Fix Design

Two-part data fix (no source code changes required):

1. **Add population group** `moon_cult_apprentice_circle` to `populations.yaml`:
   - `apprentice_mage` archetype has `faction: "arcane_circle"`, `themes: ["arcane", "moon"]` — thematically correct for moon_cult_ruins
   - `preferred_regions: ["moon_cave"]` — matches the only region defined in moon_cult_ruins

2. **Update `moon_cult_ruins.yaml`** `populations` list: replace `"apprentice_mage"` with `"moon_cult_apprentice_circle"`

## Risks and Open Questions

- No source code changes; risk is minimal — data-only fix
- `dragon_cult_elite_cell` also contains `apprentice_mage:3` as a member; this is unrelated and stays unchanged
- After fix: `population:moon_cult_apprentice_circle` node exists → edge resolves → validation passes → assembly unblocked

## Anti-Drift Hazards

- Do not add `apprentice_mage` as a top-level population group named `apprentice_mage` — that would conflate archetype and population namespaces
- The new population group must be named differently from the archetype to avoid future confusion
