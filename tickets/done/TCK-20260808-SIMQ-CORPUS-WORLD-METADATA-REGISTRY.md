---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY
phase: open
date: 2026-08-08
tags: [simulation-quality, world, corpus]
---

# TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY

## Title
Consolidate the SimQ world corpus's scattered high-level facts (scale, tier, active feature flags,
archetype) into one structured, queryable registry — currently split across 3 docs and 17 profile
YAMLs with no single source of truth

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
A 2026-08-07/08 status discussion asked whether world complexity/features/size are tracked at a
high level. They are, but only as scattered prose/tables across 3 separate places: per-world
entity/region/resource/building/quest/faction counts live in
`docs/simulation_quality/eval_matrix_results.md`'s "Corpus World-Scale Summary" table (pulled from
`world_compile_report.json` but not kept in sync automatically); tier classification
(Unit/End-to-end/Stress/Regression) lives in `docs/simulation_quality/corpus_tier_taxonomy.md`'s
own table; and which feature flags are active for a given world lives only in
`config/simulation_quality/profiles/{name}.yaml` itself, cross-referenced by hand per ticket
(e.g. `corpus_tier_taxonomy.md`'s own per-world notes citing `ENABLE_SOCIAL_COOPERATION`,
`ENABLE_ADVENTURE_ROUTING` inline in prose). No single file answers "what does this world look
like" without reading 3+ sources.

This consolidation is a direct enabler for 3 sibling tickets: `TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE`'s
`content_threshold` ceiling kind needs per-world content facts to back its judgment calls;
`TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION` needs a clean place to register its new world's
own metadata without inventing a 4th scattered location; `TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION`
needs to know which worlds exist and their scale to decide baseline coverage.

## Scope
1. **Investigate**:
   - Confirm the exact fields already available per-world: `world_compile_report.json`'s schema
     (entity/region/resource-node/building/quest counts, `distinct_populated_factions`), each
     profile YAML's feature-flag overrides, and `corpus_tier_taxonomy.md`'s tier assignment +
     justification text per world.
   - Confirm all 17 (or current count) corpus worlds under `data/worlds/` and their corresponding
     `config/simulation_quality/profiles/*.yaml` — 1:1 mapping assumed, must be verified not
     assumed.
2. **Plan**: schema for a new registry file (likely
   `config/simulation_quality/corpus_registry.yaml` or `.json`, sibling to the profiles directory)
   — one entry per world: name, tier, scale metrics (from `world_compile_report.json`), active
   feature flags (from its profile), archetype/description (from `corpus_tier_taxonomy.md`'s
   existing prose, condensed), anchor run_keys that use this world (cross-reference
   `grade_anchors.json`'s key naming convention).
3. **Implement**: generate the registry (a script reading real `world_compile_report.json` +
   profile YAMLs + the taxonomy doc, not hand-transcribed — avoids the exact staleness problem
   this ticket exists to fix) and commit it. Add a `make` target (mirroring `docs-registry`'s own
   pattern) to regenerate it, so it can be kept fresh going forward rather than becoming a 4th
   stale source.
4. Update `corpus_tier_taxonomy.md` and `eval_matrix_results.md`'s scale-summary section to point
   at the new registry as the authoritative source, keeping their own prose as narrative
   explanation (the "why," not the "what") rather than removing them.

## Out of Scope
- Authoring any new worlds — this ticket only consolidates metadata for worlds that already exist
  (or get added by sibling tickets, which register into this file as part of their own work).
- Any change to `grade_anchors.json`, feature flags, or world content itself.

## Acceptance Criteria
- [ ] investigation.md confirms the real per-world field set and the current 1:1 world/profile
      mapping
- [ ] Registry schema designed and generated from real data (not hand-transcribed)
- [ ] Regeneration mechanism (script + make target) exists, matching `docs-registry`'s own pattern
- [ ] `corpus_tier_taxonomy.md`/`eval_matrix_results.md` updated to point at the registry
- [ ] Scoped pytest passes (if any validation test is added for the registry's own schema)

## Related Tickets
- TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE, TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION,
  TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION (all consume this registry — filed together)
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC, TCK-20260704-SIMQ-CORPUS-SCALE-METRIC (established the
  scattered sources this ticket consolidates)

## Related Docs
- `docs/simulation_quality/corpus_tier_taxonomy.md`
- `docs/simulation_quality/eval_matrix_results.md` ("Corpus World-Scale Summary" section)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `config/simulation_quality/profiles/*.yaml`
- `data/worlds/*/world_compile_report.json`
- `tools/generate_registry.py` (pattern precedent for a generated, regeneratable registry —
  not directly reused, `docs/REGISTRY.yaml` indexes docs/tickets, not worlds, but the same
  "generate from real data, never hand-transcribe" discipline applies)

## Assumptions / Open Questions
- File format (YAML vs JSON) — not assumed; Investigate/Plan should match whichever sibling
  consumers (ceiling ticket, perf-baseline ticket) find easier to load, likely YAML for
  consistency with `config/simulation_quality/`'s existing convention.

## Implementation Notes
Subagent spawn cap (200/200) reached earlier this session — Investigate/Implement/Verify performed
directly.

Investigate found the world/profile mapping is NOT 1:1 by filename (5 worlds have no
identically-named profile, 2 profiles — the `urban_political_selfmodel_*_probe` pair — have no
identically-named world), confirmed via direct file listing rather than assumed. Reused
`tools/evaluate_simq.py`'s own real, already-battle-tested `_resolve_world_name`/`_parse_run_key`
functions for this resolution instead of writing a second, potentially-diverging implementation —
spot-checked the probe case (`urban_political_selfmodel_probe_seed42_200t` correctly resolves to
`world_name: urban_political` with its own distinct `ENABLE_SELF_MODEL_COGNITION`/
`ENABLE_SOCIAL_COOPERATION` flags, different from `urban_political`'s own base profile).

Schema is per-`run_key` (79 entries, one per `grade_anchors.json` key), not per-world, since a
single world can host multiple run_keys with genuinely different active feature-flag sets (the
probe case). Tier classification was hand-transcribed once from `corpus_tier_taxonomy.md`'s own
table into the generator script's `_WORLD_TIER` dict — a one-time cost, since that doc now points
at the registry for numbers going forward instead of the reverse.

Found the compiled `frontier_extended` world's real entity/region counts (59/11) already differ
slightly from `corpus_tier_taxonomy.md`'s own stale prose (56/10) — direct, live confirmation of
exactly the staleness problem this ticket exists to eliminate.

## Test Summary
`tests/tools/test_corpus_registry.py` (new): 4 passed — covers full run_key coverage, world_name
resolution against real directories, scale-field accuracy vs. compile reports, and committed-file
freshness (guards the same staleness class `corpus_tier_taxonomy.md`'s own gap-list hit twice).

## Files Changed
- `tools/generate_corpus_registry.py` (new)
- `config/simulation_quality/corpus_registry.yaml` (new, generated, 79 entries)
- `tests/tools/test_corpus_registry.py` (new)
- `Makefile` (`simq-corpus-registry` target)
- `docs/simulation_quality/corpus_tier_taxonomy.md`, `eval_matrix_results.md` (point at registry)

## Completion Summary
Built the registry from real, live data end-to-end rather than transcribing scattered docs —
found and fixed a real, live staleness case (`frontier_extended`'s entity/region counts) as direct
evidence the consolidation was worth doing. Reused `evaluate_simq.py`'s own world/profile
resolution logic rather than re-deriving it, avoiding a second implementation that could
independently drift. First of 5 tickets in this batch; unblocks the ceiling, perf-baseline, and
large-scale-world tickets that follow.
