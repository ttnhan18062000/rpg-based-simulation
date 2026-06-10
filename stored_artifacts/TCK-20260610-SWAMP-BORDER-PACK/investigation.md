# Investigation — TCK-20260610-SWAMP-BORDER-PACK

## Findings

- `swamp_tribe` faction, `lizardfolk` race, `sunken_swamp` biome, `swamp` terrain all present in base catalog
- Pack manifests are single YAML files in `data/content/packs/` (not content_packs/ subdirectory)
- `ContentPackManifest` schema: schema_version, pack_id, display_name, version, enabled, dependencies,
  included_families, state_markers, strict_validation_result, sample_compositions, sample_scenarios
- CAT-REL-011 validator blocks archetypes referencing non-existent traits/roles
- Valid traits include: amphibious, territorial, regenerating, leader, magic_sensitive, large_body
- Valid roles include: scout, shaman, brute (all needed roles exist)
- `WorldAssemblyResolver` (not WorldAssembler) is the assembly entry point in tests
