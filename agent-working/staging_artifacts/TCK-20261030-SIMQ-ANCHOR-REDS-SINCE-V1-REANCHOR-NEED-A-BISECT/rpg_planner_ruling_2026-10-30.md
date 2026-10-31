---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT
artifact_type: plan
date: 2026-10-30
tags: [simulation-quality, regression]
---

# rpg-planner ruling on the bisect result (2026-10-30)

Relayed via lead-planner-u24 and lead-planner to rpg-planner-ubuntu. The ruling is on the bisect result at rpg-ubuntu-simq-anchor-bisect-impl 5b1c1dd55: the first mover is d914bace7 (#769); urban_political_selfmodel_probe_seed42_200t WORLD 0.32 -> 0.25 (hazard_drain_applied 17 -> 12, region_trauma_delta 3 -> 2). The text below is word for word as relayed.

rpg-planner (u24)'s ruling on the bisect, relayed via lead-planner-u24 and lead-planner ("A clean bisect; thanks"):
Q1: YES, re-anchor rather than fix. #769 (div 2.139) is intended, and the WORLD drop is its direct effect. The re-anchor PR must cite d914bace7 / #769 / 2.139 and the bisect table, re-anchor that key, and remove the known-red entry. rpg-planner is sending rpg-designer an fyi.
Q2: YES to the sweep, sized as MEASUREMENT:
- Run the anchored corpus at a25619971 vs d914bace7, with the bisect's settings.
- List EVERY anchored key #769 moved, inside and outside tolerance.
- Re-anchor ONLY the out-of-tolerance keys, in the same PR with the same citation. Report the within-tolerance moves without touching them.
- If a key moved that #769's mechanism doesn't explain, STOP to rpg-planner.
rpg-designer's addition: before any re-anchor, ATTRIBUTE each of the 5 vanished hazard_drain_applied events (17→12) with the entity and the reason: (a) it retreated earlier under #769, or (b) it died earlier or never fought in that hazard region. If any vanished drain belongs to a NON-retreating entity, STOP to rpg-planner, and rule out a flight path crossing a hazard.
(iii) The re-measure at close still applies.
Process: rpg-planner is adding "behaviour-changing rpg tickets re-check SimQ anchors at close" to its review checklist.
Reviewer for the re-anchor PR: still pending the u24 owner's answer on lead-planner-u24.
Slot: the corpus sweep is a heavy run. Ask me for it after B's runs finish, pinned 4-5 under the same memory floor and before the perf window. If it won't fit today, it goes after perf.

## Ruling 2 (2026-10-31): the drain attribution STOP, option (b)

Relayed via lead-planner-u24 and lead-planner. Context: all 5 vanished hazard_drain_applied events belong to entity 3, a non-retreating entity. The text below is word for word as relayed, including item 1, which concerns TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED.

"1) (B) post-merge: PASS acknowledged. The cross-seed hash is identical at 0-3 and the first differences are unchanged. The push ask can proceed; it is the owner's call, via you.
2) SimQ attribution: option (b), trace the link first, then rule. Definition of 'direct effect' for ruling Q1: a drop counts as #769's effect if the EARLIEST behavioural difference between the runs is produced by #769's changed code (the retreat/flight logic in its two files), and every later difference descends from it. The entity whose events vanish need not be the one whose decision changed. A chain through group composition or id allocation is still #769's, since a deterministic engine has no other source of difference.
(b) must establish:
(i) that t42's difference (entity 18's withheld target, (70,50) vs (25,25)) is decided inside #769's changed path. Show the call and the branch.
(ii) the chain from t42 to t124 (group objective id 10006 vs 10007 looks like an allocation shifted by one). Find the first tick where group-objective creation differs (one extra or missing objective, or different membership) and show it is downstream of entity 18's changed behaviour.
Outcomes:
- Both shown: a #769 knock-on. Record the chain in the bisect evidence and release the 162-run sweep.
- (i) fails, i.e. the first difference is NOT in #769's changed logic: STOP. That is option (c), to the designer via rpg-planner.
- (ii) can't be closed in a short pair: report what was found and rpg-planner rules. Do not extend it into a long investigation.
The flight-path crossing doesn't need tracing unless (ii) leads there."
