---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED
artifact_type: test_plan
date: 2026-10-30
tags: [determinism]
---

# Test plan

Level: unit for the sort sites, subprocess-based for cross-process determinism, one paired measurement run (heavy slot, later). Oracle: the sorted order of ids, and equality of final canonical state hashes across two `PYTHONHASHSEED` values.

| AC | test | positive control |
|---|---|---|
| AC2 | per-site unit tests: merged identity/region lists sorted; `known_skill_ids` sorted and truncated after sorting; `active_modifiers` sorted | each fails on unfixed code for at least one seed in a subprocess sweep of seeds 0-3 |
| AC3 | tactical tie: entity with HEAVY_STRIKE and fireball ready picks the same skill at two seeds in subprocesses | unfixed `tactical.py` picks differently at some seed; if it never does, state the fixture and the seeds tried |
| AC4 | fixed short run (world, seed, ticks recorded), final canonical hash equal at two `PYTHONHASHSEED` values, `audit_mode` on (an earlier non-audit probe was non-deterministic on main, so a non-audit comparison is not a valid instrument) | the same comparison with the unfixed code, where the concerns path is exercised, differs; if it never does, record that the fixture does not reach the path |
| AC5 | paired run at seed 0 (heavy slot through rpg-planner-ubuntu): deaths per world must not drift; any drift is a STOP | n/a |

Not run in the audit phase: all of the above. No sim runs.
Scoped commands (when the OK comes): `tests/unit/engine`, `tests/unit/core`, `tests/unit/progression`, the combat_engagement tests, the new determinism tests, `tests/unit/observability` (sanity), `generate_registry --check`, the paths guard.
