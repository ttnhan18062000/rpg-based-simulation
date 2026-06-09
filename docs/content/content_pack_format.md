# Content Pack Format

**Status:** Active  
**Schema version:** `content_pack.v1`  
**Last updated:** 2026-06-09

A content pack is a versioned, dependency-aware bundle of catalog records that proves
at least one world composition or scenario consumes its content. Packs with no consumers
are rejected at validation.

---

## YAML Format

```yaml
schema_version: "content_pack.v1"
pack_id: "my_pack"              # lowercase, underscores only, must start with letter
display_name: "My Content Pack"
version: "1.0.0"
enabled: true                   # set false to disable without deleting

dependencies:                   # list of pack_id values this pack requires
  - "base_pack"

included_families:              # catalog records added by this pack
  entity_archetypes:
    - "new_archetype_id"
  populations:
    - "new_population_id"

state_markers:                  # STATE annotations for each included record
  new_archetype_id: "EXISTING-LOGIC"
  new_population_id: "EXISTING-LOGIC"

strict_validation_result: "PASS"    # "PASS", "XFAIL:reason", or null

sample_compositions:            # compositions that consume this pack
  - "frontier_extended"

sample_scenarios:               # scenarios that consume this pack (alternative to compositions)
  - "hero_wilderness_start"
```

---

## Required Fields

| Field | Type | Description |
|---|---|---|
| `schema_version` | str | Must be `"content_pack.v1"` |
| `pack_id` | str | Unique identifier; lowercase letters/digits/underscores, starts with letter |
| `display_name` | str | Human-readable pack name |
| `version` | str | Pack version string |
| `sample_compositions` OR `sample_scenarios` | list | At least one of these must be non-empty |

---

## Optional Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | Disable without deleting to suppress pack content |
| `dependencies` | list[str] | `[]` | Other pack IDs this pack requires |
| `included_families` | dict | `{}` | Catalog records by family |
| `state_markers` | dict | `{}` | STATE annotations per record ID |
| `strict_validation_result` | str | `null` | Result of strict validation pass |

---

## Validation Rules

1. **Consumer required**: At least one `sample_compositions` or `sample_scenarios` entry.
   Packs with no consumers are rejected by `ContentPackManifest` schema.

2. **Dependency resolution**: All `dependencies` entries must be registered in the known
   pack registry. Checked by `ContentPackManifestValidator`.

3. **Pack ID format**: Must match `^[a-z][a-z0-9_]*$` — no uppercase, no hyphens,
   no leading digits.

4. **No executable fields**: Manifest files are purely declarative. No `exec`, `eval`,
   callable references, or runtime hooks.

---

## Python API

```python
from src.content.pack_manifest import (
    ContentPackManifest,
    ContentPackManifestValidator,
    ContentPackValidationError,
    MANIFEST_SCHEMA_VERSION,
)
import yaml

# Load and validate a pack manifest
with open("data/content/packs/my_pack.yaml") as f:
    data = yaml.safe_load(f)
manifest = ContentPackManifest(**data)  # schema validation happens here

# Validate dependencies against a known pack registry
validator = ContentPackManifestValidator()
validator.validate_or_raise(manifest, known_packs={"base_pack"})
```

---

## Adding a New Pack

1. Create `data/content/packs/{pack_id}.yaml` following the format above.
2. Add records to the appropriate catalog YAML files under `data/content/`.
3. Add a world composition or scenario that uses the pack's content.
4. Update `sample_compositions` or `sample_scenarios` in the manifest.
5. Run `make gate-expansion` — all 12 gate items must pass.
6. Run the expansion gate before committing: `pytest tests/integration/content/test_expansion_gate.py -v`.

---

## Enabling / Disabling Packs

Set `enabled: false` in the manifest to suppress pack content from the expansion gate
and composition assembly. The pack file is preserved for reference.

Disabled packs are NOT loaded by the registry adapter pipeline.

---

## Related

- `src/content/pack_manifest.py` — Python schema and validator
- `tests/unit/content/test_content_pack_manifest.py` — Schema tests
- `docs/testing/expansion_gate.md` — Gate that packs must pass
- `docs/mechanics/06_worldbuilding_foundation.md` — World topology rules
