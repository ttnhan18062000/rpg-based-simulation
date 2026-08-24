---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-VARIANTS-METRIC
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, determinism, world]
---

# TCK-20260821-VISUAL-VARIANTS-METRIC

## Title
Variants validation metric: trail-activity liveliness and cross-spec TVD diversity

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promote the Variants metric — trail-activity liveliness plus cross-spec diversity via total-variation-distance (TVD) — into real production code.

## Scope
- Implement trail-activity = unique-tiles-visited / ticks-sampled, deciding a real entity-selection strategy to replace render_trail.py's current hardcoded "first entity in dict" choice
- Implement total_variation_distance(h1, h2) over terrain histograms, written fresh from PROPOSAL.md §5c (never saved to a file previously)
- Implement Variants as cross-*spec* comparison ONLY — no code path treats same-spec/different-seed as a diversity signal
- Both metrics computed as Tier-0, zero-image computations, reusing AuthoritativeState/DirtySet with no parallel tracking

## Out of Scope
- Multi-seed averaging / grade-band wiring (TCK-20260821-VISUAL-GRADE-SCORER's scope)
- Making the terrain-diversity half of multi-seed averaging meaningful — it stays a no-op until world-gen becomes seed-varied, which is unfiled/undecided (not this ticket)
- Threshold calibration (TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope)

## Acceptance Criteria
- [x] Trail-activity is near-zero (~2-3 tiles/100+ ticks) for the confirmed-stuck entity pattern, and materially higher for a moving entity
- [x] total_variation_distance(h1, h2) returns ~0.2315 for TVD(sandbox_world, dungeon_crawl) as a regression anchor
- [x] total_variation_distance returns exactly 0.0 for same-spec-different-seed terrain histograms, matching the confirmed seed-invariant-terrain finding
- [x] No code path in this module treats same-spec/different-seed as a diversity signal — only cross-spec comparisons are scored
- [x] Both metrics run as Tier-0 zero-image computations with no image/render dependency

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/spatial_rendering/prototype/render_trail.py
- experiments/spatial_rendering/prototype/render_world.py
- experiments/spatial_rendering/PROPOSAL.md

## Assumptions / Open Questions
- render_trail.py's entity-selection strategy needs a real decision in this ticket (replacing the "first entity in dict" hardcode)
- Multi-seed averaging will be a no-op for the terrain-diversity half of this metric until world-gen becomes seed-varied — flagged separately, not decided in this batch
- simulation-quality tag: this metric is an architecturally-independent SimQ-sibling (not a PillarScorer/pillar), tagged for topical adjacency since it reuses SimQ's grade vocabulary rather than being part of the SimQ subsystem itself

## Implementation Notes
Implemented plan.md's 6 steps exactly, in order:

1. Created `src/rendering/variants.py` with `normalize_histogram()` and
   `total_variation_distance()`, code taken verbatim from plan.md Step 1, plus a
   provenance docstring mirroring `density.py`/`shape.py`'s convention.
2. Added `compute_trail_activity()` verbatim from plan.md Step 2.
3. Added `select_trail_entity()` verbatim from plan.md Step 3 — sha256-hash-derived
   index into a sorted active-entity-ID list, no `DeterministicRNG`/`Domain` reuse.
4. Verified the module's import/class checklist per Step 4: only
   `from __future__ import annotations`, `hashlib`, and
   `from src.rendering.density import compute_terrain_histogram` are imported; zero
   classes defined; `total_variation_distance`'s parameters are exactly `h1`, `h2`.
5. Created `tests/unit/rendering/test_variants.py` implementing Tests 1-10, 12-14 from
   test_plan.md (Test 11 excluded per Decision 5), mirroring `test_density.py`'s and
   `test_shape.py`'s structure/imports/fixture style.
6. Re-ran `grep -n "^- id: INFRA-37" docs/parity_ledger/infrastructure.yaml` before
   appending — confirmed `INFRA-372` was still the max ID (file still 10876 lines), so
   `INFRA-373` was free and used as planned. Appended the entry verbatim from plan.md
   Step 6.

Independently reproduced the anchor values before writing tests (not just trusted the
plan's cited numbers): `TVD(sandbox_world, dungeon_crawl)` at seed 42 =
`0.23161981243456373` (rounds to `0.2316`), and `dungeon_crawl` seed 42 vs seed 137
terrain dicts are byte-identical, giving `TVD == 0.0` exactly. Both match plan.md.

**Deviations from plan.md (both noted in staging_artifacts' plan.md "Deviations"
section too):**
- `test_total_variation_distance_formula_on_synthetic_histograms`'s partial-overlap case
  (`h1={"A":0.6,"B":0.4}`, `h2={"A":0.4,"B":0.6}`) hits float representation error
  (`0.19999999999999996 != 0.2` under exact `==`); changed that one assertion to
  `round(total_variation_distance(h1, h2), 9) == 0.2`. No production code changed.
- The `INFRA-373` parity-ledger text block, copied verbatim from plan.md Step 6,
  contains `"...same-spec-seed-invariance anchor: its current seed-invariance..."` — a
  colon followed by a space inside a plain (unquoted) YAML scalar, which is invalid
  YAML syntax (`yaml.safe_load` raised `ScannerError: mapping values are not allowed
  here`). Changed that one colon to `--` (the doc's own existing em-dash-style
  convention, already used twice elsewhere in the same text block) to make the file
  parse as valid YAML. Content/meaning is unchanged. Confirmed the full file parses
  cleanly and the new entry matches the sibling entries' 8-field shape afterward.

## Test Summary
`PYTHONPATH=. .venv/bin/python3 -m pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v -m "not slow"`
→ 52 passed, 0 failed (13 new tests in `test_variants.py`, 39 pre-existing regression
tests in the same rendering domain, all unmodified and green).

Also ran the test_plan.md regression-surface confirmation command (noise-fill
mechanism this ticket's investigation depended on):
`pytest tests/integration/worldassembly/test_real_content_world_modules.py tests/integration/worldassembly/test_wolf_den_noise_migration.py tests/unit/worldbuilding/test_world_compiler.py tests/certification/test_world_compile_determinism.py -v -m "not slow"`
→ 56 passed, 0 failed.

## Files Changed
- `src/rendering/variants.py` (new) — `normalize_histogram()`, `total_variation_distance()`, `compute_trail_activity()`, `select_trail_entity()`
- `tests/unit/rendering/test_variants.py` (new) — 13 tests (Tests 1-10, 12-14 from test_plan.md; Test 11 excluded)
- `docs/parity_ledger/infrastructure.yaml` (modified) — appended `INFRA-373` entry
- `staging_artifacts/TCK-20260821-VISUAL-VARIANTS-METRIC/investigation.md`, `plan.md`, `test_plan.md` — pre-existing from this ticket's earlier Investigate/Plan phases (not created or rewritten in this Implement run); `plan.md` had a "Deviations" note appended this run (see below)
- `tickets/inprogress/TCK-20260821-VISUAL-VARIANTS-METRIC.md` (this file)

## Completion Summary
Implemented `src/rendering/variants.py` — a new stdlib-only, zero-class sibling to
`density.py`/`shape.py`/`connectivity.py` providing `total_variation_distance()` (cross-
spec terrain-diversity metric) and `compute_trail_activity()`/`select_trail_entity()`
(trail-liveliness metric with deterministic, insertion-order-independent entity
selection). Both metrics are pure functions over raw dicts/primitives, reusing
`density.py`'s `compute_terrain_histogram` rather than reimplementing it, and never
mixing same-spec/different-seed comparisons into the diversity signal. Added 13 new
tests in `tests/unit/rendering/test_variants.py` (Test 11 deliberately excluded per
plan.md Decision 5) and one new P2 parity-ledger entry (`INFRA-373`). Full rendering
suite plus the architecture zero-dependency guard (52 tests) and the noise-fill
regression surface (56 tests) all pass.

Verify's first pass returned BLOCKED on the `docs_to_update_coverage` static check:
`investigation.md`'s "Docs Requiring Update" section listed the two explicitly-excluded
docs (`quality_scoring_contract.md`, `idea_world_render_validation.md`) as leading
`` - `docs/...` `` bullets, which the check's parser (by its own documented contract —
it only reads the leading backtick path, not the reasoning that follows) cannot
distinguish from a genuinely-required path. This was a real formatting defect in
`investigation.md`'s own prose, not a missed doc update — the doc-updater phase had
already independently confirmed neither doc needed a change. Fixed by rewriting that
section to prose for the two excluded docs (dropping the bullet-leading backtick-path
format for them only, substance unchanged) so only the one genuinely-required path
(`docs/parity_ledger/infrastructure.yaml`) is parsed. Re-ran the static pre-check
directly afterward and confirmed `docs_to_update_coverage` now PASSes along with all
6 other conditions.
