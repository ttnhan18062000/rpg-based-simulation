---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK
artifact_type: investigation
date: 2026-10-19
tags: [testing]
---

# Investigation — TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK

## What is on main (94ff6b0bc)
- `src/core/spawn_source.py`: `SpawnSource` is well-formed by construction (`__post_init__` rejects a BIRTH without parents, parents on a non-BIRTH, an AUTHORED_ARRIVAL without rule_kind and rule_id). So ticket cases (b) and (c) cannot produce a malformed source at the ledger: the violation shape is "unsourced add", and (b)/(c) assert the construction refusal instead.
- `RunLedger._count_adds` counts `group|<SpawnKind>` or `group|unsourced`; `rpg_gate_metrics._check_unsourced_adds` counts only the `unsourced` keys. Silence (no live header or no tally) raises `GateDataMissingError`, which the harness records as no-data.
- `src/engine/apply.py::DuplicateEntityIdError(ValueError)` is raised by `_add_entities`, also for a repeated id inside one update.

## Untagged `generator.spawn_*` sites (AST, receiver named generator)
| site | gate | ruling |
|---|---|---|
| boss.py check_for_boss_spawn, check_for_lair_spawn | ENABLE_WORLD_BOSS_SPAWN | owner decision 14 |
| calamity.py _spawn_world_boss | ENABLE_WORLD_BOSS_SPAWN | owner decision 14 |
| calamity.py process_world_dynamics (magical/demonic) | ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH | DEV-002 |
| creature_territory.py process_territories | ENABLE_CREATURE_TERRITORY_LIFECYCLE (read in engine/world_dynamics.py) | D67/D70 stay OFF; DEV-002 |
| camp.py process_camps x2 | ENABLE_CAMP_NEST_SPREAD (L72), ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH (L98) | D70; DEV-002 (rpg-planner 2026-10-19) |

Tagged: `reproduction_humanoid.py process_reproduction` (BIRTH). Excluded: `src/certification/scenarios.py` (tick-0 scenario worlds, INITIAL, never an `entities_add`) and `generator.py` (the definitions).

## Findings to report
- The planner's note names `src/core/feature_flags.py`; the registry is `src/domains/optimization/feature_flags.py` (`FeatureFlagManager`). The guard reads that.
- `config.yaml` carries no flags. Gate worlds can only enable a flag through `config/simulation_quality/profiles/<world>.yaml`, the world files, or the harness `PIN_SETTINGS["flags"]` (audit_mode, no_frame_pacing only). The guard checks all three. Only `camp_maturity_calibration_pilot` (not a gate world) turns ENABLE_CAMP_NEST_SPREAD on.
- The guard does not follow a spawn result across functions: `_spawn_world_boss` returns its entity to a caller, so it is listed at the function that calls the generator.
