---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261008-TWO-MODULES-DEFINE-THE-SAME-REGION-IDS-WITH-DIFFERENT-GEOGRAPHY-LATENT-COLLISION-NEAR-FOREST-WOLF-DEN
phase: done
date: 2026-10-08
tags: [world]
---

# TCK-20261008-TWO-MODULES-DEFINE-THE-SAME-REGION-IDS-WITH-DIFFERENT-GEOGRAPHY-LATENT-COLLISION-NEAR-FOREST-WOLF-DEN

## Title
Modules `nomadic_herd` and `wolf_den_near_forest` define regions `near_forest` and `wolf_den` with different geography; they are never composed together and the collision is guarded, so it is latent (retitled from TCK-20261008-TWO-MODULES-COMPILE-A-REGION-WITH-THE-SAME-ID-NEAR-FOREST).

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Lane B reported a compiled `highland_traverse` with two regions sharing the id `near_forest`. Not reproducible on `main` or on `milestone-d27-earn-then-buy`: the resolved `highland_traverse` has exactly one `near_forest` (plain, hazard 1.5, from `nomadic_herd`) and one `wolf_den`; no world in `data/worlds` has a duplicate region id (all checked). The collision is latent: both modules define the two ids, `WorldAssemblyResolver` raises "Duplicate region ID collision" (`resolver.py:358`) if they are ever composed together, and only `highland_traverse` uses `nomadic_herd` (none uses `wolf_den_near_forest` with it).

## Scope
A corpus pin test that every resolved world has unique region ids. No rename: the catalog biome lookup is by bare region id (`resolver.py:361-363`, then the part after the first underscore) and `runtime_regions.yaml` keys hazard and biome by `near_forest` and `wolf_den`, so a module-prefixed id loses that lookup and needs catalog rows plus regenerated resolved files; Lane B's ENV-08 batch is open on the same module. A generic "no two modules define the same region id" validator would reject legitimate alternates (`hometown` x3, `bandit_road` x2, `haunted_battlefield` x2).

## Out of Scope
- Renaming content; a content-schema change for alternates.

## Acceptance Criteria
- [x] The corpus pin test passes for every resolved world.
- [x] The latent collision and the bare-id lookup are recorded here.

## Related Tickets
- The d27 + earn-then-buy batch (Lane B), ENV-08.

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md` (integrity validation).

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-TWO-MODULES-DEFINE-THE-SAME-REGION-IDS-WITH-DIFFERENT-GEOGRAPHY-LATENT-COLLISION-NEAR-FOREST-WOLF-DEN/`.

## Related Code Areas
- `src/worldassembly/resolver.py` (358, 361-363), `data/content/world_modules/nomadic_herd.yaml`, `wolf_den_near_forest.yaml`.

## Assumptions / Open Questions
- If a future world composes `nomadic_herd` with `wolf_den_near_forest`, the assembler stops it; the rename then needs the catalog rows.

## Implementation Notes
Pin test only.

## Test Summary
`tests/unit/worldassembly/test_corpus_region_ids_are_unique.py` (one case per world).

## Files Changed
tests/unit/worldassembly/test_corpus_region_ids_are_unique.py.

## Completion Summary
Closed as latent; guarded by resolver.py:358 and the new corpus pin test.
