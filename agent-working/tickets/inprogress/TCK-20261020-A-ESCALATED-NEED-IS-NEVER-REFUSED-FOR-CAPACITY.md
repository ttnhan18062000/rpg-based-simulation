---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY

## Title
A hunger or sleep goal that wins scoring at or past its SURV-07 onset is admitted even when the project cap is full

## Status
INPROGRESS

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
- Bounded by the existing `not existing`: one project per need. Nothing is evicted, abandoned or resumed by this change.
- Audit of every gate where a winning escalated-need goal can be silently discarded, each with a verdict (draft: /mnt/data/scratch-rpg-implementer/step2_audit_draft.md; open item: the bandwidth trim, `DetourSuggestionSystem.enforce_bandwidth`).

## Out of Scope
- SUSPENDED not counting as live, eviction, expiry (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK, after v1).
- Why a need loses to town_return between hunger 60 and about 95 (asked of the designer).

## Acceptance Criteria
- At 3/3 SUSPENDED a hungry-past-onset entity gets a hunger project and eats; below the onset the cap still refuses; at most one project per need; the bs13 case.
- V3 = 0 on all 15 paired cases (gate harness); "no project, no capacity" counts per world before and after.

## Related Tickets
- TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT (step 1, base 23fbe0ecf)

## Related Docs
- docs/mechanics/04_strategic_cognition.md, docs/guidelines/intentional_divergences.md (2.77)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py, src/systems/strategic_systems/detour.py

## Assumptions / Open Questions
- Resolved (designer): the bandwidth trim (enforce_bandwidth, Law 194-197) removes live projects beyond the cap after admission, lowest (current first, then id descending) first. "proj_hunger_*" and "proj_fatigue_*" sort before "proj_resolve_blocker_*", so when the escalated project is no longer current (e.g. a detour displaces it) the trim drops it first. Awaiting a designer ruling.

## Implementation Notes
Change: `escalated_need_wins` (src/ai/goals/escalation.py) admits a winning HUNGER/FATIGUE goal at or past `need_is_pressing` at the capacity check (intelligence.py, `not existing and not has_project_capacity(...) and not escalated_need_wins(...)`). Two capacity trims drop live projects beyond the cap; both now leave a live hunger/sleep project alone, keyed on KIND (`live_projects_in_the_trim`, src/core/strategic.py): `DetourSuggestionSystem.enforce_bandwidth` (detour.py) and the authoritative `CapacityEnforcementPhase` (pipeline_phases/capacity_enforcement.py, lowest score first). Designer rulings: trim option 2, keyed on kind; admission at the onset.

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
tests/integration/observability/test_an_escalated_need_is_never_refused_for_capacity_through_the_real_kernel.py (5): hunger past the onset at 3/3 suspended gets a hunger project and eats; below the onset the cap refuses; at most one project per need and nothing evicted; an admitted need project that is not current survives both trims; the gate-run blacksmith 13 replay (pins current scoring, not the rule). tests/unit/strategic/test_project_capacity_counts_live_projects.py: the at-max-live test is split into below-onset (refused) and at-or-past-onset (admitted) and a `live_projects_in_the_trim` test. tests/unit/strategic + tests/unit/ai: 504 passed with the integration file; lint-imports 17 kept; import_contracts 17 kept; mypy_gate rc 0.

## Files Changed
src/ai/goals/escalation.py (new), src/core/strategic.py, src/systems/strategic_systems/intelligence.py, src/systems/strategic_systems/detour.py, src/engine/pipeline_phases/capacity_enforcement.py, tests/unit/strategic/test_project_capacity_counts_live_projects.py, the new integration test.

## Completion Summary
Open.
