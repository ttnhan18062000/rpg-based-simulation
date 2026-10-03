---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS
artifact_type: test_plan
phase: investigate
date: 2026-08-08
tags: [simulation-quality, world]
---

# Test Plan — TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS

## New tests

**`tests/tools/test_corpus_registry.py`** (matching existing conventions —
`test_worlds_section_has_density_subobject`/`test_density_values_are_real_not_placeholder`):
1. `test_worlds_section_has_archetype_field` — every `_worlds` entry has an `archetype` key,
   value in `{"civilian_settlement", "monster_only_gauntlet"}`.
2. `test_monster_only_gauntlet_worlds_correctly_identified` — `wilderness_survival`,
   `dungeon_crawl`, `quest_dense_frontier` are `monster_only_gauntlet`; a real civilian sample
   (`sandbox_world`, `urban_political`) are `civilian_settlement`.
3. `test_corpus_registry_committed_file_matches_fresh_generation` (existing test) — must still
   pass after regeneration, confirming the committed file matches a fresh run including the new
   field.

**`tests/tools/test_entity_lifecycle_score.py`**:
4. `test_diversity_context_annotation_for_monster_only_world` — real or synthetic
   `wilderness_survival`-shaped run scored via `score_run()`/`cluster_paths()`; assert
   `clustering["global"]["diversity_context"]` is present and non-empty.
5. `test_no_diversity_context_for_civilian_world` — a civilian-archetype world's `cluster_paths()`
   output has `diversity_context` absent or `None`.

## Regression guard

- `pytest tests/tools/test_corpus_registry.py tests/tools/test_entity_lifecycle_score.py -q`
