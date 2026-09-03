---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
artifact_type: investigation
tags: [content, determinism]
---

# Investigation — TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT

Three real findings during implementation:

1. `unit_information_source` has no standalone content — confirmed directly it's a
   `worldcomposition.v1` world composing `frontier_village_core` + `hero_adventurers`, and that all 21
   worlds in the real corpus use the shared-module Composition path (`grep -L "worldcomposition"
   data/worlds/*/world.yaml` returned nothing). `WorldCompositionSpec` has no per-world region-override
   field. The plan doc's "isolated single-world pilot" framing assumed an architecture that doesn't
   exist; 17 of 21 worlds compose `frontier_village_core` (confirmed via `grep -rl frontier_village_core
   data/worlds/*/world.yaml`), so editing it cascades to all 17.
2. `world_compile_report.json`'s `state_hash` (`StateFingerprinter`, `src/replay/fingerprint.py`) has
   zero reference to `places` — confirmed by direct comparison: compiling with and without a real Place
   produces an identical `state_hash`. `CanonicalStateHasher` (the real, full-coverage hash) does detect
   it, confirmed via a direct before/after diff of the full canonical dict — only `regions`/`places`
   differ, nothing else.
3. All 21 committed `world_compile_report.json` baselines are stale, unrelated to idea 66 — confirmed via
   `git log`: every one was last committed in the same single commit (`29d78798`, 2026-08-14), 83 commits
   ago. Spot-checked 3 worlds unrelated to this ticket's changes (`dungeon_crawl`, `wilderness_survival`,
   `urban_political`); none reproduce their committed hash on a clean recompile. Root-caused: not a
   determinism bug (compiler is fully reproducible given identical input, verified directly) — a
   fixture-maintenance gap, currently unenforced by any test. Filed as
   `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`.
