---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT
tags: []
---

# investigation - TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT

## Finding
The v1 gate run on 7b1528861, crowded_frontier seed 45: raider 27 starved at t1091 shuttling on y=40. The neighbour view lists dead entities, and `_perceived_threats` had no alive test, so the tactical panic gate counted the corpses of workers 2 and 3 and guard 11 (dead since t877/883/75) as threats and fled from them each time the raider came near, while the hunger re-choice's `perceived_hostiles` already filtered the dead. Divergent predicates for the same question.

## Audit
Every get_neighbor_view and are_entities_hostile reader was checked: intelligence.py, intake.py, scorers.py, scorers_support, cooperation/providers, combat.py, legality and classify_neighbours already filter on alive; the three readers that did not were the panic gate, the appraisal and the saliency ranking (the fix). Grief, mourning and vengeance were verified not to read appraisal's ally and nemesis lists.

## Measured effect
Paired 7b1528861 to 23fbe0ecf (seeds 42-46, self-check byte-identical): people deaths frontier 142 to 130 (SE 2.23), urban 58 to 62 (SE 0.37), crowded 166 to 167 (SE 0.66), no drift; extinction stop in crowded (guard, merchant), accepted by the owner 2026-10-21. Frontier flight rises from live threats no longer crowded out by corpses (saliency slot share 29% to 11%); panic retreats on the frontier fall 16%.
