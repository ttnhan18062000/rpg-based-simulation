---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY

## Title
A hunger or sleep goal that wins scoring at or past its SURV-07 onset is admitted even when the project cap is full

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Blacksmith 13 of crowded_frontier seed 45 holds three SUSPENDED resolve_blocker projects (cap 3; a SUSPENDED project counts as live, divergence 2.77). From hunger 60 (t1201) to 100 (t2001) the hunger goal wins scoring with a target, and the capacity check at intelligence.py (`not existing and not has_project_capacity`) returns an empty update every brain tick; it starves at t2237 (V3). 16-27 entities per world sit at "no project, no capacity". Owner: fix before v1, as step 2, stacked on the corpse fix (23fbe0ecf).

## Scope
- Admit a winning HUNGER or FATIGUE goal at or past the existing onset (`need_is_pressing`: ESCALATION_ONSET of the consequence line; no new constant) at a full cap.
- Bounded by the cap plus two: one live hunger and one live sleep project (the current one, else the newest) are outside both trims, older need projects are trimmed. Nothing is evicted, abandoned or resumed by this change.
- Audit of every gate where a winning escalated-need goal can be silently discarded, each with a verdict (under Implementation Notes).

## Out of Scope
- SUSPENDED not counting as live, eviction, expiry (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK, after v1).
- Why a need loses to town_return between hunger 60 and about 95 (asked of the designer).

## Acceptance Criteria
- At 3/3 SUSPENDED a hungry-past-onset entity gets a hunger project and eats; below the onset the cap still refuses; at most one project per need; the bs13 case.
- V3 = 0 on all 15 paired cases (gate harness); "no project, no capacity" counts per world before and after.

## Related Tickets
- TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT (step 1, base 23fbe0ecf)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (sections 1 and 4), docs/guidelines/intentional_divergences.md (2.77, 2.137), docs/parity_ledger/strategic_cognition.yaml (STRAT-286), docs/plans/systemic_world/owner_decision_memo.md (row 84 (2)), docs/plans/systemic_world/v1_disclosure.md (N9, N10, N12-N15)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY/ (plan, investigation, test_plan).

## Related Code Areas
- src/systems/strategic_systems/intelligence.py, src/systems/strategic_systems/detour.py

## Assumptions / Open Questions
- Resolved (designer): the bandwidth trim (enforce_bandwidth, Law 194-197) removes live projects beyond the cap after admission, lowest (current first, then id descending) first; "proj_hunger_*" and "proj_fatigue_*" sort before "proj_resolve_blocker_*", so a no-longer-current need project was dropped first. Ruled: one need project per kind is exempt from both trims (option 2, keyed on kind), stale duplicates are trimmed (the cap-plus-two bound).

## Implementation Notes
Change: `escalated_need_wins` (src/ai/goals/escalation.py) admits a winning HUNGER/FATIGUE goal at or past `need_is_pressing` at the capacity check (intelligence.py, `not existing and not has_project_capacity(...) and not escalated_need_wins(...)`). Two capacity trims drop live projects beyond the cap; both now leave a live hunger/sleep project alone, keyed on KIND (`live_projects_in_the_trim`, src/core/strategic.py): `DetourSuggestionSystem.enforce_bandwidth` (detour.py) and the authoritative `CapacityEnforcementPhase` (pipeline_phases/capacity_enforcement.py, lowest score first). Designer rulings: trim option 2, keyed on kind, bounded to ONE live project per need kind (the current one, else the newest by `created_tick`); admission at the onset. `has_project_capacity` still counts every live project (the slot-leak ticket owns that). Exposed, not caused: the lock was in 7b1528861; the step-one fix removed the earlier starvation (raider 27) that hid it. The CapacityEnforcementPhase audit verdict (gate 8 below): it is the authoritative trim and had the same defect as `enforce_bandwidth`; both now read `live_projects_in_the_trim`. The mechanism registry binds `escalated_need_wins` under `goal_hierarchy`.

Audit of every gate where a winning escalated-need goal can be silently discarded (verdicts):
1. Frozen/stunned early return: by design (status ends on its own).
2. Worker fast path: cannot (hunger < 50, below the onset).
3. Detour completion resume / rejection backoff / completion branches / resolve_blocker timeout: delay of one brain tick at most, not a discard.
4. Target-less winner skipped (utility < 20 or no target): by design (no way open = no project; fatigue sleeps in place).
5. Capacity check (intelligence.py): THE LOCK, fixed here.
6. evaluate_project_switch against a locked current project: admission is only into a free slot or a winning switch; a hunger score of 160 passes the urgency floor; not changed.
7. enforce_bandwidth trim (detour.py): evicted the admitted need project once it was not current, and a suspended project when it was: fixed here (second gate).
8. CapacityEnforcementPhase (pipeline): same trim, lowest score first: fixed here (third gate).
9. Outside this step: a need that loses scoring to town_return until about hunger 95 (TCK-20261020-TOWN-RETURN-OUTBIDS-AN-ESCALATED-NEED-UNTIL-ABOUT-95); a project that exists but is pre-empted by AVOID_HOSTILE/PANIC.

## Test Summary
tests/integration/observability/test_an_escalated_need_is_never_refused_for_capacity_through_the_real_kernel.py (5): hunger past the onset at 3/3 suspended gets a hunger project and eats; below the onset the cap refuses; at most one project per need and nothing evicted; an admitted need project that is not current survives both trims; the gate-run blacksmith 13 replay (pins current scoring, not the rule). tests/unit/strategic/test_project_capacity_counts_live_projects.py: the at-max-live test is split into below-onset (refused) and at-or-past-onset (admitted) and a `live_projects_in_the_trim` test. the per-kind bound adds a unit test (the pick rule) and a 600-tick real-kernel switching test (at most the cap plus two). The old test `test_an_entity_holding_max_live_projects_still_cannot_start_a_new_kind` is replaced by the split tests above (designer ruling: an escalated need is admitted at a full cap). tests/unit/strategic + tests/unit/ai: 500 passed; lint-imports 17 kept; import_contracts 17 kept; mypy_gate rc 0; mechanism-registry tests pass. Full tests/unit serial on the PR tip: 8442 passed; the 9 failures are the pre-existing SimQ grade anchors (TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED, red on 7b1528861 too).

## Files Changed
src/ai/goals/escalation.py (new), registries/mechanisms.yaml (binding), tests/unit/tools/test_mechanism_registry_completeness_check.py (pin 345), src/core/strategic.py, src/systems/strategic_systems/intelligence.py, src/systems/strategic_systems/detour.py, src/engine/pipeline_phases/capacity_enforcement.py, tests/unit/strategic/test_project_capacity_counts_live_projects.py, the new integration test.

## Completion Summary
Done on branch rpg-escalated-need-not-refused-for-capacity (step two of the v1 fix PR, on top of the dead-are-not-threats step).

- **Divergence**: 2.137 (class Enforced); parity STRAT-286; memo row 84 (2); v1 disclosure N9, N10, N12-N15.
- **Measured**: V3 on all 15 gate runs: 12 clean, 3 owned known reds (N14 crowded service door; N15 flight at near-death hp, two cases). Paired 23fbe0ecf to the step, seeds 42-46, 5000 ticks: frontier 130 to 127 (SE 0.68), urban 62 to 67 (SE 1.00), crowded 167 to 177 (mean +2.0 per seed, SE 1.41), no drift; extinction stops (frontier scout; crowded hero, scout, worker) accepted by the owner, 2026-10-21. "No project, no capacity" and hunger 95+ with no project before to after: frontier 42 six to one, urban 42 two to none, crowded 45 five to one (a transient).
- **Flight**: crowded flight per 1000 alive-ticks 27 to 49, all from live threats, mostly subjects now out serving a need (flight onsets with a need project 10 percent to 23 percent); re-onsets as a share of decisions 0.0119 to 0.0260 (base 0.0276), mostly merchant 12 fleeing goblin leader 30 (C4), whose losses are all ledger hits.
- **Mechanism advisory** (report-only): names `strategic_intelligence_core` (detour.py, intelligence.py) and `cognition_capacity_fatigue` (capacity_enforcement.py) as cited code that changed without their entries; `escalated_need_wins` is bound under `goal_hierarchy`. The two entries describe the capacity trims, whose scope is unchanged in kind (one need project per kind is now outside the count); entry content is the planner's, reported to rpg-planner.
- **Follow-ups filed**: after-v1 slot-leak ticket (suspended projects never resumed, `has_project_capacity` counts exempt projects), town_return outbidding an escalated need (N13), fresh project id on re-admission (P2).
