---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY
artifact_type: investigation
tags: [simulation-quality, world, corpus]
---

# Investigation — TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY

## Docs Requiring Update

- `docs/simulation_quality/corpus_tier_taxonomy.md`: point at the new registry (Implement phase)
- `docs/simulation_quality/eval_matrix_results.md`: point Corpus World-Scale Summary at the new registry (Implement phase)

## World/profile mapping is NOT 1:1 by filename — confirmed, not assumed

`data/worlds/` has 18 world directories; `config/simulation_quality/profiles/` has 16 named
profiles + `default.yaml`. 5 worlds (`crowded_frontier`, `quest_dense_frontier`,
`resource_dense_basin`, `unit_faction_tension`, `wilderness_survival`) have no identically-named
profile file; 2 profiles (`urban_political_selfmodel_probe.yaml`,
`urban_political_selfmodel_execution_probe.yaml`) have no identically-named world directory.

The real resolution logic already exists and is authoritative:
`tools/evaluate_simq.py::_resolve_world_name(profile_name)` progressively strips trailing
`_segment` tokens from a profile name until a real `data/worlds/{name}/` directory is found (e.g.
`urban_political_selfmodel_probe` → `urban_political`) — "a profile can be a more specific variant
of a world," per its own docstring. `_parse_run_key(run_key)` extracts `(profile_name, seed,
ticks)` from a `grade_anchors.json` run_key via regex. **The registry generator must import and
call these exact functions rather than re-deriving world/profile resolution from filenames** —
reusing the real, already-battle-tested logic instead of a second, potentially-diverging
implementation.

## Real per-world/per-run_key field sources (confirmed by direct read)

1. **Scale**: `data/worlds/{name}/world_compile_report.json` — entity/region/resource-node/
   building/quest counts, `distinct_populated_factions` (already the source
   `eval_matrix_results.md`'s "Corpus World-Scale Summary" table cites).
2. **Tier**: `docs/simulation_quality/corpus_tier_taxonomy.md`'s per-world table — no machine-
   readable form exists today, will need to be transcribed once into the new registry (this is a
   one-time cost, not itself the source of ongoing staleness, since Implement wires
   `corpus_tier_taxonomy.md` to point AT the registry going forward, reversing today's direction).
3. **Active feature flags**: each profile YAML's own overrides against
   `src/domains/optimization/feature_flags.py`'s defaults (all `FeatureMode.OFF` except
   `ENABLE_PUSH_EVENT_SHAPERS`/`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, both `ON` by design, unrelated
   to per-world gameplay content).
4. **run_key coverage**: `tests/simulation_quality/fixtures/grade_anchors.json`'s own keys are the
   real, authoritative list of what SimQ actually calibrates — a world can exist under
   `data/worlds/` without ever being anchored (none currently, confirmed: all 18 world directories
   have at least one matching run_key prefix in `grade_anchors.json`, verified by direct
   cross-reference).

## Schema decision

Per-`run_key` entries (not per-world), since `run_key` is the real unit `grade_anchors.json`
already keys by, and a single world can host multiple distinct-purpose run_keys (different seeds,
tick counts, or profile variants like the `urban_political`/`urban_political_selfmodel_probe`
pair) with genuinely different active-flag sets. Each entry cross-references its resolved
`world_name` (via `_resolve_world_name`) so a consumer can still group by world when needed.

Format: YAML, `config/simulation_quality/corpus_registry.yaml` — matches the existing convention
of that directory (profiles, weights, detection_params all live there already) rather than
introducing a new top-level location.
