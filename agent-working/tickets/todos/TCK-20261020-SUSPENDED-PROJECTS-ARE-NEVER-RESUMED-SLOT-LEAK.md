---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK

## Title
Suspended projects are never resumed and never expire, so they hold project slots forever (slot leak)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A traced blacksmith 13 on crowded_frontier s45 (2026-10-20, at 23fbe0ecf and in base 7b1528861). It holds 3 SUSPENDED resolve_blocker projects (plus 4 ABANDONED). Since divergence 2.77 (TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START), ACTIVE and SUSPENDED count as live against max_active_projects (3). Nothing resumes those three or ends them, so the entity sits at 3 of 3 for its whole life: 52 of 52 strategic calls from t1207 to t2227 in the fix arm, and 99 of 99 calls from t1207 to t3167 in base.

At intelligence.py:1771 (`if not existing and not has_project_capacity(...): return StrategicUpdate()`), every winning goal is discarded. Sampled every 20 ticks, 16 to 27 entities per gate world are in "no project, no capacity".

Before v1, the designer's step 2 (TCK for "an escalated need is never refused for capacity") covers survival needs only. This ticket is the root leak itself: suspended projects need a lifecycle that resumes or ends them. The designer ruled (2026-10-20) that this is new behaviour (a timer or a rule), so it goes after v1 and is measured against v1.

## Scope
- Designer first: the rule for when a SUSPENDED project resumes (for example, its blocker clears or the pre-empting goal ends) or ends (expiry, or it becomes unreachable), with its record and reason.
- Implement it in the authoritative path, with a typed transition, and keep 2.77's live predicate as it is.
- Tests: a suspended project resumes when its condition clears, ends under the ruled rule, and an entity can never hold 3 of 3 suspended projects indefinitely.
- Measure paired against v1 (seeds 42-46, D76), and report the "no project, no capacity" entity counts per world before and after.

## Out of Scope
- Reversing 2.77 (SUSPENDED stops counting as live): rejected by the designer.
- Eviction of a live project to make room: rejected (it needs a new choice rule).
- The escalated-need admission (before-v1 step 2).

## Acceptance Criteria
- The designer's rule is in Bible 04 and the parity ledger, with a divergence entry.
- No entity stays at capacity with only SUSPENDED projects past the ruled bound in the 3 gate worlds × seeds 42-46.
- D76 shows no unexplained drift against v1.

## Related Tickets
- TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START (2.77)
- TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT (the corpse fix, which exposed this)
- TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND
- TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1, §4
- docs/guidelines/intentional_divergences.md 2.77

## Related Stored Artifacts
- Lane A probes: /mnt/data/scratch-rpg-implementer/probes_hs/ (bs13_calls.py, bs13_trace.py), output in /mnt/data/scratch-rpg-implementer/cn_meas/

## Related Code Areas
- src/ai/intelligence.py (~L1771 capacity gate)
- src/core/strategic.py (is_live_project, has_project_capacity)

## Assumptions / Open Questions
- Context (designer, 2026-10-21): after step 2, `has_project_capacity` still counts the 1-2 exempt need projects. So ordinary-project admission sees them as used slots. That is acceptable before v1, because ordinary goals yield to escalated needs anyway. Revisit it with the slot-leak rule.
- Context (designer, 2026-10-21, from the step-2 paired run, crowded s46): the same bound is seen from the other side. An exempt need project leaves room for an ordinary project that the pre-step-2 trim would have removed: blacksmith 13's suspended fatigue project is exempt, so its combat_engage project against leader 30 survives and is resumed at t547 (live 4 of 3). This is the designed bound (ordinary projects up to the cap, plus at most one exempt project per need), not a leak. The slot-leak rule must keep it consistent.
- What suspends a resolve_blocker project, and does anything resume any project kind today? (Answered below.)

### Findings (rpg-implementer, 2026-10-21; read-only, nothing run; main 4099c0889, step 2 read from branch `rpg-escalated-need-not-refused-for-capacity` a634dcfd0; no fix proposed)
The code lives in `src/systems/strategic_systems/intelligence.py` (the ticket's `src/ai/intelligence.py` path is wrong); line numbers below are that file unless stated.

**1. What suspends a project (every path).** Exactly four writers set `status=SUSPENDED`; none of them is specific to `resolve_blocker`.
- `evaluate_project_switch` L1127-1131: when a candidate project outscores the CURRENT project it returns `[replace(current, SUSPENDED), candidate]` and sets `current_project_id` to the candidate. Callers: the detour path L1531 and the generic goal path L1776 (every winning goal that differs from the current project); L1708 is only a comment about it. This is the path that suspends a `resolve_blocker` project: it is suspended whenever any higher-scoring goal replaces it while it is current. Only an ACTIVE, current project is suspended this way.
- `src/engine/tactical.py` L117-129 `_suspend_project_for_threat`, called at L240: any hostile in the tactical pass suspends the ACTIVE current project and sets `current_project_id_set=""` (cleared).
- `src/systems/world_systems/events.py` L162-169 (near-death interpretation): suspends the ACTIVE current project; it sets `current_project_id_set=None`, which in `src/engine/patches.py` L511 means "unchanged", so `current_project_id` keeps pointing at the now-SUSPENDED project (the tactical path clears it, this one does not).
- There is no other writer (`grep SUSPENDED src`).

**2. Does anything resume a SUSPENDED project?** `resume_project` (L1139-1151) has exactly two production callers, and the tests call it directly (`tests/unit/strategic/test_project_continuity.py` L100, `test_interruption_resistance.py` L173):
- L1335-1337: only after a project of kind `detour` has COMPLETED. It resumes the FIRST SUSPENDED project in dict order, of any kind (`next(p for p in projects.values() if p.status == SUSPENDED)`). So it fires only when a detour completes, and then for one project.
- L1609-1613 (in the goal-selection step): when the winning goal's kind equals the kind of `existing = next(p for p in projects.values() if p.kind == best_candidate.kind)` and THAT project is SUSPENDED. `existing` is the first project of the kind in insertion order, of ANY status. So if the first stored `resolve_blocker` record is COMPLETED/ABANDONED and a later one is SUSPENDED, the suspended one is not resumed; a new ACTIVE project is built instead (L1668 and following).
- Nothing else: no threat-cleared, blocker-cleared, timer or need-satisfied resume. `docs/simulation/belief_and_detour_contract.md` L193 and `intelligence_system_contract.md` L70 describe resumption after a detour only. The tactical suspension (hostile present) and the near-death suspension have no matching resume at all.
- Consequence for the ticket's case: a SUSPENDED project of a kind that never wins scoring again, and that is not the first of its kind, is never resumed. The `existing` lookup is also why the capacity gate is not hit for a kind that has any stored record (below).

**3. Does anything end a SUSPENDED project?** Only the capacity trims, and only when the live count is over the cap.
- The per-project end conditions (rejection backoff, the 50-tick `resolve_blocker` timeout L1475, the shopping check L1478) all sit inside `if project and project.status == ACTIVE` for the CURRENT project (L1352), so a SUSPENDED, non-current project is never visited by them. The `resolve_blocker` 50-tick timeout therefore cannot end a suspended `resolve_blocker`. `process_project_outcome` (L1172) only runs for the current project's objective.
- No expiry, no unreachable check, no retention: `COMPLETED`/`ABANDONED` records are never pruned either (`docs/mechanics/04_strategic_cognition.md` L225 says so; open ticket `TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND`).
- Trims that remove live projects (and so can remove SUSPENDED ones): `DetourSuggestionSystem.enforce_bandwidth` (`detour.py` L147-246, from intelligence.py L623, L931, L1806): over `max_active_projects` live projects it keeps the CURRENT project first and then orders by `(0, project id)` descending, i.e. string order of `proj_{kind}_{tick}`, which is neither recency nor score, and removes the rest; and `CapacityEnforcementPhase` (`src/engine/pipeline_phases/capacity_enforcement.py` L88-98): when stored projects plus the update's adds exceed the cap, `CapacityService.trim_dict(live_projects(all), cap, score)` removes the lowest-SCORE live projects. Both only act when live > cap. The admission gate keeps a kind with no record at 3 of 3 (L1771), and a kind WITH any stored record passes the gate, so live can exceed the cap through those adds (the detour path L1531 and a kind with an existing record); by reading, that is the route by which a suspended project gets trimmed on main (not exercised here).

**4. Interaction with step 2's `live_projects_in_the_trim` (`src/core/strategic.py` L359-375, a634dcfd0).** It returns the live projects except ONE `hunger` and ONE `fatigue` project (the current one of that kind, else the newest by `created_tick`, ties by greater id); both trims above (`detour.py` L206, `capacity_enforcement.py` L98) read it instead of `live_projects`. `has_project_capacity` is unchanged, so the exempt need projects still count in the admission test. Effects on this ticket:
- The only existing end path for a suspended project (the trims) now cannot end a SUSPENDED hunger/fatigue project that is the exempt one of its kind (the step-2 docstring says "a suspended project is never evicted for it"), and a live cap-plus-two entity does not get trimmed back down for them. So step 2 removes the one route by which a suspended need project used to be ended, and adds up to two live projects that still count against admission: a need kind's suspended exempt project is a permanent slot until something resumes it, and the resume paths in (2) fire only on the goal's kind winning again or a detour completing.
- The step-2 admission (`escalated_need_wins`, `src/ai/goals/escalation.py`, used at intelligence.py L1772) lets an escalated hunger/sleep goal start without a free slot only when `not existing`; it never resumes or ends anything (its docstring says so). A suspended need project of that kind is `existing`, so it passes the gate and is resumed by L1610 when that need wins.
- It does not touch the `resolve_blocker` case: the three suspended `resolve_blocker` projects of the traced entity are not exempt, so the trims may still remove them when live > cap, but the gate keeps live at 3 so the trims are idle.

**What this leaves for the designer (no proposal):** the lifecycle needs a stated owner for each of the four suspend writers' resume/end condition; the two production resume paths are narrow (one detour completion, or the same kind winning, first-of-kind only); nothing ends a non-current suspended project except a trim that is idle at the cap; and the tactical and near-death writers differ on whether `current_project_id` is cleared.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
