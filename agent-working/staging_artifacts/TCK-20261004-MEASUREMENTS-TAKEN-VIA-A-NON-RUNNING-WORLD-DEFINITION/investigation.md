---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION
artifact_type: investigation
tags: [world, content, investigation, simulation-quality]
---

# Investigation (Scope step; nothing annotated, retired or edited yet)

Method: read each closed ticket's own text for the loader and file it names, then re-take the compile-time measurements through the production path with `live_world_probe.py` (rows in `live_world_probe_results.jsonl`): `WorldRepository("data/worlds").load_world_with_context(world)` -> `WorldCompiler.compile(spec, seed=42, context=ctx)`, all 24 worlds, no kernel run. No heavy run was needed.

## UQ-3: the shorthand resolved to ticket IDs
- CAMP-STATE = `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`
- DEMOGRAPHIC-COHORT = `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED`
- UNREACHABLE-CLASSIFY = `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED` is the one that repeats the same experiment on `data/content/world_compositions/frontier_living_world.yaml`. Two other classify tickets also ran `frontier_living_world` seed 42 on the kernel (`-DEAD-GUARD`, 1,500 ticks; `-WAVE-CONFIRM`, 3,000 ticks, "canonical harness, PROD_SMALL") but their text does not name the loader, so I could not establish their path by reading; they are listed, not cleared.

## AC 1: measurement path, as a fact read from each ticket
All three name `data/content/world_compositions/frontier_living_world.yaml` (the catalog copy, deleted by #328 at 1c59e01f4) resolved through `WorldAssemblyResolver.assemble()` then `WorldCompiler.compile(seed=42)`:
- CAMP-STATE (line 134 of the ticket, and "holds under either loader" at line 49).
- DEMOGRAPHIC-COHORT (line 122, "resolved via `WorldAssemblyResolver.assemble()`").
- UNREACHABLE-CLASSIFY-NEVER-SEEDED (line 291; investigation.md:23).
The probe scripts are not on disk, so the file named in the ticket text is the evidence of path.

## Re-taken through the production path (frontier_living_world, 7 composed modules)
| closed ticket's claim | catalog-path result | production-path result | verdict |
|---|---|---|---|
| CAMP-STATE: 2 `CampState` entries, `goblin_camp_place` and `wolf_den_nest` | 2 | 2, same two ids | SURVIVES |
| DEMOGRAPHIC-COHORT: cohorts ARE seeded (the "never seeded" premise is false) | 6 of 7 regions non-empty, `near_forest` `{}`, `hometown` {4,6,3} | **8 of 9** regions non-empty (the extra regions are `trading_hometown` and a populated `near_forest`), `hometown` {4,6,3} unchanged, largest bracket 6 | CONCLUSION SURVIVES; the figure "6 of 7" and "near_forest gets {}" do NOT reproduce on the world that ran |
| UNREACHABLE-CLASSIFY-NEVER-SEEDED: same two experiments | same | same as above | same verdicts |

## AC 2: does `TCK-20260930-DEMOGRAPHIC-COHORT-NET-DELTA-TRUNCATES-TO-ZERO` depend on these?
Its defect is arithmetic (`int(count * 0.01) == 0` for count < 100, `cohort.py:377-381`), independent of which definition was measured. Its premise quotes two measured facts: "`hometown` declares 13, which splits into {4,6,3}" (reproduced on the production path) and "the largest seeded bracket in the corpus is 6" (a 9-world statement). On the production path over all 24 worlds the largest compile-time bracket is **8** (several worlds, for example `hero_guild_routing`, `urban_political`, the `unit_information_*` worlds); the ticket's own 2026-09-30 narrowing already records "largest bracket ever observed = 8" from its runtime probe. 8 also truncates to zero, so the premise survives. Verdict: depends on none of the three measurements in a way that matters; at most the "6" wording could be corrected to "8 on the 24-world production corpus". The ticket is not edited here.

## AC 3: other catalog-path measurements (search method stated)
Method: `git grep -l "world_compositions/<id>"` over `agent-working/stored_artifacts`, `agent-working/tickets/done` and `docs` for the five divergent worlds, then reading only which of them describe a measurement. `docs/parity_ledger`, `docs/simulation_quality` and `registries` only mention the retirement (`infrastructure.yaml:2017`, `substrate.yaml:5121`) or already say the mirror is frozen (`eval_matrix_results.md:890,1042`); none cites a catalog-path measurement as evidence.
Candidates, NOT yet read for "measurement vs plain mention" (counts of files naming the catalog file): frontier_living_world 16, frontier_extended 7, swamp_border_world 6, urban_political 9, dungeon_crawl 12. Those most likely to hold a measurement: `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` (investigation), `TCK-20260821-WOLF-DEN-NOISE-MIGRATION` (investigation), `TCK-20260627-P0B-URBAN-RESOURCE-NODES` (investigation), `TCK-20260824-TOWN-CENTER-POINTER-FIX` (investigation), `TCK-20260627-P1I-WORLD-BALANCE-FIX` (already handled by the CLOSED-P1 ticket). The rest are plans and tickets that name the file as a path.
Result so far: no catalog-path measurement found in parity `v2_evidence`, SimQ baselines or the registry; the stored-artifact candidates above are enumerated, not classified.

## AC 4: is the existing guard enough for this defect class? (read, not run)
The defect was two definitions of one `world_id` (a catalog copy and `world.yaml`), with a measurement free to read the wrong one. Two guards now exist and, together, cover it without a second mechanism: (1) `data/content/world_compositions/` is deleted and `tests/unit/content/test_content_paths.py` pins that the path config no longer carries it, so a second source cannot be read by the standard loaders; (2) `tests/integration/worldassembly/test_resolved_snapshot_freshness.py::test_committed_snapshot_equals_fresh_resolve` asserts, for every composition world (24), that the committed `resolved/world.resolved.yaml` equals a fresh resolve of `world.yaml` byte for byte (stricter than the six-count-field comparison the ticket text describes; that comparison was not found in this file). That second guard also means a measurement through `world.yaml` and one through `resolved/` cannot differ. Proposed answer: sufficient, no extension. Not covered, and not this class: a measurement script that loads some other path by hand; that is caught only by stating the loader in the measurement's record, which this ticket's findings already show was missing.
