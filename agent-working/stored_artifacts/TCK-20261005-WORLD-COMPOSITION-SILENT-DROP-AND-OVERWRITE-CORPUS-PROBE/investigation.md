---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE
phase: done
date: 2026-10-05
tags: [world]
---

# investigation — TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE

Measured at base `94f7a3fe3` plus this branch's commits. Evidence: `corpus_probe_results.jsonl` in this folder (120 rows = 24 worlds x 5 checks,
one row per world and check, produced by `tools/world_composition_corpus_probe.py`). Sites re-derived at this commit, not copied from the survey.

## Result: all four suspicions fire zero times on the corpus
| check | worlds | worlds non-zero | total | what the detector actually examined |
|---|---|---|---|---|
| duplicate place ids | 24 | 0 | 0 | 52 places declared across 23 worlds; 0 compile errors; 0 places lost at compile |
| dropped placements | 24 | 0 | 0 | every population / resource / building region reference (guard from `TCK-20260915-...DANGLING-REGION-REFERENCE...` also raises) |
| faction first-wins merge | 24 | 0 | 0 | 147 module faction contributions; 0 not pre-seeded; 0 differing definitions |
| biome provenance | 24 | 0 | 0 | 104 regions, but only **4 namespaced** (one each in `frontier_extended`, `frontier_living_world`, `swamp_border_world`, `urban_political`) |
Zero is a real result here, but how strong it is differs per check: the biome check could not exercise its failing case in this corpus (see (f)), and the faction
check is structurally zero (see (c)).

## Per check
**(a) Place ids.** `compiler.py:437-438` is a bare `places[p_spec.id] = PlaceState(...)`, so a duplicate silently replaces the first. Reachable, not dormant: the
comment above it said places were "empty for all existing content" and was stale. No corpus composition has a duplicate (52 places, 23 worlds). World truth if it fired:
**yes** (a place disappears from the compiled state); fired zero times, no follow-up. Comment corrected at `compiler.py:433-439`.

**(b) Dropped placements / `WorldValidator`.** Region-reference drops are fixed by the compile pre-pass (`_assert_region_references_resolve`); the probe confirms 0 dangling
references per world. The ticket's open assumption "would `WorldValidator` actually catch an unknown-region reference" is answered: yes, `WORLD-REF-002/003/004`
check spawn, resource and building regions. **Residue** (rules the three unvalidated paths still skip): `WORLD-REF-001` faction existence, `WORLD-TOPO-001` bounds within topology,
`WORLD-WARN-001` no resources, `WORLD-WARN-002` high entity density, `WORLD-BUDGET-001..006`, `WORLD-REACH-001` participant reachability (and `WORLD-UNEXPECTED-SECTION`, which needs raw YAML).
Measured by running each rule on every resolved spec without raising: **74 issues across 17 of 24 worlds, 0 errors**: `WORLD-REACH-001` 72, `WORLD-WARN-001` 2, nothing else. So the
remainder is not empty (the validator is not dead on those paths), but on the corpus it would add warnings only. Adding the call to the three paths is out of scope for a probe.

**(c) Faction first-wins merge (`resolver.py:381-390`): structurally unreachable, not merely zero.** `resolver.py:322-326` pre-seeds `factions` with every catalog faction, and each
module's faction contribution is built from the same catalog (`:833-838`, `FactionSpec(id, type=alignment_bucket)`); a module naming a faction not in the catalog raises `ResolverError`
(`:836`, tested). So `if fac.id not in factions` can never be true for a valid composition and a "differing definition" cannot exist. Confirmed empirically: 147 contributions, 0
not pre-seeded, and 0 faction provenance records carry a `source_module` (the branch that would write them never runs). #335's namespacing leaving faction ids, place
`owner_faction_id` and quest ids unprefixed is correct by design: factions are global catalog ids, and quest id collisions already raise `AssemblyCollisionError` (WORLD-ASM-012).
World truth: no. This is dead code, a candidate for `TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS`.

**(f) Biome provenance (`resolver.py:365-368`, `split("_", 1)[1]`).** The fallback is wrong only when the namespace itself contains an underscore: `moon_cult_hometown` becomes
`cult_hometown`, finds no catalog region, and records no biome. Positive control (real resolver, synthetic module, namespace `moon_cult`) fires; namespace `trading` and no namespace stay quiet.
**On the corpus it cannot fire**: the four namespaced regions all use a single-word namespace, and the generator (which namespaces with module ids that contain `_`) only namespaces on a
collision, which no corpus world currently has. `generated_frontier_3_42` (the survey's suggestion) has no namespaced region. World truth: **no**. `biome_source` is read only to fill
the provenance record (`:368`, `:376`); the region's terrain and hazard come from the authored region. It affects provenance metadata read by the observability warehouse only.
Latent: reachable the moment a composition uses an underscore namespace.

## Not found / not done
No follow-up ticket is warranted for any of the four, and that is recorded rather than assumed: each fired zero times, (c) is dead code rather than a defect, (f) is latent and
provenance-only. Two observations are routed instead of ticketed: the dead faction-merge branch, and the `WorldValidator` residue. No behaviour changed in this ticket.
