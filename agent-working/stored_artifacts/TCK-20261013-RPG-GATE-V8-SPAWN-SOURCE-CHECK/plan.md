---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK
artifact_type: plan
date: 2026-10-19
tags: [testing]
---

# Plan — TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK (AC4 + AC5 remainder)

AC1-AC3 landed earlier (#531). This pass closes AC4 and AC5 now that rpg's `SpawnSource`, `StateUpdate.entity_spawn_sources`, the `RunLedger` adds tally, V8's `compute()` and `DuplicateEntityIdError` are on main (#645).

## Steps
1. `tests/simulation_quality/rpg_gate/test_v8_fires.py`: cases (a)-(g), each driving the real `ApplyPath.apply_generation`, the real `RunLedger` and `StarvationRecorder`, and the real `rpg_gate_metrics.compute`. No hand-built tally, no skip, no xfail.
2. `tests/architecture/test_spawn_sites_declare_source.py`: AST scan of `generator.spawn_*` calls in `src/`; an untagged site must be in the `OFF_SITES` ratchet, each entry naming file:function:callee, call count, gating flag(s), ruling ref and state OFF.
3. Gate check: each flag is in the registry, defaults OFF, and no gate world (profile yaml, world files, harness `PIN_SETTINGS["flags"]`) enables it.
4. Regression cases for the guard itself: synthetic unsourced site, sourced site, stale entry, tagged-now entry, wrong count, flipped flag default, flag missing from registry, gate world enabling a flag.
5. Ticket: take the planner's UNBLOCKED note, fill Implementation/Test Summary, tick AC4-AC7.

## Scope guards
- No file under `src/`, `docs/mechanics/` or `config.yaml` changes. No oracle, k or floor changes (AC6).
- `camp.py` L72/L98 are allowlisted OFF per rpg-planner's 2026-10-19 ruling; they are not tagged.
