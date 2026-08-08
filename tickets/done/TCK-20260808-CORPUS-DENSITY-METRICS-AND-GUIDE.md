---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE
phase: open
date: 2026-08-08
tags: [simulation-quality, world, corpus]
---

# TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE

## Title
Compute real density metrics (multiple, not one) across the SimQ world corpus, extend
`corpus_registry.yaml` with them, and produce a technical spec + a practitioner guide for using
and observing density

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
A 2026-08-08 investigation into world density/pacing found real, working density mechanisms
already exist in this codebase (`src/world/spawn.py`'s area-aware formula,
`HighEntityDensityWarningRule`'s 50%-of-map-area validation warning) but scattered, undocumented as
a coherent concept, and not measured corpus-wide. `config/simulation_quality/corpus_registry.yaml`
(`TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY`) already has the raw counts (entity/region/
resource/building/quest/faction) needed to compute several real density ratios per world, but
doesn't compute or surface them.

This ticket produces: (1) multiple real density metrics, not a single number — different questions
need different ratios; (2) a technical document explaining each metric's formula/derivation and
where in the engine the analogous runtime concept lives; (3) a guide document for actually using
these metrics (how to compute one for a new world, how to interpret a high/low value, how to spot
an outlier).

## Scope
1. **Investigate**:
   - Confirm which density metrics are meaningfully distinct and worth computing separately —
     candidates: entity density (entity_count / total map area, from `topology.width × height` in
     each world's own `world.resolved.yaml`), per-region entity density (entity_count /
     region_count, coarser, already available in `corpus_registry.yaml` without new data),
     resource density (already precedented, `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE`),
     quest density (already precedented, `TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE`),
     faction density (factions / region_count, precedented informally in `crowded_frontier`'s own
     "gap 1" framing), building density. Do not invent a metric with no real question behind it —
     each one needs a stated "what does this tell you" purpose.
   - Confirm whether `topology.width`/`height` and per-region `bounds` are consistently available
     for every corpus world's own `world.resolved.yaml` (needed for the true area-based metric,
     not just the coarser count-ratio ones).
2. **Plan**: extend `tools/generate_corpus_registry.py`'s `_worlds` section (from
   `TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW`) with a `density` sub-object per world, computed
   from real data, not hand-transcribed. Design the technical doc
   (`docs/world/density_metrics.md` or similar — formulas, derivations, cross-references to
   `spawn.py`'s own runtime formula and `HighEntityDensityWarningRule`'s validation threshold) and
   guide doc (`docs/guides/world_density.md` — practical: how to compute density for a world
   you're authoring, how to read the corpus registry's own density figures, what counts as
   "dense"/"sparse" relative to the corpus's own real observed range).
3. **Implement**: the registry extension, both docs, and a scoped test confirming the computed
   density values are real (not placeholder) and internally consistent (e.g. entity density never
   exceeds `HighEntityDensityWarningRule`'s own 50% threshold for any currently-anchored world,
   which should already be true — a real assertion worth checking, not assuming).
4. Cross-reference `TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY`'s own new initial-generation density
   formula once it lands, if it lands before this ticket's own Implement phase — otherwise note it
   as a forward reference in the technical doc, don't block on it (this ticket's own metrics are
   about MEASURING existing worlds, not gating new generation).

## Out of Scope
- `TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY`'s own generation-time formula work — that ticket
  writes NEW worlds with density awareness; this ticket MEASURES existing worlds. Related, not
  the same work, and not blocking on each other.
- Changing `HighEntityDensityWarningRule`'s own threshold or severity — read-only reference.
- Building a live dashboard or automated alerting on density — a docs + registry-data ticket, not
  a new tool/service.

## Acceptance Criteria
- [x] investigation.md identifies the real, distinct density metrics worth computing, each with a
      stated purpose (6 metrics, none invented without one)
- [x] `corpus_registry.yaml`'s `_worlds` section extended with a `density` sub-object, computed
      from real data (`compute_density()`, reads real topology + scale counts, never
      hand-transcribed)
- [x] `docs/world/density_metrics.md` (technical): formulas, derivations, cross-references to
      `spawn.py`'s runtime formula and the validator's own threshold
- [x] `docs/guides/world_density.md` (guide): practical usage — computing density for a new world,
      reading the registry's own figures, interpreting relative to the corpus's real observed range
- [x] Scoped pytest passes, including a real assertion that no currently-anchored world's own
      density breaches `HighEntityDensityWarningRule`'s threshold

## Related Tickets
- TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY (generation-time density work — filed alongside this
  one, cross-referenced not blocking)
- TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY, TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW
  (built the `corpus_registry.yaml`/`_worlds` foundation this ticket extends — DONE)
- TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE, TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE
  (established resource/quest density as real, precedented corpus concepts — DONE)

## Related Docs
- `docs/world/raid_boss_camp_contract.md` (the runtime density formula precedent)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (points at `corpus_registry.yaml`, will need
  its own pointer to the new density docs once they exist)
- `docs/mechanics/06_worldbuilding_foundation.md` (topology/region bounds — the area data source)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY/`,
  `stored_artifacts/TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW/` (the registry this ticket extends)

## Related Code Areas
- `tools/generate_corpus_registry.py`
- `config/simulation_quality/corpus_registry.yaml`
- `src/world/spawn.py`, `src/world/spawn_config.py` (formula precedent, read-only reference)
- `src/worldbuilding/validator.py` (`HighEntityDensityWarningRule`, read-only reference)

## Assumptions / Open Questions
- Whether every corpus world's `world.resolved.yaml` is readily available/consistent enough to
  compute the true area-based metric for all 20 worlds, or whether some worlds' own resolved specs
  have gone stale/missing — not assumed; Investigate should check real file presence before
  committing to the area-based metric for every world (the coarser count-ratio metrics are a safe
  fallback if some worlds lack resolved specs).

## Implementation Notes
- **Subagent spawn cap reached this session** — Investigate/Plan/Implement/Document-Update/
  Parity/Verify performed directly.
- Confirmed (not assumed) all 20 corpus worlds have both real `world_compile_report.json` scale
  data and a real `resolved/world.resolved.yaml` with `topology.width`/`.height` — no missing/
  stale resolved specs, so the true area-based metric is safe for the full corpus.
- 6 density metrics selected, each with a stated real question (see investigation.md):
  `entity_density_per_area`, `entity_density_per_region`, `resource_density`, `quest_density`,
  `faction_density`, `building_density`. `resource_density`/`quest_density` deliberately reuse
  the EXACT metric definitions already established by `TCK-20260805-SIMQ-CORPUS-RESOURCE-
  DENSITY-DECOUPLE`/`TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE` rather than reinventing
  them. Deliberately did NOT compute a single combined density score — 6 distinct real questions,
  not collapsed into one number.
- `compute_density()` added to `tools/generate_corpus_registry.py`, wired into
  `build_worlds_section()`'s per-world entry as a new `density` sibling key (additive, no
  restructure — matches this file's own established backward-compat discipline from
  `TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW`).
- Real corpus-wide sanity check performed (not assumed true): every world's real
  `entity_density_per_area` sits ~2 orders of magnitude below `HighEntityDensityWarningRule`'s own
  `0.5` threshold (max observed 0.00297, `urban_political`; min 0.000168, `wilderness_survival`)
  — now a real regression assertion, not just a one-off check.
- **Parity**: none of this ticket's changed files (`tools/`, `tests/tools/`, `config/`, `docs/`)
  map to any tracked `docs/parity_ledger/` subsystem — `expected_subsystems_for_files()` and
  `find_p0_intersection()` both returned empty. Confirmed no parity ledger update is needed, not
  assumed — `behavior_changed=true` so this wasn't the blanket skip path, the real check ran and
  came back empty.
- Cross-referenced `TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY` per this ticket's own Scope item 4:
  that sibling ticket hasn't landed yet as of this Implement phase, noted as a forward reference
  in the technical doc, not blocking.

## Test Summary
- `tests/tools/test_corpus_registry.py` (extended, 10/10 pass, 4 new):
  `test_worlds_section_has_density_subobject`, `test_density_values_are_real_not_placeholder`,
  `test_density_values_internally_consistent_with_source_counts`,
  `test_no_world_breaches_high_entity_density_warning_threshold` (plus the existing
  `test_corpus_registry_committed_file_matches_fresh_generation` automatically now also covers
  density, since it compares the full `_worlds` output).
- Scoped run: `tests/tools/test_corpus_registry.py tests/tools/test_score_ceilings.py` — 16
  passed, 0 failed.
- Confirmed the one pre-existing, unrelated `hero_guild_routing_seed42_500t` grade-regression
  failure (`tests/simulation_quality/test_grade_regression.py`) exists identically on a clean
  `git stash` baseline — not caused by this ticket's changes, not fixed here (out of scope).

## Files Changed
- `tools/generate_corpus_registry.py` — new `compute_density()`, wired into
  `build_worlds_section()`
- `config/simulation_quality/corpus_registry.yaml` — regenerated, `_worlds.*.density` added
- `tests/tools/test_corpus_registry.py` — 4 new tests
- `docs/world/density_metrics.md` — new, technical doc
- `docs/guides/world_density.md` — new, practitioner guide
- `docs/simulation_quality/corpus_tier_taxonomy.md` — pointer to the 2 new docs

## Completion Summary
Computed 6 real, distinct density metrics (not a single number) across all 20 SimQ corpus worlds,
each with a stated purpose — 2 reuse exact prior-established definitions
(resource/quest density), 4 are new (entity-per-area, entity-per-region, faction, building).
Extended `corpus_registry.yaml`'s `_worlds` section with a computed `density` sub-object per
world, additive and backward-compatible. Wrote a technical doc cross-referencing the real
`HighEntityDensityWarningRule` threshold and `spawn.py`'s runtime formula, and a practitioner
guide with worked examples from the real corpus. Ran a real corpus-wide sanity check (no world
breaches the 50% warning threshold) as a new regression assertion, not just a one-off. No parity
ledger update needed — verified via the real check, not assumed.
