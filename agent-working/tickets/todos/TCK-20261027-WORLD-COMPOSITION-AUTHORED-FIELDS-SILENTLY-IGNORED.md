---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261027-WORLD-COMPOSITION-AUTHORED-FIELDS-SILENTLY-IGNORED
phase: open
date: 2026-10-27
tags: []
---

# TCK-20261027-WORLD-COMPOSITION-AUTHORED-FIELDS-SILENTLY-IGNORED

## Title
World compositions author a module `order` and module `requires` that assembly silently ignores

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Split out of TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS. That ticket's rule moves out any item
that fires on corpus content. rpg-implementer-ubuntu measured two such items at origin/main
3b5fab1e9, over all 24 `data/worlds` compositions, through the resolver's own loaders. The evidence is
in that ticket's stored artifacts (`latent_paths_results.jsonl`, investigation.md).

1. **`order` is authored and not honoured.** 72 module refs in 11 worlds set `order`, 61 of them
   non-zero. Assembly uses it only for an initial sort; the topological sort then breaks ties
   alphabetically (`src/worldmodules/utils.py`, around L26 and L39). In 14 of 24 worlds the authored
   sequence differs from the executed one. A read-only experiment showed that letting authored order
   win the topological ties changes `world.resolved.yaml` in those 14 worlds. The U3 batch documents
   today's behaviour (schema description and assembly contract) without changing it.
2. **A dangling `requires` is skipped silently.** In `wilderness_survival`, both
   `wolf_den_near_forest` and `undead_battlefield` require `frontier_village_core`, which the world
   does not compose. The topological sort (`utils.py:18`) and the generator (`generator.py`, around
   L513-515) ignore the unmet requirement. No `requires` names a module missing from the repo; both
   cases name a real module the world simply leaves out.

## Scope
1. `order`, choose one with rpg-planner and record why:
   - (a) honour it as the tie-break, which changes 14 resolved worlds, so each needs a rebaseline and
     a check that the change is intended;
   - (b) remove the field from the schema and from the 11 world files;
   - (c) keep today's behaviour as documented (closing with no code change).
2. Dangling `requires`, choose one:
   - (a) raise, which means `wilderness_survival` must compose `frontier_village_core` or the two
     modules must drop the requirement;
   - (b) warn at resolve time;
   - (c) make `requires` mean "if present".
   Decide first whether `wilderness_survival` is meant to carry the village core. That is a
   world-design question.
3. Add a regression test for each change, and run the resolved-snapshot freshness guard
   (`test_resolved_snapshot_freshness`).

## Out of Scope
- Everything left in TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS: (d), (g) and (i).
- Region-id namespacing (#335).

## Acceptance Criteria
1. The `order` decision is recorded with rpg-planner's ruling. If (a) or (b) is chosen, every changed
   resolved world is listed and explained, never just regenerated.
2. The dangling-`requires` decision is recorded, and `wilderness_survival` resolves on purpose.
3. Every world-hash change is measured and attributed. If no change was intended, there is a
   hash-neutral proof.

## Related Tickets
- TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS (parent; the U3 batch)
- TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE (sibling survey)

## Related Docs
- The assembly contract and the world composition schema description (both updated for `order` in
  the U3 batch)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS/ (after that
  ticket closes)

## Related Code Areas
- src/worldmodules/utils.py, src/worldgeneration/generator.py, src/worldassembly/resolver.py
- data/worlds/*/world.yaml (11 files set `order`), data/worlds/wilderness_survival/

## Assumptions / Open Questions
- NOT dispatched. It needs `data/worlds` edits or world changes, which the U3 release excludes, so it
  waits for rpg-planner to release it.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
