---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT
phase: done
date: 2026-10-05
tags: [strategy, cognition]
---

# TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-A-MOVING-COUNTERPARTY-AS-A-FIXED-POINT

## Title
`SocialContractScorer` targets a cooperation counterparty by entity id and freezes that entity's
position at goal-win time — the second and last live instance of the entity-as-fixed-point shape

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by `rpg-implementer` during the Scope 4 scorer audit of
`TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES`, and filed
separately on the planner's ruling rather than folded in — a different scorer, different semantics,
and different termination conditions.

`SocialContractScorer` (`src/ai/goals/social_contract_scorer.py:68-70`) sets
`target_id=str(contract.source_id)` — the **entity** id of the cooperation counterparty — and
`target_pos=source_entity.navigation.position`, that entity's position read **once**, at the moment
the goal wins.

**This is not an oversight, and the ticket should not be written as if it were.** The scorer's own
comment at `:55-59` ("Design Decision #8") states the constraint explicitly and documents the
position capture as the deliberate workaround for it:

> the counterparty's real position, so the materialized objective is tactically resolvable
> (`TacticalDecisionSystem._resolve_target_position()` only resolves int-castable targets against
> `state.resource_nodes`/`state.buildings`, never `state.entities` — a stringified entity id alone,
> as `accept_contract()`'s ORIGINAL `ObjectiveState` used, was never resolvable).

So the author knew the pursuit path cannot resolve an entity and compensated by capturing a
coordinate. That made the objective *resolvable*; it did not make it *correct for a target that
moves*. The counterparty walks away and the entity navigates to where they stood.

**Why it is worth a ticket despite the workaround being deliberate.** Cooperation contracts are live
in corpus runs, so this is not dormant. And the workaround is strictly worse than the mechanism that
`TCK-20261002` is now adding: a typed `target_entity_id` on `ObjectiveState` makes the entity target
resolvable *as an entity*, which is the thing Design Decision #8 wanted and could not have.

**The scorer audit that bounds this.** All `target_id=` sites in `src/ai/goals/` were swept. Exactly
two put an entity id there: `CombatEngageScorer` (owned by `TCK-20261002`) and this one.
`CombatRetreatScorer` uses `"town_center"`; every other site is a resource-node, building, region or
blocker id, or an `"adventure:<family>"` string. **This is a complete sweep with a negative result,
not a spot check** — there is no third case to find in that package.

**Premise corrected by measurement (2026-10-06).** The defect is not a moving counterparty frozen at a point. Every contract the cooperation domain creates (`domains/cooperation/services.py:233`, REQUEST_HELP / HIRE_SUPPORT) has `source_id` equal to the requesting entity and is added only to that entity, so the scorer's target (`contract.source_id`) is the **holder itself**: both contract projects the four corpus worlds produced were self-targeted, and the "captured position" was the entity's own old position. Ruled by `rpg-feature-planning`: option A (no rule ratification needed); Scope 1 below (typed `target_entity_id`) is **dropped** because for a self-sourced holder it would make the entity target itself and `entity_target_outcome` would never end it. See `investigation.md`.

## Scope
1. Move `SocialContractScorer`'s counterparty target onto the typed `target_entity_id` that
   `TCK-20261002` adds to `ObjectiveState`, so the pursuit path resolves the counterparty's current
   position instead of a captured coordinate.
2. Retire Design Decision #8's position-capture workaround **and its comment**, replacing the comment
   with one that records why the capture existed and what superseded it. Do not delete the reasoning;
   a future reader needs to know the capture was deliberate.
3. Give the social-contract objective its own termination conditions. They are **not** the combat
   ones: a cooperation contract's objective should terminate on the contract being fulfilled,
   cancelled or expired, and on the counterparty becoming unreachable — not on "target dead", which
   is the combat case. Enumerate them against the contract lifecycle in `investigation.md` before
   implementing, and if the contract lifecycle has no cancellation or expiry concept, say so rather
   than inventing one.
4. Measure, on a corpus world where cooperation contracts actually form, how often the captured point
   differs from the counterparty's live position, and how often a social-contract objective is still
   `ACTIVE` after its contract is no longer current. Report both whatever they are — including if
   they turn out to be near zero.

## Out of Scope
- Adding `target_entity_id` to `ObjectiveState`. `TCK-20261002` owns that; this ticket consumes it.
  **This ticket is sequenced after `TCK-20261002` lands** and must not race it.
- `CombatEngageScorer` and the combat objective's termination — `TCK-20261002`.
- The contract scoring, the reduction rule, or the tie-break at `:40-44`. Determinism-sensitive and
  not what this is about.
- Changing when contracts are offered or accepted. Only how an accepted contract's objective resolves
  its target.
- The lazy-import pattern at `:46-53`. Documented and deliberate; leave it.

## Acceptance Criteria
- [ ] **Dropped by the ruling (Scope 1):** a social-contract objective navigates toward the counterparty's current position through the typed `target_entity_id`. Not done, on purpose: it would turn the self-target artefact into a permanent hold. Nothing in `src` produces a holder that is not the contract's source today.
- [ ] **Not done, kept on purpose:** Design Decision #8's position-capture workaround is not removed; it still applies to the other holder (the recruit), and the reason it exists and why it stays is recorded in `_is_active_with_a_counterparty`'s docstring.
- [x] Every termination condition has a test, justified against the contract lifecycle rather than copied from the combat case (investigation section 3): FULFILLED, each other status (FAILED, BETRAYED, EXPIRED, CANCELLED, OFFERED, ACCEPTED, COUNTERED), the contract gone, and a project that serves no contract left alone; closed through the real `evaluate_strategic_intent`, and scheduled by the work queue.
- [x] Scope 4's two measurements are reported with world, seed and ticks, before and after (investigation sections 2 and 6): before, 2 contract projects, both self-targeted, captured != live on 18 of 40 project-ticks and ACTIVE after the contract was not ACTIVE on 16 of 40; after, 0 projects, so both are 0 **because the projects no longer form**, not because termination was exercised on the corpus.
- [x] Determinism: on a PR, CI runs the non-slow determinism and replay tests (`tests/integration` including `tests/integration/kernel`, `tests/unit/kernel`, `tests/unit/replay`, and `tests/certification` when its paths changed); the slow ones (`test_long_run_determinism.py`, the 5k regression, the milestone-B gate) run only after a merge to `main`, nightly or on manual dispatch. So the sweep was also run **locally** before asking the owner to merge: `tests/integration/kernel`, `test_lineage_dispatch_deterministic_kernel_tick.py`, `tests/unit/kernel`, `tests/unit/replay`, `test_dirty_refresh.py`, `tests/certification`, slow-marked tests included (the long-run determinism test passes): 279 passed, 1 failed. The failure, `tests/integration/kernel/test_milestone_b_closure.py::test_milestone_b_operational_gate` (slow-marked), fails the same way run alone on a clean `origin/main` export (5 of 5 runs: expects DEGRADED, gets SURVIVAL; the test fakes the clock at 2 ms per `perf_counter_ns` call and assumes about 63 calls per tick), so it is pre-existing and unrelated. A broader scoped sweep gave 1092 passed, 1 failed (`tests/regression/test_behavioral_5k.py`, red on clean `origin/main` with identical numbers, tracked by Lane B). No recorded-hash fixture moved because of this change.
- [x] The `accept_contract()` path was checked: it has no production caller, so it constructs no objectives in production; negative result, nothing to fix.

## Related Tickets
- `TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES` — **the
  prerequisite.** Adds the typed `target_entity_id` this ticket consumes; its Scope 4 audit found
  this case. Sequence after it.
- `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` — the same family (a pursuit target
  that is not where the entity should go), different mechanism.
- `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG` — introduced the `target_position` fallback that
  Design Decision #8 was written around; its own cases must keep working.
- `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` (done, #291) — changed which
  objective kinds are materialized, so any pre-#291 measurement of this path is suspect.

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` — goal hierarchy and objective lifecycle
- `docs/engine/contracts/tactical_contract.md` §7 — objective target resolution

## Related Stored Artifacts
_(none yet — Scope 4's measurement will produce the first)_

## Related Code Areas
- `src/ai/goals/social_contract_scorer.py:55-70` — the capture and the decision comment
- `src/core/strategic.py::ObjectiveState` — where `target_entity_id` arrives from `TCK-20261002`
- `src/engine/tactical.py::_resolve_target_position` — the path that could not resolve an entity

## Assumptions / Open Questions
- **Whether the contract lifecycle has cancellation and expiry at all is open** and is Scope 3's
  first question. If it does not, the honest termination set may be smaller than the combat case's,
  and that is a finding rather than a gap to fill by inventing a lifecycle.
- Line numbers are at `9bf34765b`. `TCK-20261002` edits `src/core/strategic.py` and
  `src/engine/tactical.py`, so **re-derive them** at the commit this ticket starts from.
- How often cooperation contracts form in corpus runs is not quantified here. If Scope 4 finds the
  path is rare rather than live, the priority should be revisited rather than the ticket forced
  through — report it to the planner.

## Implementation Notes
Ruled option A (`rpg-feature-planning`, 2026-10-06). (1) `SocialContractGoalScorer` ignores a contract the holder itself sourced, through `_is_active_with_a_counterparty`, which replaces the old status check so `score()` does not grow; its docstring cites `domains/cooperation/services.py:233` as the only producer. (2) `entity_target_objective.py` gains `contract_project_id` / `contract_id_of_project` (the evaluator builds the project id through the first, so the pair cannot drift), `contract_objective_outcome` and the combined `objective_outcome`; `close_entity_target_project` (the name predates the contract case and is kept because the mechanism registry cites it) and the work queue both call `objective_outcome`, each by replacing one line, so neither ceilinged function grew. FULFILLED completes the project; any other status, or a missing contract, abandons it.

Findings, not fixed (planner): nothing in `src` issues RECRUIT, so `execute_recruit`'s two-party mirror is a dead path; the scorer won with utility > 0 195 times across the four worlds but only 2 projects materialized (not investigated). The question of whether a requester should walk to the helper or the helper to the requester went to the world-rules owner, non-blocking. **Owner ruling 2026-10-06 (via world-rule-catalog-design): in a recruitment contract the helper joins the task. The contract is social, never spatial; it never creates a walk-to-a-person objective. The helper takes on the requester's objective. It binds when RECRUIT is wired. The interim fix here is consistent with it.**

Registry: after review the planner (registry owner) authorised adding `entity_target_objective.py::objective_outcome` and `::contract_objective_outcome` to `goal_hierarchy.implemented_by` (the dispatch the work queue and the evaluator now go through); `verified` left as is; `strategic_intelligence_core` needs nothing. All generated views were regenerated (none changed) and `tests/unit/tools` passes (529). Noted, not mine to fix: no mechanism binds `SocialContractGoalScorer` or `work_queue.py` (the planner's separate item).

Fix found by the gates: `contract_project_id` is typed `object`, because the evaluator reads the id from untyped goal metadata and a `str` parameter was a new mypy error.

## Test Summary
`tests/unit/strategic/test_contract_objective.py` 31 passed; with the scorer guard removed 3 fail, with the contract predicate disabled 13 fail, with the work queue reverted to entity-only 1 fails; the existing `test_entity_target_objective.py` still passes (55 together). Scoped sweep: 1092 passed, 1 failed (the pre-existing 5k regression, identical on `origin/main`). Code-health gates in a scratch venv at the `uv.lock` versions: ratchet OK (0 new, 0 worse), package registry 0 problems, mypy-baseline filter 10 unrelated lines none in a changed file (one new error was found and fixed). CI is the first run in the real environment.

## Files Changed
`src/ai/goals/social_contract_scorer.py`, `src/systems/strategic_systems/entity_target_objective.py`, `src/systems/strategic_systems/intelligence.py`, `src/systems/strategic_systems/work_queue.py`, `tests/unit/strategic/test_contract_objective.py`, `docs/mechanics/04_strategic_cognition.md`, `docs/guidelines/intentional_divergences.md` (2.72), `docs/parity_ledger/strategic_cognition.yaml` (STRAT-276), `registries/mechanisms.yaml` (two functions added to `goal_hierarchy.implemented_by`, authorised by the registry owner; `verified` untouched).

## Completion Summary
A contract objective is no longer created for the contract's own source, and a project that serves a contract now ends when its contract is no longer ACTIVE. Known gaps: the corpus numbers after the change are 0 because the two self-targeted projects no longer form, so termination is exercised only by constructed cases; Scope 1 and the removal of Design Decision #8 were dropped or kept by the ruling; the other holder (the recruit) has no production producer and its semantics are with the world-rules owner; the 195-versus-2 gap is not investigated; two tests are red on `main` independently of this change (the 5k regression, tracked by Lane B, and the slow milestone-B governor gate).
