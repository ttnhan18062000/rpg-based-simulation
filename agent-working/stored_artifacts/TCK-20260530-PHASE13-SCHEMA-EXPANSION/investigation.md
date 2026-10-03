---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260530-PHASE13-SCHEMA-EXPANSION
artifact_type: investigation
tags: [phase13, schema, expansion]
---

# Investigation Notes - Phase 13 Schema Expansion

## Current Schema State
- Current catalog classes define Factions, Roles, Stats, Combat, Inventory, Cognition, Resources, Buildings, Services, Terrains, and Spawns.
- They lack definition models for Items, Enemies, Recipes, and Progression Regions.
- `CatalogValidator` exists and checks some basic bounds, but does not validate loot drop item_ids or region references.
