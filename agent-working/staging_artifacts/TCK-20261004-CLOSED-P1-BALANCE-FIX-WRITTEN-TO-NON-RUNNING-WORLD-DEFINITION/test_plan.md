---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION
phase: open
date: 2026-10-04
tags: [world, content, root-cause]
---

# Test Plan — TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION

## Test Cases
- Freshness: snapshot == fresh resolve (parametrized over every composition world); resolve determinism; compile-report counts == fresh compile (parametrized); dungeon_crawl remedy asserted at the loaded location (module list, `danger_scale`, no removed modules in the snapshot, non-empty then 12 entities).
- Blast radius: rendering evidence tests on the frozen fixture; census pin; corpus registry regenerated.

## Proof Plan
### AC1 / AC2 / AC3
- **level**: integration
- **proof kind**: regression (fails on the old files)
- **oracle source**: `docs/mechanics/06_worldbuilding_foundation.md`; `docs/architecture/world_repository_layout.md`; parity `SUB-394`
- **expected effect**: `world.yaml` has 2 modules and `danger_scale` 2; snapshot lacks the removed modules; `load_world` yields populations summing to 12
- **selected commands**: `pytest tests/integration/worldassembly/test_resolved_snapshot_freshness.py -q -k dungeon_crawl`
### AC4 / AC4a
- **level**: integration
- **proof kind**: differential (committed vs fresh) / architecture guard
- **oracle source**: Bible 06 invariant "the world the engine loads is the one its authored definition resolves to"; `SUB-394`
- **expected effect**: equality against a fresh resolve for every composition world; determinism asserted
- **selected commands**: `pytest tests/integration/worldassembly/test_resolved_snapshot_freshness.py -q`
### AC5 / AC6
- **level**: process
- **proof kind**: recorded sweep
- **oracle source**: ticket AC-5, AC-6
- **expected effect**: sweep results in investigation.md; P1I record annotated
- **selected commands**: `python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION`
### AC7
- **level**: docs + unit
- **proof kind**: parity record
- **oracle source**: `docs/guidelines/intentional_divergences.md`; parity `INFRA-373`
- **expected effect**: DEV-009 and SUB-394 recorded; INFRA-373 anchor still reproduces on the frozen fixture
- **selected commands**: `pytest tests/unit/rendering tests/unit/worldassembly/test_corpus_diversity.py tests/tools/test_corpus_registry.py -q -m "not slow"`
