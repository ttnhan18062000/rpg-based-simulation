---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL
phase: done
date: 2026-10-20
tags: []
---

# Test plan: TCK-20261020-ENTITY-LIST-RETURNS-A-BOUNDED-SUMMARY-NOT-THE-FULL-DETAIL

## Proof Plan
- level: unit + API
- proof kind: byte ceilings on an aged-entity fixture; exact counts and exact paged history; cache separation
- oracle source: the platform SLO finding (#593 / #627): payload per entity independent of world age
- expected effect: list row <= 1 KB and detail <= 8 KB at 500 finished records of each kind; the paged history returns every quest exactly once
- selected commands: pytest tests/unit/api tests/api/test_entity_quest_history_route.py tests/api/test_live_map_terrain_codes_resolve_through_the_manifest.py tests/api/test_paged_logic.py tests/perf/test_api_projection_perf.py
