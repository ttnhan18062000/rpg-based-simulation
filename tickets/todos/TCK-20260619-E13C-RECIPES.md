---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E13C-RECIPES
phase: open
date: 2026-06-20
tags: [content, crafting-recipes, economy, phase-1]
---

# TCK-20260619-E13C-RECIPES

## Title
Epic 1.3C · Crafting Recipe Expansion

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
D07 F3: 8 crafting recipes for 34 items (Gap Risk 10/15). Most items have no production path. No gather→craft→upgrade chain exists. This ticket expands recipes from 8 to 25+ and authors the first complete gather→craft→upgrade chain.

## Scope

Expand `data/content/world/recipes.yaml` from 8 to 25+ entries.

### Required: Complete gather→craft chain (E13 acceptance criterion)

Chain 1 — Metal progression:
```
iron_ore (gather) → [refine] steel (craft: smelt_iron_to_steel, blacksmith, cost 20)
steel + wood → ember_axe (craft: craft_ember_axe, blacksmith, cost 55)
ember_axe + ember_core → enhanced_ember_axe? (upgrade — or use existing item)
```
Note: `steel` is already a catalog item. Confirm with `data/content/world/items.yaml`.

Chain 2 — Alchemy progression:
```
herb + healing_flower (gather) → small_potion (craft: already exists — verify)
herb + crystal_shard → travel_ration (craft: craft_travel_ration, healer, cost 15)
```

### Recipe coverage targets (fill uncovered item categories)

**Weapons (currently missing recipes):**
- `craft_wooden_staff`: wood×2 → wooden_staff (blacksmith, cost 15)
- `craft_basic_bow`: wood×2 + beast_fang → basic_bow (blacksmith, cost 20)
- `craft_apprentice_staff`: wood + crystal_shard → apprentice_staff (arcane, cost 35)
- `craft_frost_focus`: frost_shard×2 + crystal_shard → frost_focus (arcane, cost 65)
- `craft_ember_axe`: steel + ember_core → ember_axe (blacksmith, cost 55)

**Armor/protection (currently missing):**
- `craft_leather_armor`: wolf_pelt×2 + wood → leather_armor (blacksmith, cost 30)
- `craft_repair_kit`: iron_ore + wood → repair_kit (blacksmith, cost 25)

**Consumables:**
- `craft_travel_ration`: herb + healing_flower → travel_ration (healer, cost 15)
- `craft_large_potion`: healing_flower×2 + crystal_shard → large_potion? (check item catalog — if not exists use small_potion×2 output or skip)

**Materials/refined:**
- `smelt_iron_to_steel`: iron_ore×3 → steel (blacksmith, cost 20) — key chain step
- `render_wolf_pelt`: wolf_pelt (raw drop) is already an item; if a refined version is needed, add `tanned_hide` or skip

**Faction drops → useful items:**
- `craft_from_goblin_tokens`: goblin_token×3 → small_potion (merchant_service, cost 5) — loot conversion
- `process_shadow_ichor`: shadow_ichor + herb → warding_charm upgrade? — check if warding_charm already has recipe

The goal is ≥25 total unique recipes covering every service type (blacksmith, healer, arcane, merchant).

### Recipe YAML schema
```yaml
# STATE: ADDITIONAL
- id: "<recipe_id>"
  outputs: {<item_id>: <count>}
  ingredients: {<item_id>: <count>, ...}
  required_service: "<service_type>"
  gold_cost: <int>
```

## Out of Scope
- New item definitions (use existing 34 items only — do not add items)
- Dynamic recipe discovery
- Recipe failure/success rates

## Acceptance Criteria
- `data/content/world/recipes.yaml` has ≥ 25 entries
- At least one complete gather→craft chain: raw material (iron_ore) → intermediate (steel) → final item (ember_axe)
- `python3 -c "from src.content.repository import CatalogRepository; r = CatalogRepository('data/content'); r.load_all(); print('OK')"` passes
- `tests/integration/scenarios/test_content_foundation.py::test_crafting_chain_completes` passes (if runnable)

## Related Tickets
- TCK-20260619-E13-CONTENT-FOUNDATION (parent epic)
- TCK-20260619-E13B-MODULE-TYPES (settled_quarter module adds blacksmith_service — enabling recipes)

## Related Docs
- `docs/mechanics/03_economic_laws.md` (crafting laws reference)
- `docs/parity_ledger/town_resource.yaml` (update crafting entries on completion)
- `docs/audits/D07_content_depth.md` (update F3 count on completion)

## Related Code Areas
- `data/content/world/recipes.yaml` (expand)
- `data/content/world/items.yaml` (reference — do not modify)
- `src/content/repository.py` (`CatalogRepository.load_all()`)

## Assumptions / Open Questions
- Does `large_potion` exist as an item? Check `data/content/world/items.yaml` before adding recipe for it.
- Is `tanned_hide` a catalog item? If not, skip the wolf_pelt refinement chain — don't add new item IDs in this ticket.
- Does the recipe engine support multi-step chains natively, or does each recipe map independently? Check `src/domains/economy/` or `src/systems/world_systems/economy.py`.

## Implementation Notes
- Each recipe must reference only existing item IDs from `data/content/world/items.yaml`.
- `required_service` must match a building `kind` in `data/content/world/buildings.yaml` or service IDs in `data/content/world/services.yaml`.
- The gather→craft chain: `smelt_iron_to_steel` is the critical new recipe — it provides `steel` from `iron_ore` which then feeds `craft_ember_axe`.
- Mark all new entries with `# STATE: ADDITIONAL`.
- Run `make knowledge-index-update` after docs changes.

## Test Summary
```bash
# Catalog loads
python3 -c "from src.content.repository import CatalogRepository; r = CatalogRepository('data/content'); r.load_all(); print('OK')"
# Count
grep "^- id:" data/content/world/recipes.yaml | wc -l  # should be ≥ 25
```
Integration test `test_crafting_chain_completes` (written in E13D's test file).

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
