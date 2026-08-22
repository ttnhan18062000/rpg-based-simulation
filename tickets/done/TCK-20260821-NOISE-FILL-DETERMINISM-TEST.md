---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-DETERMINISM-TEST
phase: done
date: 2026-08-21
tags: [world, determinism, testing]
---

# TCK-20260821-NOISE-FILL-DETERMINISM-TEST

## Title
Add golden-hash determinism regression test for noise-fill terrain generation

## Status
DONE

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
- [x] Compiling the same WorldSpec (with a variant-declaring region) twice with an identical seed produces bit-identical per-tile terrain dicts (tile-for-tile equality on `state.terrain` — the ticket's own text says "frozen RegionState.terrain", but the real field is `AuthoritativeState.terrain`, confirmed by investigation), not just equal report["state_hash"]. Already satisfied by pre-existing `test_compiler_terrain_variants_deterministic_same_seed` (added by `TCK-20260821-COMPILER-NOISE-FILL`); no new work needed for this half.
- [x] Compiling with two different seeds produces at least one differing tile within the variant region's bounds, proving the fill is actually seed-varied. Already satisfied by pre-existing `test_compiler_terrain_variants_different_seed_differs`.
- [x] A region that does NOT declare a variant still produces the exact pre-epic flat single-terrain fill under the new compiler code path (backward-compat regression guard). Already satisfied by pre-existing `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict`.
- [x] The new test reuses compile()'s existing report["state_hash"] equality assertion (mirroring test_compiler_seeding_determinism) as one signal, in addition to the new tile-level dict comparison. This was the only genuinely uncovered AC — closed by extending `test_compiler_terrain_variants_deterministic_same_seed` in place to also capture and assert `report1["state_hash"] == report2["state_hash"]`.

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
Investigation found this ticket's 4 Acceptance Criteria substantially overlap with the immediately
prior batch ticket (`TCK-20260821-COMPILER-NOISE-FILL`, closed): ACs 1-3 were already fully satisfied
by 3 tests that ticket added to `tests/unit/worldbuilding/test_world_compiler.py`. Only AC 4 (state_hash
equality as an additional signal alongside the tile-dict comparison) was genuinely uncovered — this
ticket does not re-implement ACs 1-3, only closes the real gap, per the Hard Rule against duplicate work.

Extended `test_compiler_terrain_variants_deterministic_same_seed` (`tests/unit/worldbuilding/test_world_compiler.py`)
in place: captured `report1`/`report2` (previously discarded as `_`) from both same-seed `compile()`
calls, added `assert report1["state_hash"] == report2["state_hash"]` before the existing tile-dict
comparison, mirroring `test_compiler_seeding_determinism`'s pattern. Updated docstring to name both
signals. No production code touched.

Also broadened `docs/parity_ledger/substrate.yaml`'s `SUB-385` entry `test_path` (via
`tools/parity_ledger_writer.write_entry()`, never raw Edit) from
`test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` to the now-extended
`test_compiler_terrain_variants_deterministic_same_seed` — the old citation only exercised the
non-declaring flat-fill path and never triggered `weighted_choice()`/`Domain.INIT`, while the new
citation exercises the real noise-fill mechanism the ledger entry's own text describes. All other
`SUB-385` fields (`status`, `priority`, `text`, `v2_evidence`) left byte-identical.

## Test Summary
`.venv/bin/python3 -m pytest tests/unit/worldbuilding/test_world_compiler.py tests/certification/test_world_compile_determinism.py -v`
— 44 passed, 0 failed, including the extended test and all pre-existing tests in both files.

## Files Changed
- `tests/unit/worldbuilding/test_world_compiler.py` — extended `test_compiler_terrain_variants_deterministic_same_seed` with a `report["state_hash"]` equality assertion.
- `docs/parity_ledger/substrate.yaml` — `SUB-385`'s `test_path` broadened to cite the extended test (written via `tools/parity_ledger_writer.write_entry()`).
- `tickets/inprogress/TCK-20260821-NOISE-FILL-DETERMINISM-TEST.md` — this file: Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary.

## Completion Summary
Closed the one genuinely uncovered Acceptance Criterion (state_hash equality as an additional
determinism signal) by extending an existing test in place, after investigation confirmed the other
3 ACs were already fully satisfied by tests the immediately prior batch ticket added — avoiding
duplicate test coverage per the repo's anti-drift discipline. Zero production code touched; one test
file extended, one parity ledger metadata field broadened to a more representative citation.
