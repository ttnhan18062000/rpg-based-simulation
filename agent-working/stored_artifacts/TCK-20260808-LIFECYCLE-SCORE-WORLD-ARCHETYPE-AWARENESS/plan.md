---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [simulation-quality, world]
---

# Plan — TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS

## Fix

1. **`tools/generate_corpus_registry.py`**: add `compute_archetype(world_name) -> str`, reading
   `data/worlds/<name>/resolved/world.resolved.yaml`'s `entities` list (same file
   `compute_density()` already reads), returning `"monster_only_gauntlet"` if no entry's `role`
   field is in `{"worker", "guard", "merchant", "blacksmith"}`, else `"civilian_settlement"`. Wire
   into `build_worlds_section()` alongside `density`/`tier`/`scale`.
2. Regenerate `config/simulation_quality/corpus_registry.yaml` via
   `python3 tools/generate_corpus_registry.py` — real, computed output, not hand-edited.
3. **`tools/entity_lifecycle_score.py`**: in `cluster_paths()`'s output (`global` and per-group),
   add a `diversity_context` string field, looked up from `corpus_registry.yaml`'s `_worlds`
   section for the run's own `world` argument: `"monster-only gauntlet — low diversity is
   expected by design, not a defect"` for `monster_only_gauntlet` worlds, `None`/omitted for
   `civilian_settlement`. The raw `dominant_shape_share`/`distinct_shapes` numbers are unchanged —
   only an interpretive annotation is added.
4. Test: a new unit test confirming `wilderness_survival` (and `dungeon_crawl`,
   `quest_dense_frontier`) get the `monster_only_gauntlet` archetype and the tool's own output
   carries the context string; a civilian world (e.g. `sandbox_world`) gets no such annotation.
5. Docs: update `docs/simulation_quality/entity_lifecycle_score.md` /
   `docs/guides/entity_lifecycle_score.md` to explain the new field, and add a one-line pointer in
   `docs/simulation_quality/corpus_tier_taxonomy.md`.

## Acceptance-criteria map

| Criterion | Satisfied by |
|---|---|
| investigation.md surveys existing signals, confirms new field needed | Done — corpus_tier_taxonomy.md's tier ≠ archetype; corpus_registry.yaml is the right reuse point |
| plan.md specifies exact field(s) and surface point | This plan |
| Implemented, verified by a real test, not just a doc note | Step 4 |
| entity_lifecycle_score docs updated | Step 5 |
| Scoped pytest passes | test_plan.md |
