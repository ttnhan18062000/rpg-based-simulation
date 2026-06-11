---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-MIGRATION-MAP-YAML
artifact_type: test_plan
tags: [migration, map, yaml]
---


# Test Plan

10 unit tests in tests/unit/content/test_migration_map_schema.py, all pass.

| # | Test | Validates |
|---|------|-----------|
| 1 | file_exists | YAML file created |
| 2 | has_schema_version | migration_map.v1 header |
| 3 | has_entries | non-empty entries list |
| 4 | all_entries_have_required_fields | no missing fields |
| 5 | all_status_values_are_valid | enum guard |
| 6 | all_legacy_families_are_known | family guard |
| 7 | fallback_allowed_is_boolean | type safety |
| 8 | legacy_ids_are_unique | no duplicate (id, family) pairs |
| 9 | all_required_legacy_families_are_represented | coverage gate |
| 10 | deprecated_entries_have_notes | explanation requirement |
