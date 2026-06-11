---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-MIGRATION-MAP-YAML
artifact_type: plan
tags: [migration, map, yaml]
---


# Plan

## New files
- `data/content/compatibility/migration_map.yaml` — 29 entries across 8 families
- `tests/unit/content/test_migration_map_schema.py` — 10 schema validation tests

## Schema
schema_version: migration_map.v1
Required per entry: legacy_id, legacy_family, catalog_family, catalog_id, adapter, status, fallback_allowed
Statuses: catalog_authoritative, compat_projected, fallback_only, deprecated, removed
