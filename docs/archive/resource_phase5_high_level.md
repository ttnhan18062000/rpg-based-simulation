# High-Level Implementation Plan — Phase 5 of `src_v2`

This plan assumes Phase 4 has brought `src_v2` to a materially better state, but not yet to full RPG-core progression closure.

It assumes the current branch either already has, or is expected to complete before formal Phase 5 entry:

- a stronger deterministic movement slice,
- a bounded resource interaction slice,
- improved replay correctness,
- better inventory pressure handling,
- and a meaningful engine/runtime proof surface.

It also assumes the project is **not done** recovering the original RPG-core loop from `src`.

This is not the phase where the project should widen into combat, broad AI, full quest graphs, or generalized economy simulation.

It is the phase where `src_v2` must recover the next part of the original gameplay spine:

- resources moving from world to inventory,
- inventory resolving through town behavior,
- town behavior producing material/gold/capability pressure,
- that pressure generating blockers, hints, and leads,
- and the resulting loop being proven, benchmarked, and declared honestly.

The purpose of Phase 5 is:

- close the remaining Phase 4 proof and readiness gaps,
- recover the town/resource progression loop from the original `src`,
- recover the first bounded strategic resource-intelligence loop,
- prove the integrated progression loop against original behavior where preservation is required,
- and expand support, benchmark, certification, and release truth around that real gameplay loop.

This version keeps the same milestone format as the prior high-level implementation plans, but aligns the next phase to the actual current branch state rather than to generic expansion language.

---

# [Milestone 1] - Phase 4 Exit Closure and Phase 5 Readiness

## [Milestone Description]

Milestone 1 is the entry gate for Phase 5.

Its purpose is to stop the team from building the next gameplay loop on top of unfinished Phase 4 truth gaps.

By this point, `src_v2` may already have a better movement slice and a better resource interaction slice, but that does not automatically mean the branch is ready for the next phase.

This milestone exists to close the remaining gaps that would otherwise contaminate all later progression work:

- proof gaps,
- parity enforcement gaps,
- support-boundary ambiguity,
- release-truth gaps,
- and resource-contract ambiguity.

This milestone does not add new major gameplay semantics.

It closes the phase boundary honestly.

## [Milestone technical implementation]

Create one explicit readiness gate for Phase 5 that confirms the current `src_v2` branch is stable enough to attach the next progression-layer systems.

This milestone must:

- finalize remaining Phase 4 movement/resource proof gaps,
- ensure the current support boundary is explicit,
- ensure release/documentation truth is back in sync with code,
- ensure parity verification is not hidden in ad hoc scripts alone,
- and close any remaining declared-but-not-governed resource-contract ambiguity.

This milestone must not:

- widen gameplay breadth,
- begin broad town/economy behavior before entry criteria are satisfied,
- or treat partial green tests as equivalent to true phase closure.

## [Milestone important notes]

The trap here is premature graduation.

A branch that is “much better than before” is still not phase-ready if:

- proofs lag implementation,
- support claims remain ambiguous,
- release truth is still broken,
- or declared resource contracts are still only partially real.

This milestone is successful only if Phase 5 starts from a platform that is honest enough to extend.

## [Milestone acceptance criteria]

At the end of this milestone:

- the current movement slice is enforced as an official proof-gated slice,
- the current resource interaction slice has at least initial differential validation against original `src` where preservation is required,
- release/documentation surfaces are green again,
- current support boundaries are explicit,
- and Phase 5 can begin without inheriting unresolved Phase 4 truth debt.

## Task

- [ ] (checkbox) - [Task 1] - Promote movement parity verification into the standard proof/test path
- [ ] (checkbox) - [Task 2] - Add initial differential validation for the current resource interaction slice against original `src`
- [ ] (checkbox) - [Task 3] - Restore or regenerate missing release/documentation proof artifacts and integrity checks
- [ ] (checkbox) - [Task 4] - Reconfirm and publish the current support boundary for movement and resource interaction
- [ ] (checkbox) - [Task 5] - Resolve remaining declared-resource contract ambiguity such as CPU-governance scope
- [ ] (checkbox) - [Task 6] - Freeze the Phase 4 exit package: support status, proof status, known limitations, and declared divergences
- [ ] (checkbox) - [Task 7] - Publish the formal “Phase 5 ready” gate

---

# [Milestone 2] - Supported Town Resource Resolution Core

## [Milestone Description]

Milestone 2 is the first real gameplay milestone of Phase 5.

Its purpose is to recover the next missing section of the original RPG-core loop: town-based resource resolution.

The current branch already has stronger world-side resource behavior than before, but world-side gathering alone is not a progression loop.

The original `src` does not stop at loot and harvest.
It routes gathered value through town systems that resolve inventory pressure, convert materials and items into progression, and generate new needs.

This milestone recovers the first bounded, officially supported version of that town loop.

## [Milestone technical implementation]

Create one native `src_v2` town resource-resolution layer that covers the first officially supported town-side progression behavior.

This milestone must:

- define the supported town-entry resource resolution behavior,
- define the first supported shop behavior,
- define the first supported blacksmith or material-resolution behavior,
- define what inventory is converted, preserved, sold, consumed, or blocked,
- and keep all of that within a narrow, proofable support boundary.

This milestone must preserve discipline.
It must not widen into broad economy simulation, rich pricing systems, full crafting graphs, or generalized service AI.

## [Milestone important notes]

The danger here is faking the town loop with temporary shortcuts and then quietly treating those shortcuts as the game.

This milestone is not successful because town “does something.”
It is successful only if town behavior becomes the next truthful step in the supported progression loop.

## [Milestone acceptance criteria]

At the end of this milestone:

- town resource resolution is an officially supported gameplay slice,
- supported shop/blacksmith/town-entry behavior is explicit,
- inventory-to-progression behavior is explicit,
- original behavior is preserved where required or divergences are declared,
- and town behavior is integrated into replay, lifecycle, and certification surfaces where relevant.

## Task

- [ ] (checkbox) - [Task 1] - Freeze the exact scope of the supported town resource-resolution slice
- [ ] (checkbox) - [Task 2] - Capture original `src` town/shop/blacksmith behavior for supported cases through characterization tests or fixtures
- [ ] (checkbox) - [Task 3] - Define the V2 authoritative state, work contract, and apply contract for supported town resolution
- [ ] (checkbox) - [Task 4] - Implement or finalize the local reference path for town-entry resource resolution
- [ ] (checkbox) - [Task 5] - Implement the supported shop and blacksmith behavior for the declared narrow scope
- [ ] (checkbox) - [Task 6] - Integrate town resolution into replay, runtime visibility, and certification surfaces where needed
- [ ] (checkbox) - [Task 7] - Add parity, contract, lifecycle, and certification tests for town resource resolution
- [ ] (checkbox) - [Task 8] - Declare the support boundary and intentional divergences for the town resource-resolution slice

---

# [Milestone 3] - Strategic Resource Intelligence and Blocker/Lead Recovery

## [Milestone Description]

Milestone 3 recovers the first bounded strategic feedback loop from resource progression.

The original `src` does not treat gathering and town services as isolated mechanics.
Those systems emit pressure, needs, hints, and leads that shape what happens next.

This milestone exists to recover the first supported version of that loop in `src_v2`.

The goal is not to recover all strategic AI.
The goal is to recover the part of strategy that is directly necessary for resource progression truth.

## [Milestone technical implementation]

Create one bounded strategic resource-intelligence layer that connects town/resource outcomes back into future world-facing gameplay.

This milestone must:

- define supported blocker emission from resource/town state,
- define supported guild or resource-intel outputs,
- define supported lead generation for materials, locations, camps, or zones,
- define how supported blockers and leads feed the next action loop,
- and keep the scope narrow enough to stay testable and honest.

This milestone must not widen into rich project systems, full social strategy, or broad long-horizon AI reconstruction.

## [Milestone important notes]

The trap here is pretending strategic recovery means “AI is back.”
It is not.

This milestone is only about restoring the strategic outputs necessary to make the resource loop feel like the same RPG again.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported resource blockers are emitted explicitly,
- supported resource leads or hints are generated explicitly,
- the town/resource loop can feed future resource-seeking action,
- preservation vs divergence boundaries are explicit,
- and the resource progression loop is no longer just a disconnected gather-and-sell system.

## Task

- [ ] (checkbox) - [Task 1] - Freeze the exact scope of supported blocker, hint, and lead behavior for Phase 5
- [ ] (checkbox) - [Task 2] - Capture original `src` guild/resource-intelligence behavior for supported cases through characterization tests or fixtures
- [ ] (checkbox) - [Task 3] - Define the V2 authoritative state and update contracts for blockers, hints, and leads in supported scope
- [ ] (checkbox) - [Task 4] - Implement or finalize the local reference path for supported strategic resource-intelligence outputs
- [ ] (checkbox) - [Task 5] - Integrate strategic outputs into the supported gameplay loop without widening into broad AI scope
- [ ] (checkbox) - [Task 6] - Add replay/runtime/certification visibility for blocker and lead generation where needed
- [ ] (checkbox) - [Task 7] - Add parity, contract, lifecycle, and certification tests for the supported strategic resource-intelligence slice
- [ ] (checkbox) - [Task 8] - Declare the support boundary and intentional divergences for supported blocker/hint/lead behavior

---

# [Milestone 4] - Integrated Resource Progression Differential Proof

## [Milestone Description]

Milestone 4 is the proof milestone for the Phase 5 loop.

By this point, the branch should have:

- movement,
- resource interaction,
- town resource resolution,
- and strategic resource-intelligence outputs

at least within a narrow supported scope.

This milestone exists to prove that those pieces together preserve the intended RPG-core progression loop where preservation is required.

This is not a generic testing milestone.
It is the milestone that stops the team from declaring loop recovery without evidence.

## [Milestone technical implementation]

Create one integrated differential-proof layer comparing the supported progression loop in original `src` and `src_v2` under equivalent conditions where parity is intended.

This milestone must:

- define equivalent scenarios across old and new implementations,
- compare authoritative outcomes for the supported loop,
- log and explain accepted divergences,
- guard against parity drift,
- and make those guards part of the normal validation path.

This milestone must not pretend unsupported original behavior is already preserved.
Scope must stay narrow and literal.

## [Milestone important notes]

The danger here is self-deception.

Once several pieces work in `src_v2`, teams start calling that “recovered gameplay.”
That claim is worthless unless old-vs-new comparisons exist for the same supported loop.

## [Milestone acceptance criteria]

At the end of this milestone:

- the integrated resource progression loop has old-vs-new comparison coverage for the declared support boundary,
- accepted divergences are explicit,
- parity drift is guarded in the standard validation path,
- and the project can state what part of the original loop is now truly recovered.

## Task

- [ ] (checkbox) - [Task 1] - Freeze the exact parity scope for the integrated Phase 5 progression loop
- [ ] (checkbox) - [Task 2] - Build old-vs-new scenario fixtures for supported gather, return, resolve, and redirect behavior
- [ ] (checkbox) - [Task 3] - Compare authoritative results for supported loop scenarios and investigate mismatches
- [ ] (checkbox) - [Task 4] - Record explicit intentional divergences where preservation is not required or not yet possible
- [ ] (checkbox) - [Task 5] - Add regression guards for integrated parity drift in the normal validation path
- [ ] (checkbox) - [Task 6] - Add lifecycle and replay validation for the integrated supported loop
- [ ] (checkbox) - [Task 7] - Publish the first precise statement of what resource progression behavior is now recovered vs not recovered

---

# [Milestone 5] - Supported Progression Surface Consolidation

## [Milestone Description]

Milestone 5 consolidates the supported gameplay surface after the progression loop is recovered to the declared extent.

Its purpose is to stop the project from remaining a pile of individually supported systems and turn it into one explicit supportable progression package.

This is where the project should be able to state, precisely:

- what movement/resource/town/strategic progression behavior is officially supported,
- under what profiles,
- under what execution modes,
- with what lifecycle and replay guarantees,
- with what benchmark and certification scope,
- and with what preserved original behavior vs intentional divergence.

## [Milestone technical implementation]

Create one progression-support consolidation layer that unifies:

- support boundaries,
- benchmark boundaries,
- certification boundaries,
- release-gate expectations,
- known limitations,
- and progression-loop claim scope.

This milestone must:

- expand benchmark scenarios around the integrated progression loop,
- expand certification scenarios around the integrated progression loop,
- integrate supported progression truth into release expectations,
- tighten proof and report language around the supported loop,
- and publish one coherent support package for the current phase.

This milestone must not widen into unsupported later systems just because the progression loop is now stronger.

## [Milestone important notes]

This milestone is the difference between:

- “the branch contains a stronger RPG loop”
  and
- “the branch can state exactly what RPG progression loop it supports and proves.”

If the support package, release truth, benchmarks, certification, and docs do not all say the same thing, the phase failed.

## [Milestone acceptance criteria]

At the end of this milestone:

- the supported progression surface is explicit,
- benchmark and certification matrices cover the declared supported loop,
- release-gate expectations reflect real progression-loop proof,
- preserved vs divergent original behavior is stated explicitly,
- and the project is ready to decide the next post-progression phase without lying about what is already done.

## Task

- [ ] (checkbox) - [Task 1] - Define the supported progression-surface matrix for the current `src_v2` phase
- [ ] (checkbox) - [Task 2] - Expand certification scenarios to cover the integrated supported progression loop
- [ ] (checkbox) - [Task 3] - Expand benchmark scenarios to cover the integrated supported progression loop
- [ ] (checkbox) - [Task 4] - Integrate supported progression truth into release-gate expectations and proof bundle requirements
- [ ] (checkbox) - [Task 5] - Consolidate report language and proof language around supported progression claims
- [ ] (checkbox) - [Task 6] - Add progression-surface regression guards for parity, determinism, lifecycle, and proof integrity
- [ ] (checkbox) - [Task 7] - Publish the supported progression package: matrix, boundaries, known limitations, preserved behavior, and declared divergences

---

## Shared Milestone Exit Checklist

The following are not core milestone tasks unless the milestone is specifically about them.
They are required close-out checks for every milestone in this phase.

- [ ] Documentation updated
- [ ] Divergence log updated
- [ ] Regression guards added or updated where relevant
- [ ] Support boundary declared or updated
- [ ] Lifecycle impact reviewed
- [ ] Certification/proof impact reviewed
- [ ] Benchmark impact reviewed where applicable
- [ ] Known limitations recorded
- [ ] Original `src` parity impact reviewed where preservation is claimed
