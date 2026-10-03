---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260604-PHASE23-REFERENCE-GRAPH
artifact_type: investigation
tags: [phase23, reference, graph]
---

# Investigation: Global Content Reference Graph and Dead Data Validation

## 1. Content Reference Graph Design

We need to build a directed graph containing all loaded content records as nodes, and dependencies between them as edges.

### Node Format
`family_short_name:record_id` (e.g. `race:human`, `trait:valiant`, `archetype:village_guard`)

### Edge Format
`source -> target` (e.g. `archetype:village_guard -> race:human`, meaning archetype references/depends on race)

### Bidirectional Mapping
To dynamically build the graph from Pydantic model fields without hardcoding every single relation, we can analyze the fields on each `CatalogBaseDefinition` subclass. Pydantic models contain field names and type annotations. We can define a lookup mapping based on:
1. Exact field name (e.g. `race` always points to `race:`)
2. Collection fields containing lists or dicts of IDs (e.g. `traits: List[str]` points to `trait:`, `ingredients: Dict[str, int]` keys point to `item:`)
3. A static mapping rule set for attribute names.

### Family to Short Name Mapping
```python
FAMILY_TO_SHORT = {
    "foundation.materials": "material",
    "foundation.traits": "trait",
    "foundation.themes": "theme",
    "foundation.relationship_axes": "relationship_axis",
    "foundation.attributes": "attribute",
    "foundation.elements": "element",
    "living.races": "race",
    "living.need_profiles": "need_profile",
    "living.sense_profiles": "sense_profile",
    "living.body_models": "body_model",
    "living.drive_profiles": "drive_profile",
    "living.cognition_profiles": "cognition_profile",
    "social.roles": "role",
    "social.factions": "faction",
    "social.perspectives": "perspective",
    "social.faction_relationships": "faction_relationship",
    "entities.stat_profiles": "stat_profile",
    "entities.combat_profiles": "combat_profile",
    "entities.inventory_profiles": "inventory_profile",
    "entities.skill_profiles": "skill_profile",
    "entities.populations": "population",
    "entities.entity_archetypes": "archetype",
    "world.buildings": "building",
    "world.terrain": "terrain",
    "world.services": "service",
    "world.regions": "region",
    "world.recipes": "recipe",
    "world.resources": "resource",
    "world.items": "item",
    "world.biomes": "biome",
    "world.ecologies": "ecology",
    "defaults": "defaults",
    "spawn_tables": "spawn_table",
    "compatibility.legacy_enemy_projection": "projection",
    "world_modules": "module",
    "world_compositions": "composition",
}
```

### Reference Attributes Extraction Mapping
We can define a mapping rule from field names to target short names:
- `"race"` -> `"race"`
- `"body_model"` -> `"body_model"`
- `"need_profile"` -> `"need_profile"`
- `"sense_profile"` -> `"sense_profile"`
- `"cognition_profile"` -> `"cognition_profile"`
- `"drive_profile"` -> `"drive_profile"`
- `"stat_profile"`, `"default_stats_profile"` -> `"stat_profile"`
- `"combat_profile"` -> `"combat_profile"`
- `"inventory_profile"`, `"default_inventory_profile"` -> `"inventory_profile"`
- `"skill_profile"` -> `"skill_profile"`
- `"role"`, `"compatible_roles"` -> `"role"`
- `"faction"`, `"chosen_faction"`, `"source_faction"`, `"target_faction"`, `"controlling_faction"` -> `"faction"`
- `"traits"`, `"natural_traits"`, `"compatible_traits"` -> `"trait"`
- `"themes"` -> `"theme"`
- `"biomes"` -> `"biome"`
- `"dominant_factions"`, `"default_factions"` -> `"faction"`
- `"populations"` -> `"population"`
- `"resources"` -> `"resource"`
- `"services"`, `"required_service"`, `"service_profile_id"` -> `"service"`
- `"materials"`, `"common_materials"`, `"material"` -> `"material"`
- `"allowed_enemy_ids"` -> `"projection"`
- `"provided_items"`, `"ingredients"`, `"outputs"` -> `"item"`
- `"provided_recipes"` -> `"recipe"`
- `"archetype_id"`, `"members"` -> `"archetype"`
- `"spawn_regions"` -> `"region"`
- `"axes"` -> `"relationship_axis"`
- `"terrain_mix"` -> `"terrain"`
- `"biome"` -> `"biome"`

This mapping covers all relationships checked in the `CAT-REL-*` rules.

---

## 2. "No Dead Active Data" Rule

We must ensure that all active data records (records with maturity class `EXISTING-LOGIC`, `LEGACY-EXPORT`, or `REDESIGNED-CORE`) have at least one downstream usage path unless explicitly exempted.

### Maturity Identification
Each record in the catalog yaml files has a corresponding maturity in the `CONTENT_USAGE_MATRIX` based on its family path.
Wait, can we load the maturity state directly from `src/content/matrix.py`?
Yes, `src/content/matrix.py` defines the content usage matrix mapping family names to entries containing `content_maturity` and `implementation_state`.
Maturity states requiring usage:
- `EXISTING-LOGIC`
- `LEGACY-EXPORT`
- `REDESIGNED-CORE`

We should exempt records if they belong to:
- `ADDITIONAL`
- `FUTURE-EXTENSION`
- `DESIGN_ONLY`

Wait, how do we find out what uses a node?
A node `X` has downstream usage if there is at least one directed path from some node `Y` to `X` (meaning `Y` references `X`, so `Y` consumes `X`).
Wait, is it just direct references (parents in the reference graph, i.e., nodes pointing to `X`), or transitive references?
Let's see: if `Y` references `X`, then `X` is used.
What if `Y` itself is dead/unused? That is also a concern, but the rule states: "Detect active data that is loaded and valid but never consumed by any higher component. These must have at least one downstream usage path unless explicitly exempted."
Wait, "at least one downstream usage path" means there is some incoming edge (or path) to it from another active/consumed node, or simply that it has at least one incoming edge from any record.
Wait, let's look at the specific test cases required:
- `active archetype with no population/projection → warning or error`
- `active material with no resource/item/recipe usage → warning or error`
- `active module with no composition → warning`
- `future-extension record unused → allowed`

Let's look at this carefully:
- An archetype is used if it's referenced by a population recipe (`entities.populations` / `PopulationRecipeDefinition`) or a legacy enemy projection (`compatibility.legacy_enemy_projection`).
- A material is used if it's referenced by a resource node (`world.resources`), an item (`world.items`), or a recipe (`world.recipes`).
- A module is used if it's referenced by a composition (`world_compositions`).
So, yes! If there are incoming edges (direct references) from these consuming records to the target records, they are considered used.
Let's write a generic validation check:
For each record node `X` in the graph:
1. Look up its family key's entry in `CONTENT_USAGE_MATRIX`.
2. Check if the matrix entry's `content_maturity` or `implementation_state` is one of `EXISTING-LOGIC`, `LEGACY-EXPORT`, or `REDESIGNED-CORE`.
3. If yes, check if the node has at least one incoming edge (`target = X`).
4. If it has no incoming edges, flag it as a Warning or Error.
Wait! Let's check: are there certain nodes that are "roots" or "entry points" that do not need incoming edges?
For example:
- `world_compositions` / `composition` (no one references a composition; it is the top-level assembly target)
- `defaults` (global compile profiles)
- `spawn_tables` (root spawn weights)
- `scenario` (simulation scenarios)
These are top-level / entry points, so they will naturally have 0 incoming edges and should be exempted.
Also, any record belonging to a family whose matrix entry is in `ADDITIONAL`, `FUTURE-EXTENSION`, or `DESIGN_ONLY` implementation state / content maturity is exempt.
Let's define a clean set of root families or rules to exempt them from having incoming edges.
For example, families that are entry points:
- `defaults`
- `spawn_tables`
- `world_modules`
- `world_compositions`
- `simulation_scenarios`
Wait, does `world_modules` require incoming edges? Yes, "active module with no composition -> warning". So a module must be referenced by at least one composition.

Let's double-check this logic. It is extremely clean and fully generic!
