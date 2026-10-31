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

## Ruling 3 (2026-10-31): the trace chain and the groups.py finding

Relayed via lead-planner-u24 and lead-planner. The text below is word for word as relayed. Filed as TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP.

"(1) CHAIN ACCEPTED. (i) is met: the t42 difference is inside #769's changed logic (COMBAT_RETREAT 84.52 vs 123.40 via retreat_pull, +38.88 re-derived, only d914bace7 crosses REGION_STABILIZATION's 100). (ii) is met: the t63 split is the same chain, only earlier (extra 10006_30 from leader 18's t42 project, t84 dissolution, t104 first id split, t123 10006 vs 10007). Attribution stands: the anchor reds are #769's retreat change working through group objectives. The entity 3 line (objective to t143 vs t199, lost drains at t185-189) is downstream of that split and doesn't change attribution; record it in the evidence as an observed lead, not traced. Same for the parent's t62 arbiter not creating a retreat project (136 vs 100). No further tracing needed for this ticket.
(2) GROUPS.PY:308 IS A SEPARATE TICKET, SETTLED BEFORE THE RE-ANCHOR.
- The defect: `new_g_id = 10000 + len(state.groups) + len(groups_add_or_update)` derives an id from a count. That count includes in-place updates of existing groups (the dissolution markers at l.110 and l.170, the update at l.227), and it can collide with a live id, overwriting a live group record. That is a durable-state integrity defect: a live group silently disappears.
- It sits on the path that produces the anchors' group objectives. Re-anchoring on it means a second 162-run re-anchor after the fix. So the sweep keeps running as measurement only, and the re-anchor waits for the fix to merge. If the owner prefers to re-anchor now and accept a second move later, that is the owner's call, not rpg-planner's.
- The ticket is ubuntu's, from its id block:
  - Title along the lines of A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP.
  - Tier standard: it moves outcomes in every world where groups form after an update or dissolution.
  - Class Bug Fix divergence, with a parity entry under social_narrative.
- Investigation must establish:
  (a) what shrinks or overwrites state.groups so that a count collides with a live id (removal path vs dict overwrite on apply);
  (b) what the overwritten members' identity.group_id points to afterwards;
  (c) whether any other site mints group ids the same way.
- Fix shape (designer to confirm): ids allocated so they can never repeat, e.g. max over all retained ids (dissolved records are kept per TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED) plus ids pending this tick, plus 1. Any counter must be typed state, not a local.
- Acceptance:
  - a test with a dissolve-then-form in the same tick and across ticks: no live group is overwritten, and every member's group_id resolves to a live or dissolved record;
  - a hard-law style check that a GroupRecord id is never re-issued;
  - the seed-0 outcome change measured and disclosed.
- Dispatch needs the ubuntu owner's go. If the fix changes a cited mechanism's implemented_by, rpg-planner will supply the mechanisms.yaml note text then."

lead-planner's note, same message: the known-red entry stays in place until the re-anchor. Order among B, this ticket and the generator ticket comes once the owner has answered.
