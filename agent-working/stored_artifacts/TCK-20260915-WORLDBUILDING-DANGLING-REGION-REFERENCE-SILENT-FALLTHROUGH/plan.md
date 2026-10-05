---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH
phase: done
date: 2026-10-05
tags: [world]
---

# plan — TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH

1. Add `_assert_region_references_resolve(spec)` to `src/worldbuilding/compiler.py`; call it first in
   `WorldCompiler.compile`. It raises `InvalidWorldSpecError` naming every dangling population, resource node and
   building and the regions that are defined. Module-top import of `InvalidWorldSpecError` (ruff PLC0415).
2. Tests in `tests/unit/worldbuilding/test_world_compiler.py`: one per reference kind, all-at-once reporting, and a
   resolving world still compiles.
3. Update `docs/world/compiler_contract.md` (step 0 + "Region reference check").
4. No `trade_road` content change: it is a documented, working compat mapping.
Scope guards: no `src/core/state.py` edit; no new validator tool (the compile path is the guard, so no new CI job).
