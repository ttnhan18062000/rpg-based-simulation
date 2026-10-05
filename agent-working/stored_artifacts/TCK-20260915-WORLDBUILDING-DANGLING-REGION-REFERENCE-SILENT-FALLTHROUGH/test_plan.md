---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH
phase: done
date: 2026-10-05
tags: [world]
---

# test_plan — TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH

| Case | Test |
|---|---|
| dangling `spawn_region` / resource `region` / building `region` raises, message names the offender and defined regions | `test_compiler_rejects_dangling_region_reference` (3 params) |
| several dangling references all reported | `test_compiler_reports_every_dangling_region_reference_at_once` |
| resolving world compiles unchanged | `test_compiler_accepts_world_whose_region_references_all_resolve` |
| regression: existing compile behavior | `tests/unit/worldbuilding`, `tests/unit/worldassembly`, `tests/certification/test_world_compile_determinism.py`, plus every other test file referencing `WorldCompiler` with `-m "not slow"` |

Negative control: with the guard call disabled, the 4 new tests fail; restored, they pass.
Known red on main, independent of this change: the `test_corpus_diversity.py` stability-anchor tests (reproduced on
clean `origin/main`).

## Proof Plan
- level: unit (WorldSpec through `WorldCompiler.compile`), plus a corpus-wide referential audit of the 24 resolved worlds
- proof kind: rejecting cases per reference kind, an accepting control, and a negative control (guard disabled makes the rejecting tests fail)
- oracle source: the `WorldSpec` region ids themselves; Mechanics Bible 06 (populations depend on their target regions as referential edges)
- expected effect: an undefined region id aborts compilation naming each offender and the defined regions; a world whose references all resolve compiles exactly as before
- selected commands: `pytest tests/unit/worldbuilding tests/unit/worldassembly tests/certification/test_world_compile_determinism.py`; the other test files referencing `WorldCompiler` with `-m "not slow"`
