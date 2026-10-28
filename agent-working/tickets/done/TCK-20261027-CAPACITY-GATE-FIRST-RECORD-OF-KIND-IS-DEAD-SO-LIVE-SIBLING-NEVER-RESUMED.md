---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED
phase: done
date: 2026-10-27
tags: []
---

# TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED

## Title
Strategic winner lookup takes the first project of the kind in dict order (often a dead record), so the live SUSPENDED sibling is never resumed, a duplicate is created over the cap and the trim evicts the entity's own suspended project

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by the HUNGER step A capacity-refusal confirm runs (2026-10-27; data
`/mnt/data/scratch-rpg-implementer/stepA/confirm/{R,base}_{42,43}.json`, probe `stepA/confirm_probe.py`,
dump `stepA/proj_dump.py`). Ruled a base defect, its own ticket and its own measured step after step A
(rpg-designer, 2026-10-27).

`src/systems/strategic_systems/intelligence.py:1610` (at 358f4cb7f / 3533fde71):
`existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)` matches a
project of ANY status and takes the first in dict order. Observed on frontier_living_world, base arm:
- s42 t530 guard 11: first match `proj_combat_engage_129` COMPLETED; s43 t326 scout 15: first match
  `proj_combat_engage_5` ABANDONED.
- `:1612` resumes only when that first match is SUSPENDED, so it does not resume, although 3 SUSPENDED
  combat_engage projects sit later in the dict.
- `:1773` `not existing` is False, so the capacity gate is skipped; `evaluate_project_switch` creates a new
  ACTIVE engage (4 live of max 3).
- `CapacityEnforcementPhase` (`src/engine/pipeline_phases/capacity_enforcement.py` ~103,
  `live_projects_in_the_trim`) then evicts the entity's own oldest SUSPENDED engage (`_449` / `_185`).

Already disclosed (Bible 04 line ~229): "a goal whose kind already has a stored record, of any status, passes
the capacity gate exactly as before". NOT disclosed: the dead-first lookup that blocks resume of the live
sibling, the duplicate over the cap, and the self-eviction.

## Scope
1. The winner lookup resumes the live record of the kind first: a SUSPENDED project of the kind wins over any
   dead (COMPLETED/ABANDONED) record, independent of dict order. Deterministic choice when several live
   records of the kind exist (state the rule, e.g. newest `created_tick`, and test it).
2. Decide, with rpg-designer, whether a kind with ONLY dead records still bypasses the capacity gate. Designer
   lean: no, a dead record is not a reason to pass (then only escalated needs (2.137) pass a full cap).
3. Bible `docs/mechanics/04_strategic_cognition.md` capacity paragraph: rewrite the "of any status" sentence
   to the new rule; update divergences 2.77 and 2.137 (and add a new divergence entry, Bug Fix); parity
   ledger entries for the capacity gate in `strategic_cognition.yaml`.
4. Tests: dead-first-in-dict with a SUSPENDED sibling resumes the sibling (no new project, no eviction);
   the dead-only case per decision 2; escalated need unchanged.
5. Measured step: `tools/rpg_measure` paired run against the step-A-landed base, 3 worlds x s42-46 x 5000t.
   This changes base behaviour for every project kind.

## Out of Scope
- HUNGER step A and its flight. The COMBAT_RETREAT escalated-need exemption is designed but rides with the
  held flight step (rpg-designer 2026-10-27 ruling (ii)), not here.
- Pruning finished records from `StrategicComponent.projects`.

## Acceptance Criteria
1. With a dead record of the kind first in dict order and a SUSPENDED one later, the winner resumes the
   SUSPENDED one; no project is created; `CapacityEnforcementPhase` evicts nothing for it.
2. The dead-only rule matches the decision recorded in the ticket, with a test.
3. Bible 04, divergences 2.77/2.137 plus the new entry, and the parity ledger agree with the code.
4. Paired run reported with the per-kind and extinction lines; any STOP goes to rpg-planner before landing.
5. Mechanism registry check run; `strategic_intelligence_core` entry reviewed.

## Related Tickets
- TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START (2.77)
- TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY (2.137)
- HUNGER step A (`rpg-hunger-retreat-step-a`), which found it

## Related Docs
- docs/mechanics/04_strategic_cognition.md (capacity paragraph)
- docs/guidelines/intentional_divergences.md §2.77, §2.137

## Related Stored Artifacts
- none

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (~1610-1612, ~1773)
- src/core/strategic.py (is_live_project, has_project_capacity, live_projects_in_the_trim)
- src/engine/pipeline_phases/capacity_enforcement.py

## Assumptions / Open Questions
- Not M1-blocking unless it shows in the M1 gate (rpg-designer). Dispatch after step A lands.
- **rpg-designer ruling, 2026-10-28 (decisions 1-3, binding):**
  - Decision 2: NO. "Existing" means a LIVE record of the kind; dead records (COMPLETED/ABANDONED) take no part in
    the lookup or the gate (2.77 "finished records never count"). At a full cap only `escalated_need_wins` (2.137)
    admits a new project.
  - Lookup, stated as behaviour (dict order plays no part anywhere): (1) the current project is of the kind ->
    continue it (no new project, no switch); (2) else the newest live record of the kind by `created_tick`, a
    non-current ACTIVE over SUSPENDED if that state can exist (investigator says whether it can) -> resume it;
    (3) else no live record -> a new project through the cap gate.
  - Decision 3, report BEFORE code: kind-only matching can resume a suspended record whose TARGET differs from the
    winning candidate's (combat_engage on hostile X vs candidate Y; a different harvest node). Designer lean: resume
    only when the live record's target matches the candidate's (`target_entity_id` / `target_id`); a different target
    is a new project through the gate (refused at a full cap; the tactical pass still handles the adjacent fight).
    Count on the confirm seeds (frontier s42 to t531, s43 to t326) how often the resumed record's target differs; if
    common, the numbers go to rpg-designer before the plan is approved.
  - No owner row, on condition: the paired step measures it, and any STOP goes to the owner as step A's did.
- **rpg-designer decision-3 ruling, 2026-10-28 (binding, relayed by rpg-planner, word for word):**
  1. Match = the typed target is equal: target_entity_id when either side has one, else target_id. Both None is a match, so kinds with no typed target stay kind-only. The investigation lists, per kind in your counts (combat_engage, resolve_blocker, guild, harvesting), which key the scorer sets and which key the record's objective carries. A kind where the two sides use different keys comes back to rpg-designer through me; don't guess.
  2. Live same-kind record, target matches: continue if current, else resume the newest such record (as ruled).
  3. Live same-kind record, target differs: SUPERSEDE, cap-neutral. The newest live record of the kind is ended, and the new project at the candidate's target is created in the same update; the live count is unchanged and the gate is not consulted. Only that one record is superseded; older duplicates are left to the existing trims. The ending must be typed: an existing terminal status plus a typed end reason if ProjectState has one, otherwise the plan proposes the smallest typed field. Never a reason string.
  4. No live record of the kind: a new project through the gate (decision 2).
  5. Switching is unchanged: evaluate_project_switch decides whether the superseding project becomes current.
  Records: the divergence (Bug Fix) states rules 1-5. Bible 04 l.229: "one live project per kind is resumed or superseded by target" (diff to rpg-designer). The paired Measured section reports supersede counts by kind next to the refusal counts. No owner row; a STOP goes to the owner.
- **rpg-designer amendment and conditions, 2026-10-28 (binding, relayed by rpg-planner, word for word):**
  - "Rule 3 (amended): supersede happens only when evaluate_project_switch returns an update for the candidate; the newest live same-kind record is ended (ABANDONED, ended_by SUPERSEDED_BY_TARGET) and the candidate is created and made current in that same update. If the switch loses, nothing changes this tick, whether the record is current or not. Rule 5: supersede is the commit to the new target; a candidate that loses the switch ends nothing and creates nothing."
  - The matching-target direct resume (outside the switch check) is existing behaviour, NOT endorsed.
  - ProjectState.ended_by (Optional[ProjectEnd], one member SUPERSEDED_BY_TARGET, set only together with ABANDONED) approved. Conditions: (1) typed round-trip test through the canonical dict and through checkpoint save/restore, with ended_by set and None, plus a hash-neutral check (a state with no superseded project fingerprints byte-identically to before the field existed); (2) invariant test: ended_by set implies status ABANDONED, and nothing else ever writes ended_by; (3) wherever a read model or debug view shows a project's status it also shows ended_by; if no project read model exists, say so here and do not build one. No link field to the superseding project.
  - Tests: (i) a different-target candidate that loses the switch leaves the live record unchanged and creates no project; (ii) a winning one ends exactly one record and creates one, with the live count unchanged.
  - The mapped-kind question (ADVENTURE_ROUTE, SOCIAL_CONTRACT, REGION_STABILIZATION, OCCUPATION_CHANGE candidates never match a stored record because the project kind differs from the candidate GoalKind) is ticketed separately by rpg-planner and does not ride with this ticket.
- **Records required:** new divergence entry or amendment of 2.77 (rationale Bug Fix); Bible 04 ~l.229 sentence
  rewritten (diff to rpg-designer, who OKs or drafts); parity entry.
- **Measured report must list per-kind capacity-refusal counts, base vs new** (below-onset hunger/sleep,
  combat_engage, harvest at a full cap are now refused where base admitted them: the behaviour shift to watch).

## Implementation Notes
- Lookup (`same_kind_record`, `src/core/strategic.py`): the current project when it is of the kind, else the newest live record by `created_tick` (ACTIVE before SUSPENDED, tie to the larger id). COMPLETED and ABANDONED records and storage order play no part. Kind identity is class-strict (`same_kind`): a GoalKind never matches a ProjectKind that shares its value.
- Target match (`project_target_matches`): `target_entity_id` when either side has one, else `target_id`.
- Matching target: continue the current project; resume a SUSPENDED record (existing behaviour); make an ACTIVE non-current record current; when another live project is current the record is the candidate of the existing `evaluate_project_switch` call (designer ruling b), a won switch being a fresh commitment (live utility, t+10 lock).
- Different target: the live record is superseded (`supersede_record`, the only writer of `ProjectState.ended_by`) only when the switch returns an update; cap-neutral.
- No live record: the capacity gate (unchanged `not existing` condition).
- Docs: Bible ch04 section 4, divergence 2.143 (Measured items 1 to 7), parity ledger STRAT-289.

## Test Summary
- `tests/unit/strategic/test_project_lookup_live_record_first.py` (about 33 tests): lookup order, target match, resume past a dead first record, continue, gate and escalated need, supersede win and lose, orphan switch win and lose with the lock and score, class-strict match, enum class through every rebuild path, hash neutrality, single-writer scan, cognition graph.
- `tests/unit/strategic`, `tests/unit/core`, `tests/unit/ai`: 872 passed. Wide run on the code: 4 known order-dependent fails that pass alone, 8197 passed. `tests/unit/tools`: see closure.
- Paired run (base d914bace7 vs c32db1a41, 3 worlds, seeds 42 to 46, 5000 ticks): no drift in any world; crowded scout extinction STOP and crowded starvation 1 to 2, both disclosed in 2.143 and accepted by the designer (shifted trajectory, trace in Measured item 7).

## Files Changed
src/core/strategic.py, src/core/state.py, src/systems/strategic_systems/intelligence.py, src/systems/strategic_systems/cognition_export.py, tests/unit/strategic/test_project_lookup_live_record_first.py, docs/mechanics/04_strategic_cognition.md, docs/guidelines/intentional_divergences.md (2.143), docs/parity_ledger/strategic_cognition.yaml (STRAT-289).

## Completion Summary
A winning goal now continues, resumes or supersedes the entity's live project of its kind by target, chosen from the current project then the newest live record; a dead first record of the kind no longer blocks the live sibling or skips the capacity gate. Disclosed shifts: capacity-gate refusals rise (intended, base defect gone); escalated hunger and fatigue orphans lose the project switch at a rate comparable to base (a gap that already exists in base; follow-up TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH); crowded scout 29 returns to its pre-step-A count; crowded starvation pair at seed 46 is a shifted trajectory, with worker 1's non-eating untraced at the execution layer. Sleep-debt collapses and time at hunger of 95 or more were not measured (no ledger counter).
