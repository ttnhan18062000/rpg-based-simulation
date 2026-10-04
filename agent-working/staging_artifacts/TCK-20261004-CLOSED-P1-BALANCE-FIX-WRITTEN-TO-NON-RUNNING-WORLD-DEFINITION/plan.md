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

# Plan — TCK-20261004-CLOSED-P1-BALANCE-FIX-WRITTEN-TO-NON-RUNNING-WORLD-DEFINITION

## Approach
Apply the accepted `TCK-20260627-P1I-WORLD-BALANCE-FIX` remedy to the authoritative `world.yaml`, regenerate what production loads, and add guards so a stale artifact cannot hide again.

## Steps
1. AC-4a first: for every composition world, compare the committed `resolved/world.resolved.yaml` with a fresh resolve (and check resolve determinism). Record the result before changing anything.
2. AC-5 sweep: compare each catalog copy with its `world.yaml`.
3. Edit `data/worlds/dungeon_crawl/world.yaml` (2 modules, `danger_scale: 2`); regenerate `resolved/`, `world_compile_report.json`, corpus registry.
4. Guards in `tests/integration/worldassembly/test_resolved_snapshot_freshness.py`: snapshot == fresh resolve for every composition world; content-derived counts of every committed compile report == fresh compile; dungeon_crawl remedy pinned at the loaded location.
5. Shared renderer `render_resolved_world_yaml` in `src/worldbuilding/cli.py` so the guard cannot drift from `resolve`.
6. Blast radius: repoint six rendering-evidence tests to a frozen fixture (planner ruling); census pin 4 -> 2; docs DEV-009, SUB-394; note on `TCK-20260627-P1I-WORLD-BALANCE-FIX`.

## Scope guards
- Do not re-decide the balance target. Do not edit `src/rendering/` or `docs/visual_quality/` (assigned to neither lane).
- Do not fix other census entries or the broader compile-report hash staleness; they are filed separately.
