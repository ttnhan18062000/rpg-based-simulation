# Investigation - Phase 23 Reference Graph and active-data validation

## Current State Analysis

1. **Comment-State Assumptions**:
   - Python code currently does not parse comments like `# STATE:` directly.
   - However, dead active data validation checks `content_maturity` in `CONTENT_USAGE_MATRIX`. We need to ensure that it only does family-level checks and relies strictly on `implementation_state`.
   - Compatibility files (`compatibility/legacy_enemy_projection.yaml`) map clean archetypes to legacy tags. We need to make sure compatibility records point to clean source data (existing archetypes, etc.) and validate this referential integrity.

2. **Module and Composition Edges**:
   - `ContentReferenceGraph` currently uses a generic scan for module fields which misses or misinterprets the count maps like `resources: {wood_node: 2}` because dictionaries are parsed as lists of keys, yielding strings, which `find_references_recursive` skips.
   - We must explicitly scan biomes, ecologies, populations, factions, relationships, resources, buildings, services in the module, and add them as typed edges.
   - We need to introduce an `edge_metadata` dictionary in `ContentReferenceGraph` to store counts (e.g. `count = 2`).
