---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER
phase: open
date: 2026-09-14
tags: [combat, cognition, determinism]
---

# TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

## Title
Complete and enable `combat_engagement`: build durable `OpponentModel` storage, correct the power-gap-driven estimate, wire real combat learning, and flip `ENABLE_COMBAT_ENGAGEMENT` last, against the approved `docs/mechanics/04_strategic_cognition.md` §13 law

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` found that nothing lets an entity learn
that one kind of creature is more dangerous than another from what it has actually seen/fought. The
user declared this real gameplay and directed: declare the Bible law first, build second. §13
("Perceived Power Assessment (Completing and Enabling Combat Engagement)") is now declared,
reviewed, and approved (peer-approved through several rounds, including a real 214-entity corpus
measurement that changed `true_power()`'s own formula before any code was written).

**This is not a new mechanism.** `src/domains/combat_engagement/` already implements most of the
pipeline (`OpponentPerceptionService`, `CombatLearning`, `EngagementRiskEvaluator`,
`CombatPostureSelector`) gated behind `ENABLE_COMBAT_ENGAGEMENT` (default OFF), never run in a real
corpus profile. This ticket completes the real, disclosed gaps §13 names and enables it — it does
not authorize a second, parallel implementation.

## Scope
In the order §13 and peer direction specify — **storage first, flag flip last**:

1. **Durable `OpponentModel` storage** (§13.6): a typed, bounded, per-observer `Dict[str,
   OpponentModel]` field. `CognitionModel.memory.combat` (`CombatMemory.opponent_stats: Mapping[str,
   Any]`, `src/core/cognition.py`) is an existing, unclaimed, unwritten, unread "Phase 4 Combat
   memory Shell" — confirmed via a full-repo grep with zero real usages anywhere — and is the
   correct home: it is not `src/domains/memory/`'s own memory-domain state (that domain's contract,
   `docs/simulation/domains/memory_contract.md`, never mentions `combat`/`opponent_stats`) and not
   `KnowledgeFact`, matching §13.6's own reasoning for a third, purpose-built type. Retype it from
   `Mapping[str, Any]` to `Mapping[str, OpponentModel]`. Salience-based eviction (surprise magnitude
   + outcome severity), not oldest-first — §13.6 states this is load-bearing for the feature's own
   three-phase acceptance scenario (engage → withdraw → engage-again-once-stronger), explicitly
   diverging from causal memory's own oldest-first policy (`src/domains/memory/phase.py:99-100`).
2. **Wire storage into the real per-tick call site**: `CombatEngagementPhase.apply()`
   (`src/domains/combat_engagement/phase.py`) currently calls
   `CombatEngagementDecisionService.evaluate(actor, target, state)` with no `memory=` argument
   (defaults to `None` everywhere, every tick — confirmed via grep, zero real callers ever pass a
   memory). Read `actor.cognition.memory.combat.opponent_stats.get(subject_key)` before evaluating,
   write the updated model back via `EntityUpdate.cognition_bundle_set`, following
   `MemoryUpdatePhase.apply()`'s own read-through-then-replace pattern exactly
   (`src/domains/memory/phase.py`).
3. **Correct `OpponentPerceptionService.estimate()`'s power/uncertainty formula** (§13.2–13.3):
   - Replace `target_lvl * 20.0` with `true_power(entity) = atk + def_stat * 0.5 + max_hp * 0.1`
     (evidence-backed, already fully specified in §13.2 and D-11 of
     `docs/plans/deferred_tuning_decisions_register.md` — do not re-derive, implement as specified).
   - Add `apparent_power()` as the condition-adjusted true-power identity (reuse the existing
     `hp_ratio` adjustment already in this file).
   - Replace the flat `if perception < 4: uncertainty += 0.15` threshold with power-gap-driven
     uncertainty: `gap = |true_power(observer) - apparent_power(observed)|`, PER-modulated per
     §13.3.
   - The observer's own side of the gap is `true_power(actor)`, never an estimate — a stated law
     (§13.2). Do not route this through `SelfCombatEstimateService` (that service's own
     condition-adjusted estimate remains correct and untouched for `EngagementRiskEvaluator`'s own
     `power_ratio` use — a different, already-correct concern; this ticket does not change it).
   - Fix the real, disclosed dead-code defect in the same change (§13.3): `attrs.intelligence` is
     read into `intel` and never used anywhere in `estimate()`.
4. **Determinism** (§13.9): the new power-gap-driven noise term must be a pure function of
   `(seed, tick, observer_id, observed_id)` via `hashlib.sha256(...).digest()`, following
   `_hash_point_in_bounds()`'s precedent (`src/worldassembly/resolver.py:947`) — never
   `DeterministicRNG` or any seeded-but-stateful generator.
5. **Witnessed-combat third tier** (§13.7): derive from existing combat-resolution `SimulationEvent`
   participant `entity_id`/`target_id`/`tick` fields cross-referenced with
   `state.entities[...].navigation.position` and the existing perception-radius neighbor scan — no
   new event field.
6. **Wire `CombatLearning.learn()` into the real combat resolution path**: confirmed zero real call
   sites today (`src/engine/combat.py`'s `CombatResolutionSystem.resolve_attack()`/
   `resolve_skill_usage()`/`resolve_multi_attack()` produce real `CombatUpdate.outcome_kind`
   values — `SURVIVE`/`KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`/`REJECTED` — with no mapping today to
   `CombatLearning.learn()`'s own `"WON_EASY"`/`"LOST"`/`"NEAR_DEATH"`/`"FLED"` vocabulary). Build the
   real outcome classification and wire it so both combat participants' `OpponentModel`s update from
   real fight results, per §13.5.
7. **Flip `ENABLE_COMBAT_ENGAGEMENT` to `ON` last** (`src/domains/optimization/feature_flags.py:31`),
   after everything above is built and tested — per explicit peer direction and §13.10's own
   expectation that this will surface real bugs the moment it becomes reachable, the same way
   `ENABLE_GUILD_QUEST_GENERATION` did (`TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION`).
8. Run the **full** `tests/integration/` suite (not a narrowed selection) once the flag is ON, with
   the covered paths explicitly named in the Test Summary, per peer's standing reminder from this
   same arc.

## Out of Scope
Everything §13.8/§13.10 names as a declared future seam, not built here:
- Deception (`apparent_power()` stays an identity w.r.t. deception).
- Observation-count-based confidence growth (only combat improves an estimate beyond observation,
  per §13.5).
- Hearsay and group-power tiers.
- Fallible self-assessment (`SelfCombatEstimateService` as a future gap-input substitute).
- Kind-generalized `subject_key` (per-individual only, per §13.6).
- Cross-episode entity-id-instability fix (a real, disclosed limitation per §13.6, not addressed).
- `INT`-weighted consideration strength (§13.4) — `bravery`'s existing weighting stands.
- Any change to `EngagementRiskEvaluator`'s existing bravery/personality_bias/risk_score formulas —
  already correct per §13.4, not touched.
- `CombatReassessmentService` — exists, has no real pipeline call site either; out of this ticket's
  scope unless directly blocking the flag flip (investigate only if it turns out to be load-bearing
  for a real acceptance scenario; otherwise leave as its own separate dormant-code finding).

## Acceptance Criteria
- [ ] `OpponentModel` storage is durable, typed, bounded, and salience-evicted; persists across
      ticks in a real corpus run.
- [ ] `OpponentPerceptionService.estimate()` uses `true_power`/`apparent_power`/power-gap-driven
      uncertainty exactly as specified in §13.2–13.3; the dead `intel` variable is fixed.
- [ ] The noise term is proven deterministic (same seed/tick/observer/observed → same estimate,
      always) — a real test, not just code review.
- [ ] Witnessed-combat third tier is real and reachable from existing event/position data.
- [ ] `CombatLearning.learn()` is wired into a real combat-resolution call site; both participants'
      `OpponentModel`s update from real fight outcomes.
- [ ] `ENABLE_COMBAT_ENGAGEMENT` is `ON` by default, flipped last, after everything above passes.
- [ ] Full `tests/integration/` run, paths named in Test Summary, green (or every failure triaged
      and disclosed, per CI Failure Triage discipline).
- [ ] Every real bug `combat_engagement` reveals once reachable (§13.10's own prediction) is either
      fixed in this ticket (if in scope) or filed as its own disclosed follow-up (if a design
      decision, brought to peer first).

## Related Tickets
- `TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` (the finding that started this; stays
  BLOCKED — this ticket is the build the user's decision authorized, not a reopening of that one)
- `TCK-20260913-HOTFIX-GUILDNEEDSCORER-HIJACKS-HOSTILE-ENTITY-NAVIGATION` (the precedent: flipping a
  long-dormant flag ON surfaced a real regression; expect the same class of finding here)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` §13 (the full law this ticket implements — read in
  full before touching code)
- `docs/simulation/domains/combat_engagement_contract.md` (existing technical contract)
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-273` (currently `missing`; update to
  `verified` on completion)
- `docs/plans/deferred_tuning_decisions_register.md` D-11 (`true_power()` coefficients — implement
  as specified, do not re-derive)
- `docs/simulation/domains/memory_contract.md` (confirms `cognition.memory.combat` is outside the
  memory domain's own write-scope)

## Related Stored Artifacts
`staging_artifacts/TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER/` (`plan.md`, `investigation.md`,
`test_plan.md`)

## Related Code Areas
- `src/core/cognition.py` (`CombatMemory.opponent_stats` — storage retype)
- `src/domains/combat_engagement/phase.py` (`CombatEngagementPhase.apply()` — read/write wiring)
- `src/domains/combat_engagement/perception.py` (`OpponentPerceptionService.estimate()` — formula
  rewrite, dead `intel` fix)
- `src/domains/combat_engagement/learning.py` (`CombatLearning.learn()` — real call site needed)
- `src/domains/combat_engagement/schema.py` (`OpponentModel` — salience field)
- `src/engine/combat.py` (`CombatResolutionSystem` — real `CombatUpdate.outcome_kind` values,
  the wiring point for real combat learning)
- `src/domains/optimization/feature_flags.py:31` (`ENABLE_COMBAT_ENGAGEMENT`)
- `src/worldassembly/resolver.py:947` (`_hash_point_in_bounds()`, determinism precedent)
- `src/domains/memory/phase.py` (`MemoryUpdatePhase.apply()`, read-through-then-replace precedent;
  also the oldest-first eviction precedent this ticket deliberately does not copy)

## Assumptions / Open Questions
- None currently — §13 resolved every open design question through peer review before this ticket
  was picked up. Any new one found during implementation goes to peer before being decided in code,
  per standing arc discipline.

## Implementation Notes
_(pending)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
