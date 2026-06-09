---
ticket: TCK-20260609-HARDCODED-GAMEPLAY-GUARD
phase: investigation
---

# Investigation

## Scan target

`src/core/registries.py` fallback block contains dict-literal style gameplay definitions:
- 20 ItemDef entries (equipment + materials)
- 5 ResourceDef entries (node_*)
- 7 EnemyDef entries
- 3 RecipeDef entries
- 5 ServiceDef entries (hometown services)
- 7 RegionDef entries

## Key distinction

Dict-literal pattern (fallback maps): `"id_string": XxxDef(` — scannable by regex
Direct-assignment pattern (adapters): `dict["id"] = XxxDef(` — excluded from scan

This naturally limits the scan to fallback map content vs adapter-generated content.

## Migration map coverage

migration_map.yaml covers: rusted_sword, wooden_staff, basic_bow, leather_armor, herb,
apprentice_staff (items), all 5 node_* resources, 6 enemies (not rat), small_potion (recipe).

Pre-existing IDs NOT in migration_map → added to KNOWN_HARDCODED_BASELINE (29 entries).
