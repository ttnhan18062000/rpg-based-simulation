---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-WORLDSPEC-SCHEMA-INIT
artifact_type: test_plan
tags: [worldspec, schema, init]
---

# Test Plan - WorldSpec Schema Initialization

## Unit Tests
To be implemented in `tests/unit/worldbuilding/test_worldspec_schema.py`:

- **test_valid_minimal_world_spec_loads**: Loads a valid YAML minimal specification and asserts all fields map correctly.
- **test_missing_schema_version_rejected**: Rejects loading if `schema_version` is omitted.
- **test_missing_world_id_rejected**: Rejects loading if `world_id` is omitted.
- **test_invalid_topology_size_rejected**: Rejects if topology dimensions are negative, non-integer, or empty.
- **test_optional_sections_omitted**: Verifies that optional fields (like factions, entities, buildings) are loaded as empty collections or defaults.
- **test_schema_no_side_effects**: Verifies that parsing the YAML does not load or compile state into the active engine.
