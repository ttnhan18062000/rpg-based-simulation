---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY
artifact_type: plan
tags: [simulation-quality, world, corpus]
---

# Plan — TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY

## Steps

1. **`tools/generate_corpus_registry.py`** (new): for every key in
   `tests/simulation_quality/fixtures/grade_anchors.json`, parse `(profile_name, seed, ticks)` via
   `evaluate_simq._parse_run_key`, resolve `world_name` via `evaluate_simq._resolve_world_name`,
   read `data/worlds/{world_name}/world_compile_report.json` for scale fields, read
   `config/simulation_quality/profiles/{profile_name}.yaml` (falling back to `default.yaml`) for
   active (non-default) feature flags, and hand-transcribe each world's tier + one-line archetype
   description from `corpus_tier_taxonomy.md`'s existing table (one-time; the doc points at the
   registry afterward, not the reverse).
2. Write `config/simulation_quality/corpus_registry.yaml`.
3. Add `make simq-corpus-registry` target (mirrors `docs-registry`'s pattern).
4. `tests/tools/test_corpus_registry.py`: the 3 tests from test_plan.md.
5. Update `corpus_tier_taxonomy.md`/`eval_matrix_results.md` to point at the registry as the
   machine-readable source, keeping their own prose as narrative "why."

## Acceptance-criteria map

| AC | Step |
|---|---|
| investigation.md confirms real field set + 1:1 mapping (found NOT 1:1, resolved via real code) | Investigate (done) |
| Registry generated from real data | Steps 1-2 |
| Regeneration mechanism (script + make target) | Steps 1, 3 |
| Docs point at registry | Step 5 |
| Scoped pytest passes | Step 4 |
