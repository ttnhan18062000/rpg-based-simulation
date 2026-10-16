---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT
artifact_type: investigation
tags: []
---

# investigation - TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT

- Catalog terrain ids are lower case; the checks named upper-case WALL, FOREST, MOUNTAIN, HILL, so neither ever fired (cover and high ground had never worked).
- Paired measurement (30 runs, 3 worlds, seeds 42-46, 5000t): identical to base in every counter; people deaths 138/58/170 in both arms; self-check byte-identical.
- Probe (seed 42): both reads reached (354/235/501 calls), always false. No gate world has a mountain tile; urban has no cover tile; where cover tiles exist (forest, cave, ruin) the tile behind the defender was never one. The modifiers are dormant in the gate worlds; unit tests are the proof (see 2.129).
- The crowded workers are extinct in every seed in both arms (base-state); rpg-planner ruled the owner's stop rule means a step that takes them to 0, which this does not.
- Knowledge index was missing; docs were located by targeted grep.
