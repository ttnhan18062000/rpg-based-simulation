# Plan — TCK-20260610-SWAMP-BORDER-PACK

Pack follows `data/content/packs/` single-file manifest pattern (matching frontier_extended_pack).
Content files go in existing catalog directories (not a separate content_packs/ subdirectory).

New files: manifest, world module, world composition.
Modified files: entity_archetypes, populations, frontier_scenarios, perspectives.

Key constraint: all traits and roles must exist in the base catalog (CAT-REL-011 validator).
