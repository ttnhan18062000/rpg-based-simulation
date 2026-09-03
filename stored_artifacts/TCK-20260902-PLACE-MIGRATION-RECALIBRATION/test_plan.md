---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-RECALIBRATION
artifact_type: test_plan
tags: [content, determinism]
---

# Test Plan — TCK-20260902-PLACE-MIGRATION-RECALIBRATION

This ticket is a triage/investigation pass, not a code change — no new automated tests were added. The
`canonical_state_hash` mechanism it relies on was already covered by Stage A/B's own test suites
(`tests/unit/worldbuilding/test_world_compiler.py`, `tests/certification/test_world_compile_determinism.py`).

## Verification performed
1. Recompile all 21 worlds, diff `canonical_state_hash` against committed baseline — all 21 changed as
   expected (new Place data), matching the isolation already proven in Stage A/B.
2. Full 81-run_key sweep of `tests/simulation_quality/fixtures/grade_anchors.json` via
   `tools/calibrate_simq.py` — 18 matched, 61 drifted, 2 failed (unrelated tooling gap).
3. Causal isolation control: revert all 6 idea-66-touched content modules to pre-migration state, re-run
   `unit_information_source_seed123_200t` — drift persisted identically, proving non-causation.
4. Hand-verified control: `unit_information_source_seed42_200t` matched its anchor exactly across all 10
   pillars pre-sweep.

## Result
No regression tests needed — no regression found. Existing suites (`test_grade_regression.py`,
`test_world_compile_determinism.py`) remain the authoritative gates; this ticket's finding is recorded in
`TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS` for future fixture-refresh work, not as a new test.
