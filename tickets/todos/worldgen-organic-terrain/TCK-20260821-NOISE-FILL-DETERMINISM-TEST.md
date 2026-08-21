---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-DETERMINISM-TEST
phase: open
date: 2026-08-21
tags: [world, determinism, testing]
---

# TCK-20260821-NOISE-FILL-DETERMINISM-TEST

## Title
Add golden-hash determinism regression test for noise-fill terrain generation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add a test proving that, with the noise-fill change in place, the same seed still produces bit-identical terrain. No existing test locks in flat-fill as a contract or asserts terrain-fill shape at all, so this is genuinely new coverage guarding the compiler's determinism guarantee for the new mechanism.

## Scope
- Add a new compiler-level test (tests/unit/worldbuilding/test_world_compiler.py and/or tests/certification/test_world_compile_determinism.py) asserting tile-for-tile equality of frozen RegionState.terrain across two same-seed compiles of a variant-declaring WorldSpec.
- Assert cross-seed variation within the variant region's bounds.
- Assert byte-identical flat-fill backward compatibility for a non-declaring region under the new compiler code path.
- May use a synthetic WorldSpec fixture (following create_certification_base_spec()/create_base_valid_spec()) — a real migrated module is not required for this ticket.

## Out of Scope
- Integrating with HeadlessRunner / TestStrategicRegression::test_headless_run_determinism — that is a separate, broader full-engine/replay-level determinism mechanism (Absolute Determinism / Bors Check) that this narrower compiler-level test does not need to touch.
- Requiring a real migrated module (TCK-20260821-WOLF-DEN-NOISE-MIGRATION) as a prerequisite — a synthetic WorldSpec fixture is sufficient per this concern's own findings; that ticket is soft/nice-to-have only, not a dependency.

## Acceptance Criteria
- [ ] Compiling the same WorldSpec (with a variant-declaring region) twice with an identical seed produces bit-identical per-tile terrain dicts (tile-for-tile equality on frozen RegionState.terrain), not just equal report["state_hash"].
- [ ] Compiling with two different seeds produces at least one differing tile within the variant region's bounds, proving the fill is actually seed-varied.
- [ ] A region that does NOT declare a variant still produces the exact pre-epic flat single-terrain fill under the new compiler code path (backward-compat regression guard).
- [ ] The new test reuses compile()'s existing report["state_hash"] equality assertion (mirroring test_compiler_seeding_determinism) as one signal, in addition to the new tile-level dict comparison.

## Related Tickets
- TCK-20260821-COMPILER-NOISE-FILL
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN
- TCK-20260812-COMMITTED-INTENTION-SEQUENCE

## Related Docs
- docs/engine/contracts/regression_and_verification.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/unit/worldbuilding/test_world_compiler.py
- tests/certification/test_world_compile_determinism.py
- src/worldbuilding/compiler.py
- src/core/state.py
- src/platform/rng.py

## Assumptions / Open Questions
- Confirmed this is a compiler-level test only and does not need to touch TestStrategicRegression::test_headless_run_determinism or HeadlessRunner.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
