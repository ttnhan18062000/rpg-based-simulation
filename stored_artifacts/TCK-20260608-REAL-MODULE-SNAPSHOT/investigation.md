# Investigation — TCK-20260608-REAL-MODULE-SNAPSHOT

## Findings
- frontier_village_core.yaml exists in data/content/world_modules with biomes, ecologies, populations, buildings fields
- Has biomes: ["frontier_village"], ecologies: ["frontier_village_ecology"], populations: ["frontier_village_population"]
- Has buildings dict: {town_hall:1, shop:1, blacksmith:1, inn:1, healer_hut:1}
- No resources, services, or relationships keys (will normalize to empty dict/tuple)
- WorldModuleRepository.load_all() + get_module(module_id) is the correct retrieval path
- NormalizedWorldModule *_refs fields are tuples of strings after TCK-20260608-NORMALIZED-MODULE-REFS
- All existing integration tests use repos fixture but don't snapshot the full normalized shape per-field
