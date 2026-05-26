# Investigation - WorldSpec Schema Initialization

## Existing Setup
- `src/config/profiles.py` uses `pydantic` or `dataclasses`? Let's check how the config is structured.
- The project has Pytest suite running under Python 3.13.7.
- YAML parsing is available via `pyyaml`.

## Design Considerations
- Must keep YAML parsing separate from AuthoritativeState compilation.
- Validation should check:
  - Required fields (schema_version, world_id, topology).
  - Valid topology size.
  - Coordinate system matching supported types (grid).
  - Rejection of invalid schemas.
