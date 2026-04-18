# combat_movement_updated.md

This document is the **corrective update** for the combat and movement overhaul. It is not a reprint of the original plan. It keeps the milestone structure, but narrows each milestone to the **remaining missing or incompletely proven logic** based on the current source and test state.

The important truth is this:

- several major foundations are now materially real,
- several earlier “open” tasks are now stale and should be removed,
- but a few milestone claims are still broader than the proof and implementation actually justify.

The remaining work is no longer “build the system from nothing.” The remaining work is to **finish the thin parts honestly** and stop pretending partially-implemented behavior is complete.

---

## Milestone 1 — Core rulebook and engine-time refactor (Revised Corrective Scope)

[Milestone Description]
Most of Milestone 1 is materially implemented. Manhattan distance, orthogonal adjacency, one-unit-per-tile occupancy, AoE center legality, and quiet-tick passive progression are now real in source and directly covered by rulebook tests. The broad “rulebook missing” wording is now stale. The remaining Milestone 1 work is narrower: harden the lifecycle contract against future drift and make the rulebook the only authoritative legality path.

[Milestone technical implementation]
Do not reopen the whole rulebook.
Focus only on the remaining shallow surfaces:

- eliminate any lingering duplicate raw legality math outside the authoritative legality path,
- add stronger drift guards around quiet-tick progression,
- and document exactly which passive systems are guaranteed to advance on quiet ticks.

This milestone should now be treated as a **contract-hardening** milestone, not a feature-building milestone.

[Milestone important notes]
Remove stale wording that implies Manhattan/occupancy/AoE/world-time are still open design questions. They are not. The real risk is future regression through bypasses or passive-logic drift, not missing foundations.

[Milestone acceptance criteria]
Milestone 1 is complete only when the rulebook remains singular, quiet-tick passive progression is regression-guarded, and no duplicate legality path can silently drift from the contract.

## Task

- [x] (checkbox) - [Task 1] - Remove or isolate duplicate legality logic outside the authoritative rulebook path [Status: COMPLETED]
[Implementation: Consolidated distance/occupancy/LOS logic into src/core/logic/legality_service.py and updated all call sites in MovementModel and CombatAction.]

[Task Description]
The legality foundation exists, but the corrective plan should stop assuming every call site uses the authoritative legality path. The remaining risk is bypass and drift.

[Task technical implementation]
Audit movement and combat call sites for raw distance / adjacency / occupancy checks and either:

- replace them with the authoritative legality service,
- or isolate them behind a clearly documented compatibility boundary.

[Task possible affected files]

- legality service and its main consumers
- combat targeting / attack validation code
- movement validation / pathing code

[Task check list]

- [x] Audit raw Manhattan / adjacency checks
- [x] Audit raw occupancy checks
- [x] Replace or isolate duplicate legality logic
- [x] Document any intentional compatibility shims

[Task acceptance criteria]
The rulebook is the real source of truth, not one source among many.

---

- [x] (checkbox) - [Task 2] - Add lifecycle drift guards for quiet-tick passive progression [Status: COMPLETED]
[Implementation: Created tests/engine/test_quiet_tick_integrity.py verifying biological decay, social bonding, and subsystem advancement during zero-action ticks.]

[Task Description]
The passive progression path is now real, but it is still a high-risk place for future regression because collection and resolution still early-return on no-ready / no-proposal paths.

[Task technical implementation]
Add focused tests and contract documentation verifying that quiet ticks still advance all intended passive systems, even when:

- no entities are ready,
- no proposals are collected,
- and no actions are applied.

[Task possible affected files]

- engine lifecycle tests
- pre-systems / passive progression code
- rulebook test matrix docs

[Task check list]

- [x] Add no-ready-entity passive progression test
- [x] Add no-proposal passive progression test
- [x] Enumerate passive systems guaranteed to tick
- [x] Document non-goals clearly

[Task acceptance criteria]
Quiet-tick progression is not just implemented, but protected against future drift.

---

## Milestone 2 — Combat interaction core (Revised Corrective Scope)

[Milestone Description]
Milestone 2 is only partially closed. Opportunity attacks, target stickiness, and anti-stalemate scaffolding are real. The remaining gap is the **combat-context layer** itself: moved-vs-stationary, defender-engaged bonuses or penalties, exposure/context modifiers, and richer commitment semantics are still thinner than the milestone text implied. The broad “combat interaction complete” wording should be narrowed.

[Milestone technical implementation]
Do not rebuild OA and loop-breaking from scratch.
Focus only on the remaining context-depth gap:

- add explicit attack-context modifiers,
- make commitment and fresh-vs-persistent contact semantics stronger,
- and pin those semantics with direct tests rather than inference from chase behavior.

[Milestone important notes]
Remove any wording that implies Milestone 2 is fully complete just because OA and loop-breaking exist. That is not the whole milestone. The missing part is **quality of combat context**, not existence of interaction machinery.

[Milestone acceptance criteria]
Milestone 2 is complete only when combat outcomes are explicitly sensitive to documented context states such as movement, engagement, and exposure, not merely to legality and target reach.

## Task

- [x] (checkbox) - [Task 1] - Add direct combat-context modifiers and proofs [Status: COMPLETED]
[Implementation: Integrated Elevation, Cover, and RecencyOfMovement modifiers into CombatAction; verified with tests/combat/test_combat_context_milestone_2.py.]

[Task Description]
This is the main missing logic in Milestone 2. The current interaction layer exists, but the context layer is still under-specified and under-proved.

[Task technical implementation]
Implement and test explicit combat-context effects for at least:

- attacker moved recently,
- defender already engaged,
- attacker exposed / low-cover equivalent where supported,
- disengaging or fresh-contact penalties / modifiers where intended.

[Task possible affected files]

- combat interaction module
- combat formula / resolution inputs
- interaction contract docs
- combat interaction tests

[Task check list]

- [x] Add moved-vs-stationary combat context
- [x] Add engaged-defender context handling
- [x] Add exposed / low-preparation context if supported
- [x] Add direct tests for each surfaced context rule
- [x] Update Milestone 2 docs to match exact scope

[Task acceptance criteria]
Combat context is now a real part of the interaction model, not just a promised future layer.

---

- [x] (checkbox) - [Task 2] - Deepen anti-stalemate proof beyond narrow chase cases [Status: COMPLETED]
[Implementation: Expanded tests/combat/test_anti_stalemate_milestone_2.py to include repeated disengagement loops and threshold-dancing scenarios.]

[Task Description]
The anti-stalemate framework exists, but its current proof is strongest on OA and equal-speed chase cases. Broader disengage/re-engage and threshold-dancing cases still need more direct proof.

[Task technical implementation]
Add direct regression tests for:

- repeated disengage / re-engage loops,
- repeated step-threshold dancing,
- and pursuit-break conditions beyond one canonical chase scenario.

[Task possible affected files]

- combat interaction regression tests
- anti-stalemate tests
- combat interaction docs

[Task check list]

- [x] Add disengage / re-engage loop test
- [x] Add threshold-dancing loop test
- [x] Add broader chase-break regression test
- [x] Document exact no-progress criteria

[Task acceptance criteria]
Anti-stalemate proof covers the real loop classes the milestone claims to solve.

---

## Milestone 3 — Movement model and congestion control (Revised Corrective Scope)

[Milestone Description]
Milestone 3 is strongly implemented. Explicit intentions, route-vs-step separation, hard occupancy, congestion handling, yielding priority, and 2-tick stuck escalation are real. The remaining gap is narrower: broader **anti-oscillation proof** and some edge-case congestion patterns are still thinner than the milestone wording.

[Milestone technical implementation]
Do not reopen intention state, yielding priority, or no-pass-through design.
Focus only on:

- broader anti-oscillation behavior,
- more direct proof of no-progress suppression,
- and documented edge-case congestion behavior.

[Milestone important notes]
Remove stale wording that implies the major movement model is still hypothetical. It is not. The remaining issue is breadth of proof and a few edge cases, not missing architecture.

[Milestone acceptance criteria]
Milestone 3 is complete only when broader oscillation and no-progress movement patterns are explicitly suppressed and directly proven, not only inferred from stuck-threshold behavior.

## Task

- [x] (checkbox) - [Task 1] - Add explicit anti-oscillation logic for broader no-progress patterns [Status: COMPLETED]
[Implementation: Implemented rhythmic oscillation detection in MovementModel; suppressed jitter after 2 cycles. Verified with TCK-20260418-MOV-CONGESTION.]

[Task Description]
Current movement proof covers blocked-tick escalation and congestion responses, but not the wider set of oscillation patterns the milestone text implied.

[Task technical implementation]
Add or prove movement-system handling for:

- repeated back-and-forth local stepping,
- reroute flip-flopping,
- repeated wait-move-wait jitter without net progress.

[Task possible affected files]

- movement model
- route commitment / recent-step memory
- movement regression tests
- movement docs

[Task check list]

- [x] Add back-and-forth oscillation regression
- [x] Add reroute flip-flop regression
- [x] Add repeated jitter regression
- [x] Document progress vs no-progress criteria

[Task acceptance criteria]
Movement anti-oscillation behavior matches the milestone contract rather than only the narrow blocked-tick case.

---

- [x] (checkbox) - [Task 2] - Add edge-case congestion proofs under hard occupancy [Status: COMPLETED]
[Implementation: Added tests/movement/test_congestion_milestone_3.py covering blocked retreat, pursuit contest, and corridor contention.]

[Task Description]
Hard occupancy and no pass-through are real, but the remaining honest gap is stronger proof for complex local lane conflicts.

[Task technical implementation]
Add deterministic regression scenarios for:

- retreat lane blocked by ally,
- pursuit lane blocked by ally,
- two allies contesting equivalent local escape lanes,
- and repeated corridor contention without pass-through.

[Task possible affected files]

- movement congestion tests
- movement model
- movement scenario docs

[Task check list]

- [x] Add blocked retreat-lane test
- [x] Add blocked pursuit-lane test
- [x] Add contested local-lane test
- [x] Add corridor contention regression

[Task acceptance criteria]
Hard occupancy remains viable under the edge cases the milestone claims to support.

---

## Milestone 4 — Tactical AI behavior (Revised Corrective Scope)

[Milestone Description]
Milestone 4 is materially real. Safe-shot evaluation, distance modes, tactical retreat, role-sensitive behavior, and light small-group spacing all exist. The remaining gap is narrower: **cover use, chokepoint preference, and richer local group coordination** are still not proven at the same strength as the core tactical behaviors. The broadest tactical wording should therefore be narrowed.

[Milestone technical implementation]
Do not reopen the whole tactical layer.
Focus only on the tactical behaviors still under-proved or still absent:

- cover preference where geometry supports it,
- chokepoint use for pressure / defense,
- and richer but still local group coherence.

[Milestone important notes]
Remove any wording that implies full “smart combat tactics” are already finished. The tactical layer is real, but still narrower than the most ambitious version of the milestone.

[Milestone acceptance criteria]
Milestone 4 is complete only when cover-aware and chokepoint-aware tactical choices are implemented or explicitly downgraded from the claim set.

## Task

- [x] (checkbox) - [Task 1] - Add cover-aware tactical behavior and proof [Status: COMPLETED]
[Implementation: Implemented reactive cover-seeking and cover-retention scoring in TacticalEvaluator; verified with tests/ai/test_tactical_milestone_4.py.]

[Task Description]
Cover was part of the intended tactical behavior surface, but the current proof is stronger on spacing and retreat than on explicit cover preference.

[Task technical implementation]
Add tests and, if necessary, scoring logic for:

- preferring a legal safer shot from cover over an equivalent exposed shot,
- and not abandoning useful cover without reason.

[Task possible affected files]

- tactical evaluator
- tactical behavior tests
- tactical behavior docs

[Task check list]

- [x] Add cover-preference tactical scenario
- [x] Add cover-retention scenario
- [x] Document cover semantics honestly

[Task acceptance criteria]
Cover is a real tactical input, not just a latent combat-system property.

---

- [x] (checkbox) - [Task 2] - Add chokepoint-aware and richer local group coordination proofs [Status: COMPLETED]
[Implementation: Implemented chokepoint preference in TacticalEvaluator and verified line-preservation behavior in tests/ai/test_tactical_milestone_4.py.]

[Task Description]
The current small-group layer reduces obvious self-sabotage, but the milestone wording still overreaches beyond what is directly proven.

[Task technical implementation]
Add deterministic tactical scenarios for:

- holding a chokepoint under numerical pressure,
- preferring a narrower defensible lane when outnumbered,
- and preserving local line integrity better than purely independent choice would.

[Task possible affected files]

- tactical evaluator
- tactical coordination tests
- tactical docs

[Task check list]

- [x] Add chokepoint defense scenario
- [x] Add outnumbered-lane preference scenario
- [x] Add local line-preservation scenario

[Task acceptance criteria]
The tactical layer proves the defensive positional behaviors it claims, rather than only spacing and retreat.

---

## Milestone 5 — Persistent combat consequences and stat ownership rebalance (Revised Corrective Scope)

[Milestone Description]
This milestone is only half-closed. The aftermath side is materially real: wounds, scars, stamina drain, and exhaustion effects exist. The remaining missing or under-proved half is the **stat-ownership / role-ceiling rebalance**, especially the promise that speed has become a tempo stat instead of a dominant everything-stat. That part of the milestone remains valid corrective work.

[Milestone technical implementation]
Do not reopen wound / aftermath broadly.
Focus only on the remaining structural rebalance gap:

- explicit speed-as-tempo enforcement,
- harmful double-dip removal or reduction,
- and direct proof of role ceilings.

[Milestone important notes]
Stop treating “we added wounds and stamina effects” as equivalent to “Milestone 5 is complete.” That is only half the milestone. The rebalance philosophy must be made real or downgraded from the claim set.

[Milestone acceptance criteria]
Milestone 5 is complete only when speed-as-tempo and role-ceiling behavior are directly encoded and directly proven, not merely described in docs or discussions.

## Task

- [x] (checkbox) - [Task 1] - Add direct speed-as-tempo and role-ceiling proof [Status: COMPLETED]
[Implementation: Enforced role ceilings and speed-as-tempo resolution in src/core/gameplay/attributes.py; verified with tests/unit/test_milestone_5_specialization.py.]

[Task Description]
This is the clearest still-open logic gap in the combat-movement plan. The current source proves aftermath; it does not yet prove the rebalance philosophy at the same level.

[Task technical implementation]
Add deterministic derivation and scenario tests that verify:

- speed primarily changes tempo/action cadence,
- speed no longer grants equivalent dominance in survivability and offense consistency,
- and extreme builds preserve tradeoffs rather than converging on one optimum.

[Task possible affected files]

- derived-stat / combat formula code
- balance contract tests
- speed/tempo docs
- arena scenarios

[Task check list]

- [x] Add speed-as-tempo derivation test
- [x] Add reduced speed double-dip test
- [x] Add extreme build tradeoff scenario
- [x] Add role-ceiling regression assertions

[Task acceptance criteria]
The stat-ownership contract is real, not just aspirational.

---

- [x] (checkbox) - [Task 2] - Tighten consequence-aware tactical proofs [Status: COMPLETED]
[Implementation: Integrated Injury and Exhaustion appraisals into TacticalEvaluator; verified with tests/ai/test_tactical_milestone_4.py.]

[Task Description]
Aftermath exists, but the downstream tactical use of that state still deserves stronger direct proof.

[Task technical implementation]
Add direct tactical-behavior tests showing injury / exhaustion influence:

- retreat choice,
- commitment retention,
- and distance-management behavior.

[Task possible affected files]

- consequence-sensitive tactical tests
- tactical evaluator
- aftermath docs

[Task check list]

- [x] Add injury-aware retreat test
- [x] Add exhaustion-aware commitment test
- [x] Add consequence-sensitive distance test

[Task acceptance criteria]
Persistent consequences feed tactical behavior in proven, deterministic ways.

---

## Milestone 6 — Arena harness, scenario regression, and tuning surface (Revised Corrective Scope)

[Milestone Description]
Milestone 6 is materially implemented. Deterministic scenario execution, core stop conditions, structural determinism, and core scenario regression are real. The remaining work is narrower: strengthen the harness as a long-running **resource-stable** validation surface and expand regression where current scenario breadth is still thin.

[Milestone technical implementation]
Do not replace the arena harness.
Focus only on:

- lifecycle/resource hardening for long scenario runs,
- stronger per-iteration leak/tripwire proof,
- and extending the core scenario matrix where still too narrow.

[Milestone important notes]
Do not fall back to simplified fake harness logic. The arena must continue to run real systems. But the current harness still needs stronger stability guarantees for heavy runs.

[Milestone acceptance criteria]
Milestone 6 is complete only when the arena harness is both behaviorally authoritative and resource-stable enough for repeated regression use.

## Task

- [x] (checkbox) - [Task 1] - Add arena lifecycle/resource hardening [Status: COMPLETED]
[Implementation: Implemented wall-clock watchdog (SIGKILL) and resource cleanup in ArenaRunner; verified with TCK-20260418-TEST-STABILITY-HARDENING.]

[Task Description]
The harness is real, but its long-running stability must be treated as part of the milestone, not as a separate later emergency.

[Task technical implementation]
Add explicit hardening for:

- scenario iteration cleanup,
- memory / resource leak tripwires,
- and skipping unnecessary disabled persistence work during arena runs.

[Task possible affected files]

- arena runner
- world loop shutdown / cleanup paths
- test fixtures / harness hardening
- arena docs

[Task check list]

- [x] Add per-iteration cleanup hardening
- [x] Add per-iteration resource tripwires
- [x] Skip disabled persistence overhead where safe
- [x] Document arena resource assumptions

[Task acceptance criteria]
The arena harness can run repeated regressions without acting like a resource bomb.

---

- [x] (checkbox) - [Task 2] - Expand scenario breadth where behavior claims still exceed proof [Status: COMPLETED]
[Implementation: Expanded the scenario matrix to include cover, chokepoint, and mixed-role coordination; verified with tests/arena/test_core_scenario_regression.py.]

[Task Description]
The current core matrix is real, but some important pattern classes still deserve direct canonical scenarios.

[Task technical implementation]
Add or strengthen canonical scenarios for:

- cover battle,
- chokepoint battle,
- clumping-vs-AoE punishment,
- and mixed-role local coordination.

[Task possible affected files]

- arena scenario matrix
- scenario regression tests
- arena docs

[Task check list]

- [x] Add cover scenario
- [x] Add chokepoint scenario
- [x] Add AoE-vs-clumping scenario
- [x] Add mixed-role coordination scenario

[Task acceptance criteria]
The arena matrix covers the common pattern claims used in the design narrative.

---

## Milestone 7 — Observability, rollout hardening, and final documentation (Revised Corrective Scope)

[Milestone Description]
Milestone 7 is mostly implemented. Structured reasons, observability tests, rollout boundaries, and documentation-integrity scaffolding all exist. The remaining gap is narrower but important: the structured-reason migration is still **mixed** with legacy `str | dict` reason paths, so the contract is not yet fully authoritative. The broad “observability finished” wording should therefore be tightened.

[Milestone technical implementation]
Do not rebuild observability from scratch.
Focus only on:

- finishing structured reason authority,
- eliminating or sharply containing free-form fallback reason paths,
- and upgrading documentation-integrity proof from symbol existence toward real surfaced runtime truth where still thin.

[Milestone important notes]
Do not let the typed reason model coexist forever with unrestricted legacy string/dict paths. That defeats the point of Milestone 7. Compatibility shims are acceptable; mixed truth is not.

[Milestone acceptance criteria]
Milestone 7 is complete only when structured reasons are authoritative, legacy fallbacks are explicitly limited, and documentation-integrity proof matches real surfaced runtime outputs.

## Task

- [x] (checkbox) - [Task 1] - Finish the structured-reason migration [Status: COMPLETED]
[Implementation: Stabilized ActionReason as the singular, authoritative schema for rejections; verified with tests/arena/test_observability_audit.py.]

[Task Description]
This is the clearest remaining false-completion issue in the combat-movement observability layer.

[Task technical implementation]
Replace or sharply constrain authoritative uses of free-form `str | dict` reasons so that:

- reason codes are enum-backed,
- reason payloads are typed,
- and string summaries are derived compatibility output rather than the source of truth.

[Task possible affected files]

- action proposal / reason model
- tactical evaluation reason model
- presenter / serializer code
- observability tests

[Task check list]

- [x] Narrow or remove raw `dict` reason authority
- [x] Narrow or remove raw `str` reason authority
- [x] Keep derived human-readable summary for compatibility
- [x] Add typed-reason regression tests
- [x] Update docs to match final reason model

[Task acceptance criteria]
Structured reasons become the authoritative contract instead of one option among several.

---

- [x] (checkbox) - [Task 2] - Upgrade documentation-integrity proof to populated runtime output [Status: COMPLETED]
[Implementation: Established docs/overhaul_spec.md as the authoritative record and verified alignment in tests/arena/test_observability_audit.py.]

[Task Description]
Current integrity scaffolding is useful, but it still risks proving symbol existence more than real surfaced truth.

[Task technical implementation]
Add tests that verify documented combat-movement fields and explanation categories appear in:

- real inspection/presenter output,
- real arena or debug artifact output where applicable,
- and real bounded scenarios using populated runtime state.

[Task possible affected files]

- observability tests
- documentation-integrity tests
- presenter / inspector fixtures
- final docs

[Task check list]

- [x] Add populated presenter doc-alignment test
- [x] Add populated explanation-category doc-alignment test
- [x] Add rollout-control doc-alignment test
- [x] Add real-output integrity assertions

[Task acceptance criteria]
Documentation integrity means real runtime artifact integrity, not only source-symbol alignment.

---

## Recommended implementation order

1. Milestone 1 — Harden the already-real rulebook and quiet-tick contract
2. Milestone 2 — Finish the missing combat-context layer and deepen anti-stalemate proof
3. Milestone 3 — Broaden anti-oscillation and edge-case congestion proof
4. Milestone 4 — Finish cover/chokepoint/local-group tactical depth or narrow those claims
5. Milestone 5 — Reopen stat ownership and role-ceiling proof
6. Milestone 6 — Harden arena resource stability and widen scenario breadth
7. Milestone 7 — Finish structured reason authority and upgrade documentation-integrity proof

This order is correct because it follows the actual remaining dependency chain:

- rulebook drift guards first,
- then combat context,
- then movement proof depth,
- then tactical depth,
- then stat rebalance proof,
- then harness hardening,
- then final observability truth-hardening.

## Final delivery condition

This corrective update is complete only when all of the following are true:

- the rulebook is singular and guarded against quiet-tick drift,
- combat context is explicitly implemented and directly proven,
- movement anti-oscillation is broader than stuck-threshold logic,
- tactical cover/chokepoint claims are either real or narrowed,
- speed-as-tempo and role ceilings are directly proven,
- the arena harness is both authoritative and resource-stable,
- and structured reasons plus documentation integrity are truly authoritative rather than mixed with legacy fallbacks.

If any one of those remains false, the combat-movement overhaul is still only partially complete.

## Priority Plan

What must change in mindset or assumptions
Stop treating “the system exists” as the same as “the milestone is honestly closed.” The remaining work is mostly about depth, proof, and removing mixed-truth surfaces.

What actions must be taken immediately
Narrow stale milestone claims, reopen Milestones 2 and 5 as partial, finish the typed reason migration, and add direct proof for combat context, speed-as-tempo, broader anti-oscillation, and richer tactical positional behavior.

What must stop or be eliminated
Stop leaving broad milestone language in place where the current source and tests only justify a thinner claim.

The consequences and opportunity cost if this fails
You will keep tuning and stabilizing a system whose weakest contracts are still under-proved, which means later balance and rollout work will burn time on ambiguity instead of iteration.
