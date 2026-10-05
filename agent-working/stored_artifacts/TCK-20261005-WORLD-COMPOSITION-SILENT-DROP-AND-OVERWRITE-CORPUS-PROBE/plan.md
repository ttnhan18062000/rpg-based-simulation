---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE
phase: done
date: 2026-10-05
tags: [world]
---

# plan — TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE

1. Add `tools/world_composition_corpus_probe.py`: pure detectors (`duplicate_place_ids`, `dropped_placements`, `faction_merge`, `biome_provenance`, `validator_residue`) plus a runner that
   resolves each `data/worlds/*/world.yaml` through the real `WorldAssemblyResolver` (recording each module contribution by wrapping `resolve_module_contribution` on the instance) and compiles it.
   Read-only; writes `.jsonl` only.
2. Add `tests/tools/test_world_composition_corpus_probe.py`: a firing case and a quiet case per detector, end to end through the real resolver where the resolver allows it.
3. Run it over all 24 compositions; store the rows under this folder as `.jsonl`.
4. Correct the stale comment at `src/worldbuilding/compiler.py:433-439` (comment only).
Scope guards: no change to resolver or compiler behaviour; do not add `WorldValidator` to the three compile paths; do not touch `src/cli/` or `src/api/`.
