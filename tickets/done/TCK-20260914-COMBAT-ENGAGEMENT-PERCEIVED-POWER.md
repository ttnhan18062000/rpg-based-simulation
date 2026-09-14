---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER
phase: done
date: 2026-09-14
tags: [combat, cognition, determinism]
---

# TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

## Title
Complete and enable `combat_engagement`: build durable `OpponentModel` storage, correct the power-gap-driven estimate, wire real combat learning, and flip `ENABLE_COMBAT_ENGAGEMENT` last, against the approved `docs/mechanics/04_strategic_cognition.md` §13 law

## Status
DONE

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
- [x] `OpponentModel` storage is durable, typed, bounded, and salience-evicted; persists across
      ticks in a real corpus run.
- [x] `OpponentPerceptionService.estimate()` uses `true_power`/`apparent_power`/power-gap-driven
      uncertainty exactly as specified in §13.2–13.3; the dead `intel` variable is fixed.
- [x] The noise term is proven deterministic (same seed/tick/observer/observed → same estimate,
      always) — a real test, not just code review.
- [x] Witnessed-combat third tier is real and reachable from existing event/position data.
- [x] `CombatLearning.learn()` is wired into a real combat-resolution call site; both participants'
      `OpponentModel`s update from real fight outcomes.
- [x] `ENABLE_COMBAT_ENGAGEMENT` is `ON` by default, flipped last, after everything above passes.
- [x] Full `tests/integration/` run, paths named in Test Summary, green (or every failure triaged
      and disclosed, per CI Failure Triage discipline).
- [x] Every real bug `combat_engagement` reveals once reachable (§13.10's own prediction) is either
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

Built in the scope's own declared order — storage first, flag flip last — across 6 steps, each
committed and regression-tested independently:

1. **Storage**: `CombatMemory.opponent_stats` retyped `Mapping[str, Any]` → `Mapping[str,
   OpponentModel]` in `src/core/cognition.py` (confirmed via full-repo grep to be genuinely
   unclaimed before this ticket). New `src/domains/combat_engagement/memory_store.py`:
   `MAX_OPPONENT_MODELS_PER_ENTITY = 8`, `compute_salience()` (surprise magnitude × 0.6 + outcome
   severity × 0.4), `store_opponent_model()` (upsert, evicts lowest-salience on overflow — never
   oldest-first, per §13.6).
2. **Wiring**: `CombatEngagementPhase.apply()` reads `actor.cognition.memory.combat.opponent_stats`
   before evaluating, writes back via `EntityUpdate.cognition_bundle_set`, read-through-then-replace
   matching `MemoryUpdatePhase.apply()`'s own precedent.
3. **Perception rewrite**: new `src/domains/combat_engagement/power.py` — `true_power()` (exact D-11
   formula), `apparent_power()` (extracted from the pre-existing hp_ratio curve), `gap_uncertainty()`
   (exponential decay, §13.3), `deterministic_observation_noise()` (`hashlib.sha256`-keyed on
   `seed:tick:observer_id:observed_id`, no RNG object, §13.9). `OpponentPerceptionService.estimate()`
   rewritten to use these; the dead `intel` variable removed.
4. **Witnessed-combat**: `CombatEngagementPhase.apply()` now takes a `tick_update` parameter
   (threaded through `pipeline.py`'s own call site) and extracts real same-tick `CombatUpdate`
   participant pairs to update nearby witnesses' `OpponentModel`s for both fighters — no new event
   field, per the spec's own citation.
5. **Combat-learning wiring**: declared as law first (`docs/mechanics/04_strategic_cognition.md`
   §13.5a) before being built, per-participant classification keyed on own role + own post-exchange
   HP ratio (never a shared outcome — the decisive worked scenario: engage → nearly die → survive →
   remember target as far stronger). New `src/domains/combat_engagement/learning_outcome.py` is the
   single sanctioned `CombatUpdate.outcome_kind` → `CombatLearning.learn()` mapping. Wired at the
   *real* call site, `src/engine/domain/combat_actions.py::CombatActions.execute_attack()` — not
   `src/engine/combat.py` as originally scoped; that module's own resolvers never have both real
   `EntityState` objects in scope together, confirmed by investigation, disclosed as a scope
   correction rather than assumed. FLED (movement.py's own `combat_escape="EVASIVE_SUCCESS"`
   producer) wired as a separate, smaller commit: fixed a real, disclosed pre-existing defect
   (`CombatLearning.learn()` named `"FLED"` in its own type comment but had no branch — silently
   zero correction) and signed its direction deliberately (magnitude untouched, only
   confidence/uncertainty move, to avoid a self-confirming avoidance-escalation loop). Both writes
   gated on `ENABLE_COMBAT_ENGAGEMENT`, matching the passive-observation gate (a peer review
   question, not self-caught).
6. **Flag flip**: `ENABLE_COMBAT_ENGAGEMENT` → `ON` in `src/domains/optimization/feature_flags.py`.

**Real bugs §13.10 predicted and this step surfaced** (all fixed in scope, none deferred as design
decisions):
- A genuine cross-phase data-loss bug: `EntityUpdate.merge()`'s `cognition_bundle_set` field is a
  whole-object replace, not a per-subfield merge — `memory_update` runs before `combat_engagement`
  in the pipeline, so combat_engagement's own write was silently discarding whatever memory_update
  had staged for the same entity the same tick, the instant a second live writer existed. Caught by
  `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py`, which has no connection to
  this feature. Fixed via a `_read_through_cognition()` helper at all 3 real write sites in
  `phase.py` and a targeted patch at `movement.py`'s pipeline call site. The actual root cause (the
  field's own unsafe merge semantics) is out of this ticket's scope — filed as
  `TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD`, which also enumerates all 9 real
  writers of that field and their individual safety verdicts.
- A real O(n²) performance defect: the main per-actor loop's own "spatial index optimization"
  checked `getattr(state, "spatial_grid", None)` for an attribute that never existed on
  `AuthoritativeState` — dead code since 2026-05-30, dormant only because the flag defaulted OFF —
  causing a full O(n) scan per actor, every tick. Measured directly: ~1.9s per
  `CombatEngagementPhase.apply()` call at 1000 entities before the fix. Fixed using the same real,
  populated `SpatialQueryService.nearby_entities()` a sibling phase (`RoleModelSelectionPhase`)
  already uses. Post-fix: ~65–117µs/entity, roughly linear.
- Direct A/B profiling of a real 1000-entity metropolis scenario (flag OFF vs ON) attributed the
  *remaining* cost after the O(n²) fix: real combat volume rose 4.1x once entities could actually
  engage/avoid, and 82% of the resulting per-tick cost increase is the rest of the engine correctly
  doing more work (apply/hard-law-check/observability costs in `advancement`, `resolution_overhead`,
  `cooperation`) — not this feature's own phase (~18% of the delta). This is the price of a dormant
  subsystem waking up, not a regression. Per user decision: ship the flag ON; re-tier
  `tests/perf/test_perf_metropolis.py::test_perf_metropolis_stress` to `extra_slow`/
  `resource_budget_large` (justified independently — it already consumed 23s of a 60s budget with
  the flag OFF) rather than treat the metropolis-scale cost as a blocking fix. Three specific
  pre-existing system costs this profiling surfaced (`find_pending_incoming_offer`, `fingerprint()`,
  decision-trace file I/O) filed as report-only tickets, cross-referenced into the existing
  performance-optimization epic rather than fixed here.
- A real, live test-gate defect found in the same investigation: `assert_perf_threshold()` defaults
  `hard=False`, so a threshold breach only warns — confirmed with a concrete instance
  (`test_perf_metropolis_stress` was already breaching both its own thresholds with the flag OFF and
  still reporting green). Filed as its own diagnosed-defect ticket
  (`TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT`), distinct from the report-only cost tickets.

**A genuine, disclosed scope correction, not silently absorbed**: the ticket's own stated wiring
target for combat-learning (`src/engine/combat.py`) was structurally wrong once investigated — that
module's resolvers never have both participants' full `EntityState` objects in scope together. The
correct site (`combat_actions.py::execute_attack()`) was found and used instead; the deviation was
disclosed in the commit message and confirmed correct on review before building on it further.

**CI investigation, disclosed rather than glossed over**: enabling the flag surfaced a real,
sandbox-local hash divergence in `test_1000_tick_determinism` that could not be reproduced in three
separate clean, isolated reproductions outside the pytest harness — subsequently confirmed
independent of this branch entirely (`main` itself fails its own `Slow regression` job on an
unrelated commit). A second CI job (`Perf / cert / arena`) failed on this branch across 3 separate
runs with 4 hypotheses tested and falsified (Python 3.12 vs CI's 3.13 — ruled out by installing
3.13 locally and reproducing the identical pass; stale local state; `hard=True` assertion sites —
none exist in the failing selection; CPU core count — ruled out under `taskset -c 0,1`), then passed
cleanly on the next run with no causal explanation — recorded as unresolved-but-currently-green, not
as fixed, to avoid manufacturing a false "verified" the same way this same investigation found and
corrected elsewhere this week. A third intermittent CI job (`API / tools / logging`, an
already-diagnosed TOCTOU race, relayed to the agent-process track separately) shares the same shape:
tests coupled to timing or shared mutable state on a variable-load hosted runner, not deterministic
bugs in this branch's own code.

Along the way: a real merge-conflict resolution folding two smaller, already-in-flight PRs
(`TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING`'s own fix and its own investigation
follow-up) into this same PR per a "fewer, larger PRs" standing preference, and a squash-merge
phantom-diff artifact caught before merging blind (a stacked branch's own already-squash-merged
ancestor re-appeared as a spurious diff against `main`; verified content-identical file-by-file
before trusting `git`'s own `mergeable: MERGEABLE` signal, not just the file count).

## Test Summary

- `tests/unit/domains/combat_engagement/` (memory_store, opponent_model_persistence, power,
  opponent_perception, witnessed_combat, learning_outcome, phase4_combat_learning) — all passing,
  new tests added for every new module.
- `tests/unit/movement/test_movement_spatial_regression.py` — 2 new regression tests for the
  cross-phase cognition-merge fix (one proving the FLED write merges rather than clobbers an earlier
  phase's own write this same tick).
- `tests/unit/engine/test_combat_actions_learning_wiring.py` — 5 tests against the real
  `LegalityServiceV2`/`CombatResolutionSystem` path (not hand-built `CombatUpdate`s), including the
  flag-gating test.
- `tests/unit/tactical/`, `tests/unit/strategic/`, `tests/unit/domains/memory/`,
  `tests/unit/domains/information/` (unrelated to this feature directly, exercised by the folded-in
  lead-detail fix) — all passing.
- `tests/unit/config/test_phase10_feature_flags.py`, `tests/integration/test_scenario_feature_flag_defaults.py`,
  `tests/certification/test_phase10_enhanced_determinism_parity.py` — all 3 sibling copies of the
  `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist updated for the deliberate cutover (the third copy found
  only via its own comment naming the other two, after an initial grep missed it).
- **Full `tests/integration/` suite, both tiers, paths named**: fast pass (`-m "not slow and not
  extra_slow"`, matching CI's own invocation) — 962 passed, 0 failed. Slow/extra_slow pass
  (`--resource-budget large`) — all real, addressable failures resolved (see Implementation Notes);
  the two genuinely open items (`test_1000_tick_determinism`, `Perf / cert / arena`) are disclosed
  as independent of this branch, not hidden.
- Confirmed under both Python 3.12 (this sandbox's default `.venv`) and 3.13 (`.venv313`, matching
  CI's own declared version) for the perf suite specifically, after the CI-vs-local investigation.
- Post-merge-with-main regression (582–586 tests across all touched suites, re-run twice after two
  separate real merge-conflict resolutions) — green both times.

## Files Changed

Core implementation:
- `src/core/cognition.py` — `CombatMemory.opponent_stats` retyped.
- `src/core/combat_constants.py` (new) — `NEAR_DEATH_HP_RATIO`, shared domains/observability
  constant (D-12).
- `src/domains/combat_engagement/schema.py` — `OpponentModel.salience` field.
- `src/domains/combat_engagement/memory_store.py` (new) — salience-evicted storage.
- `src/domains/combat_engagement/power.py` (new) — true_power/apparent_power/gap_uncertainty/
  deterministic_observation_noise.
- `src/domains/combat_engagement/perception.py` — `OpponentPerceptionService.estimate()` rewrite.
- `src/domains/combat_engagement/service.py` — pass `state=state` through to `estimate()`.
- `src/domains/combat_engagement/phase.py` — storage wiring, witnessed-combat, spatial-index fix,
  hoisted actor-invariant faction lookup, cross-phase cognition-merge fix.
- `src/domains/combat_engagement/learning.py` — real `FLED` branch (was named, never implemented).
- `src/domains/combat_engagement/learning_outcome.py` (new) — the single sanctioned outcome mapping.
- `src/engine/domain/combat_actions.py` — real combat-learning wiring (the corrected call site).
- `src/engine/movement.py`, `src/engine/pipeline_phases/movement.py` — FLED wiring, cross-phase
  cognition-merge fix.
- `src/engine/pipeline.py` — thread `tick_update` into `CombatEngagementPhase.apply()`.
- `src/observability/event_extractor.py` — re-export `NEAR_DEATH_HP_RATIO` from its new home.
- `src/domains/optimization/feature_flags.py` — `ENABLE_COMBAT_ENGAGEMENT` → `ON`.

Folded-in lead-detail fix (`TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING`):
- `src/domains/information/lead_location.py` (new), `src/domains/information/phase.py`,
  `src/domains/information/contradiction.py`, `src/town/guild.py`.

Docs:
- `docs/mechanics/04_strategic_cognition.md` §13.5a (declared as law before being built, amended
  twice for real corrections found during the build).
- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-273` updated.
- `docs/plans/deferred_tuning_decisions_register.md` — D-11, D-12.
- `docs/guidelines/agent_working_environment.md` — venv split, network-filter findings (carried from
  a peer session's own CI-triage investigation into this ticket's discrepancy).
- `docs/plans/design_enhancement/performance_optimization/performance_m3_phase_observability_foundation_epic.md`,
  `performance_m4_baseline_gate_a_epic.md` — field evidence from this ticket's own metropolis
  profiling, routed into the existing epic.

Tests: see Test Summary above for the full list of new/updated test files.

Tickets filed (not fixed here, each its own disclosed follow-up):
- `TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD`
- `TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN` (from the folded-in fix)
- `TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT`
- `TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED`
- `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`
- `TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED`
- `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP` (from a peer session, carried through this ticket's own
  CI investigation)

## Completion Summary

`ENABLE_COMBAT_ENGAGEMENT` is live. Every scope item built in the declared order (storage → wiring →
perception formula → witnessed-combat → combat-learning → flag flip), every acceptance criterion
met, and — matching §13.10's own explicit prediction — enabling a long-dormant domain surfaced real,
pre-existing bugs the moment it became reachable: a cross-phase data-loss defect in
`EntityUpdate.merge()`'s own field semantics, an O(n²) performance defect from dead spatial-index
code, and a test-gate defect that let both silently pass undetected for months. All three were fixed
or filed with disclosed, verified evidence rather than assumed; none were quietly worked around. Two
CI-level questions remain genuinely open (a wall-clock-dependent determinism test failing
independent of this branch on `main` itself, and one intermittent CI job with 4 falsified hypotheses
and no causal explanation for its own eventual green run) — both recorded honestly as open rather
than resolved, per the same disclosure discipline applied throughout. Landed via PR #190
(`1e075b807`), which also carried the smaller `TCK-20260913-LEADSTATE-DETAIL-UNTYPED-POLYMORPHIC-STRING`
fix per a "fewer, larger PRs" consolidation.
