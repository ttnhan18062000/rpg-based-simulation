---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE
artifact_type: test_plan
tags: [simulation-quality, world, corpus]
---

# Test Plan — TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE

New tests in `tests/tools/test_corpus_registry.py` (extending the existing `_worlds`-section
coverage from `TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW`):

1. `test_worlds_section_has_density_subobject` — every world entry has a `density` dict with
   exactly the 6 documented keys.
2. `test_density_values_are_real_not_placeholder` — spot-check 2-3 worlds' computed density
   values against hand-computed expected values from their own `scale`/topology data (not a
   tautological "computed == computed" check).
3. `test_density_values_internally_consistent_with_source_counts` — for every world,
   `entity_density_per_region * region_count` recovers `entity_count` (within float tolerance),
   and similarly for the other ratio metrics — catches a formula/field-mismatch bug.
4. `test_no_world_breaches_high_entity_density_warning_threshold` — the real assertion from
   investigation.md: every world's `entity_density_per_area < 0.5` (`HighEntityDensityWarningRule`'s
   own threshold), computed fresh from real topology + entity_count, not hardcoded expected
   values.
5. `test_corpus_registry_committed_file_matches_fresh_generation` (existing test, extended) —
   density sub-object included in the fresh-vs-committed comparison.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies real, distinct density metrics, each with a stated purpose | Done — 6 metrics |
| corpus_registry.yaml's `_worlds` section extended with a `density` sub-object | Implement |
| docs/world/density_metrics.md (technical) | Implement |
| docs/guides/world_density.md (guide) | Implement |
| Scoped pytest passes, including the real WORLD-WARN-002 threshold assertion | Tests 1-5 |
