---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [simulation-quality, world]
---

# Investigation — TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS

## Scope item 1: does `corpus_tier_taxonomy.md`'s existing framing already cover this?

No — it's a related but distinct dimension. The Unit/End-to-end/Stress/Regression-baseline
taxonomy answers **why a world exists in the calibration corpus** (its testing purpose), not
**what kind of gameplay population it represents**. `wilderness_survival` and `dungeon_crawl` are
both classified `End-to-end` tier (same tier as `sandbox_world`/`urban_political`) even though
they have zero civilian population — the taxonomy doc's own per-world notes column already
mentions "no settlement module" in free prose for both, but this is not a structured, queryable
field. `config/simulation_quality/corpus_registry.yaml`'s `_worlds` section (the taxonomy doc's
own designated machine-readable source of truth) already carries `tier`/`scale`/`density` per
world but has no archetype/population-composition field either. Reuse the existing per-world
registry location, add a new field — not a new taxonomy document.

## Scope item 2: real, corpus-wide survey (all 20 worlds)

**A real, field-level pitfall found first**: `entity.identity.role` (the `EntityRole` IntEnum —
`HERO=0, SHOPKEEPER=1, MONSTER=2, CITIZEN=3, WORKER=4, GUARD=5`) is **not** a reliable signal —
direct inspection of `wilderness_survival`'s own compiled state shows all 11 entities (6
`sentinel`, 4 `predator_hunter`, 1 `alpha` — genuine monster content) carry `role=3` (`CITIZEN`),
not `role=2` (`MONSTER`). `EntityRole.MONSTER` appears effectively unused by this corpus's real
population-recipe spawning path — a real, disclosed, out-of-scope finding (not this ticket's own
problem to fix; noted for whoever next touches entity role tagging). The same class of pitfall as
the `entity.identity.faction` vs `properties["faction_id"]` correction found during
`TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS`'s own Investigate phase.

**The real, reliable signal is `entity.kind`** (a content-driven string, e.g. `"sentinel"`,
`"predator_hunter"`, `"worker"`, `"merchant"`) — directly available, per-entity, in each world's
own static `data/worlds/<name>/resolved/world.resolved.yaml` `entities` list (`role` field there,
confusingly named but distinct from `EntityRole` — matches `entity.kind` 1:1, confirmed by direct
comparison against a live-loaded `AuthoritativeState`). No live Kernel/world-compile needed to
read this signal — a static YAML read, matching `compute_density()`'s own existing pattern in
`tools/generate_corpus_registry.py`.

**Real survey result, all 20 corpus worlds** (via a live-loaded `AuthoritativeState.entities`,
cross-checked against the static resolved YAML):

| World | Population kinds | Has civilian-service kind? |
|---|---|---|
| `wilderness_survival` | sentinel, predator_hunter, alpha | **No** |
| `dungeon_crawl` | scout, raider, leader, predator_hunter, sentinel | **No** |
| `quest_dense_frontier` | sentinel (only) | **No** |
| all other 17 worlds | worker, guard, merchant, blacksmith (+ scout/raider/predator_hunter/etc. as hostiles alongside) | Yes |

**3 worlds, not just `wilderness_survival`, are genuinely civilian-population-free**:
`wilderness_survival`, `dungeon_crawl`, and `quest_dense_frontier` — all zero `worker`/`guard`/
`merchant`/`blacksmith` presence. `dungeon_crawl`'s own authored description already says "No
settlement — pure dungeon exploration"; `quest_dense_frontier`'s own description says "standalone,
no settlement dependency" (composes `ruins_mystery_quest`, 6 `sentinel` entities). This is a
real, corpus-wide pattern, not a one-off — the archetype field must cover all 3, not just the one
this ticket's own Request Summary was originally grounded in.

**Classification rule** (real, evidence-based, not invented): a world is `monster_only_gauntlet`
if none of its resolved population entries' `role` field is in `{"worker", "guard", "merchant",
"blacksmith"}` (the 4 kinds present in every one of the other 17 worlds, zero exceptions);
otherwise `civilian_settlement`. A small, explicit, human-verified 2-value enum is sufficient —
the corpus's real population composition is genuinely bimodal (either has the standard civilian
service quartet, or has none of it at all), no world sits in between.

## Scope item 3: where should this live?

**`config/simulation_quality/corpus_registry.yaml`'s `_worlds` section** — reusing the exact
precedent `density`/`scale`/`tier` already established (`TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY`,
`TCK-20260808-CORPUS-DENSITY-METRICS-AND-GUIDE`), computed by `tools/generate_corpus_registry.py`
from real data (not hand-transcribed), regenerated via `make simq-corpus-registry`. Surfaced by
`tools/entity_lifecycle_score.py`'s `cluster_paths()` output as a `diversity_context` string
annotation alongside `dominant_shape_share` — the raw number stays honest, only the interpretation
gets context, matching the ticket's own Plan guidance.

## Docs Requiring Update

- `docs/simulation_quality/entity_lifecycle_score.md`: explain the new `archetype`/
  `diversity_context` mechanism and the `entity.identity.role` vs `entity.kind` field pitfall
- `docs/guides/entity_lifecycle_score.md`: practitioner-facing guidance on reading
  `diversity_context` when present
- `docs/simulation_quality/corpus_tier_taxonomy.md`: one-line pointer to the new
  `corpus_registry.yaml` `archetype` field, since its own per-world table already gestures at "no
  settlement module" in free prose for 2 of these 3 worlds
