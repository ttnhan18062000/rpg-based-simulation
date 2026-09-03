---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
artifact_type: test_plan
tags: [content, determinism]
---

# Test Plan — TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT

**Normal flow:** `unit_information_source` compiles to exactly 1 Region containing exactly 1
`Place(kind=CITY)`; `canonical_state_hash` differs between with/without-Place compiles, `state_hash`
does not (both confirmed, the second being the exact gap this ticket found and fixed).

**Edge cases:** the only canonical-dict diff between with/without-Place states is `regions`/`places` —
verified directly via a full key-by-key diff, not assumed from the hash alone.

**Failure modes:** a future field addition to `WorldCompiler.compile()`'s report dict that breaks an
exact-key-set assertion elsewhere (already hit and fixed once:
`tests/certification/test_world_compile_determinism.py::test_compile_report_contents`).

**Regression-prone paths:** full existing worldbuilding/worldassembly/core/engine/kernel/certification
suite, since this touches the compile report's public shape.

**Scope command (used):**
`pytest tests/unit/worldbuilding/test_world_compiler.py -v -m "not slow"` — 50 passed (2 new).
Full regression: `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/unit/worldmodules/ tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/ -m "not slow"`
— 895 passed, 2 skipped (pre-existing, unrelated), 0 failed.
