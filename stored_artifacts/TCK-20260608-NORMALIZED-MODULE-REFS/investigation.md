# Investigation — TCK-20260608-NORMALIZED-MODULE-REFS

## Findings
- NormalizedWorldModule in normalizer.py had four fields: biomes, ecologies, populations, relationships
- resolver.py used normalized_module.biomes/ecologies/populations/relationships at lines 699, 705, 711, 727
- reference_graph.py used them at lines 215-221
- test_reference_graph.py used old names as kwargs in _make_normalized_module
- test_modules.py accessed .biomes/.ecologies/.populations/.relationships on result
- integration test_real_content_world_modules.py: two occurrences of normalized.populations (line 65, 91)
- WorldModuleSpec.biomes/ecologies/populations/relationships (raw schema) — kept unchanged (out of scope)
- CatalogRepository.biomes/ecologies/populations (different class) — kept unchanged
- Pre-existing world_compositions failures unrelated to this ticket
