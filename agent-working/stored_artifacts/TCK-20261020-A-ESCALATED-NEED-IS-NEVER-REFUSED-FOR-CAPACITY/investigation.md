---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY
tags: []
---

# investigation - TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY

## Finding
Crowded_frontier seed 45, blacksmith 13: three SUSPENDED resolve_blocker projects fill its cap of 3 (a suspended project counts as live, divergence 2.77). From hunger 60 (t1201) to 100 (t2001) the hunger goal wins scoring with a target, and the capacity check in `evaluate_strategic_intent` returns an empty update every brain tick; it starves at t2237 (V3). 16-27 entities per world sat at "no project, no capacity". This was EXPOSED, not caused, by the step-one fix: before it, raider 27 starved first at t1091 and masked the lock; the lock (and the V3 on crowded 45) was already in 7b1528861.

## Gates audited (silent discards of a winning escalated-need goal)
1. frozen/stunned early return: by design. 2. worker fast path: below the onset. 3. detour completion resume, rejection backoff, completion branches, resolve_blocker timeout: at most one brain tick of delay. 4. target-less winner skipped: by design. 5. capacity check in intelligence.py: THE LOCK, fixed. 6. `evaluate_project_switch` against a locked current project: not changed. 7. `enforce_bandwidth` trim: evicted an admitted need project once it was not current: fixed (second gate). 8. `CapacityEnforcementPhase`: the same trim, lowest score first: fixed (third gate, found during the build). 9. Outside this step: a need losing to town_return until about hunger 95 (TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95); a project pre-empted by AVOID_HOSTILE or PANIC.

## The unbounded first build and its correction
The first build exempted every live need project from both trims. Gate runs showed need projects piling up without bound (13 live projects against a cap of 3 for raider 38), because each need switch makes a new project id and the old one was never trimmed. The correction (designer ruling) exempts one live project per need kind; every older one is trimmed. Max live projects per entity after it: 5 (cap 3 plus 2) in all three traced cases.

## Measured
V3 on all 15 gate runs on the step: 12 clean, 3 owned known reds (crowded s46 raider 38 and frontier s44 worker 2, flight at near-death hp; urban s44 merchant 28, a crowded service door), each filed. Paired 23fbe0ecf to the step: frontier 130 to 127 (SE 0.68), urban 62 to 67 (SE 1.00), crowded 167 to 177 (SE 1.41), no drift; extinction stops frontier scout, crowded hero, scout, worker, accepted by the owner 2026-10-21.
