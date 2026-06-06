# Revised High-Level Implementation Plan — Next Phase of `src`

This plan assumes the current `src` branch is **close** to build-ready, but not yet ready to freeze blindly.

This is not a new roadmap from zero.

It is the corrected next implementation phase after the current hardening work, where `src` already has:

- profile and startup contracts,
- authoritative state and apply-path structure,
- runtime control and anti-thrashing behavior,
- lifecycle-aware shutdown/certification flow,
- replay/proof bundle structure,
- and a meaningful law-style test surface.

However, this next phase does **not** assume that every substrate truth problem is already closed.
Before the substrate is frozen, the project must close the remaining resource-truth and behavior-truth gaps that would otherwise contaminate every later gameplay slice.

The purpose of this corrected next phase is:

- close remaining substrate truth gaps before freeze,
- freeze the repaired substrate only after closure,
- attach the first officially supported RPG-core slice without semantic drift from original `src`,
- build the benchmark and optimization foundation around a real preserved gameplay slice,
- widen the supported gameplay surface carefully along the original RPG-core path,
- and consolidate certification, proof, and release truth around real gameplay rather than only engine infrastructure.

This version corrects two major risks in the earlier plan:

- freezing a substrate that still has unresolved truth gaps,
- and drifting away from original `src` RPG-core logic by using generic slice names that do not match the old gameplay loop.

---

# [Pre-Milestone Gate] - Resource Truth Closure

## [Gate Description]

Before Milestone 1 begins, the project must close the remaining substrate issues that would make any later freeze dishonest.

This gate exists because a platform is not ready for “freeze and attach gameplay” just because its architecture looks cleaner or its milestone language is more disciplined.

If declared runtime resources are only partially enforced, if replay truth is still vulnerable to incorrect pressure-path behavior, or if official gameplay attachment begins before old-`src` behavior is pinned as the oracle, then the team is not moving from repair mode to build mode.
It is moving unresolved defects deeper into the foundation.

## [Gate technical implementation]

This gate must close four categories of truth:

1. **Declared resource truth closure**
   - no declared runtime resource may remain profile-only or documentation-only,
   - every declared governed resource must be either measured, interpreted, and certified,
   - or explicitly downgraded out of the supported resource contract.

2. **Replay pressure truth closure**
   - replay chunk rotation and persistence must remain correct under pressure,
   - async persistence must not rely on mutable state that can drift after dispatch,
   - proof artifacts must remain coherent under rotation, pressure, and shutdown.

3. **Concurrency support-boundary truth closure**
   - currently supported concurrent work kinds must be explicit,
   - local-only work kinds must be explicit,
   - and undeclared execution-mode broadening must fail visibly.

4. **Behavior-oracle closure for official gameplay attachment**
   - original `src` and `tests` become the required behavior oracle for official RPG slices,
   - parity-required behavior must be captured before a slice can be declared officially supported,
   - and any intentional divergence must be logged explicitly.

## [Gate important notes]

This is not extra ceremony.
It is the line between a trustworthy port and a clean-looking fork.

If this gate is skipped, later milestones may still look disciplined while the branch quietly drifts away from either:

- its declared runtime contract,
- or its original RPG-core logic.

## [Gate acceptance criteria]

Before Milestone 1 starts:

- every in-scope resource claim is either fully enforced or explicitly removed from scope,
- replay pressure paths are correct under bounded async behavior,
- current concurrency support boundaries are explicit and enforced,
- and original `src/tests` are established as the required oracle for official gameplay slices.

---

# [Milestone 1] - Substrate Freeze and Baseline Readiness

## [Milestone Description]

Milestone 1 is the transition from repair mode to controlled build mode.

Its purpose is to freeze the repaired `src` substrate so future gameplay implementation does not continue building on moving assumptions.

At this point, the engine should already have passed the Resource Truth Closure gate.
This milestone turns repaired and closed substrate truths into a stable platform instead of letting the team keep reopening substrate arguments during gameplay work.

This milestone does not introduce major new gameplay.

It creates the baseline that the first official gameplay slice will be allowed to stand on.

## [Milestone technical implementation]

Create one stable implementation baseline for future RPG-core porting and feature work.

This milestone must:

- freeze the semantic baseline contract,
- freeze the runtime signal and lifecycle vocabulary,
- freeze the current proof bundle and certification artifact contract,
- freeze the supported concurrency boundary for current scope,
- remove remaining transitional inconsistencies,
- establish one explicit readiness gate for gameplay attachment,
- and explicitly bind future official gameplay slices to old `src/tests` characterization and divergence discipline.

This milestone must not:

- widen gameplay breadth,
- introduce combat,
- introduce complex item or quest systems,
- start broad optimization before benchmark truth exists,
- or permit unofficial gameplay semantics to harden into “the new normal” without parity review.

## [Milestone important notes]

The main trap here is still impatience.

If the substrate is “mostly fixed” but the team freezes it before its support boundaries, behavior oracle rules, and truth surfaces are fully closed, every later gameplay slice will become harder to reason about, harder to compare against original `src`, and harder to certify honestly.

This milestone is not glamorous.
It is a stabilization gate.

## [Milestone acceptance criteria]

At the end of this milestone:

- the local `src` semantic baseline is stable,
- runtime/lifecycle/certification truth contracts are stable,
- proof bundle conventions are stable,
- supported concurrency boundaries are explicit,
- original `src/tests` are formally established as the gameplay behavior oracle for official slices,
- and the team has one clear “ready for gameplay attachment” platform.

## Task

- [ ] (checkbox) - [Task 1] - Freeze the repaired semantic baseline contract for `src`
- [ ] (checkbox) - [Task 2] - Freeze runtime signal, runtime status, and lifecycle outcome vocabulary
- [ ] (checkbox) - [Task 3] - Freeze proof bundle artifact naming and required certification artifact rules
- [ ] (checkbox) - [Task 4] - Freeze the currently supported concurrency scope and explicitly mark unsupported work kinds
- [ ] (checkbox) - [Task 5] - Remove remaining transitional, dead, or compatibility-only substrate paths
- [ ] (checkbox) - [Task 6] - Add substrate drift guardrails and baseline compatibility checks
- [ ] (checkbox) - [Task 7] - Publish the official “ready for gameplay attachment” gate
- [ ] (checkbox) - [Task 8] - Publish one known-boundaries package for the frozen substrate
- [ ] (checkbox) - [Task 9] - Publish the gameplay-oracle and divergence-rule package for official RPG slices

---

# [Milestone 2] - Attach Gate 1: Deterministic Grid Movement as the First Official RPG Slice

## [Milestone Description]

Milestone 2 is the first official gameplay milestone for `src`.

Its purpose is to make deterministic **grid movement** the first officially supported RPG-core slice in the new engine.

Movement is chosen first because it is:

- visible in authoritative state,
- foundational to the original `src` gameplay loop,
- suitable for parity validation against original `src`,
- suitable for replay, lifecycle, and certification proof,
- and narrow enough to port without exploding state complexity.

This milestone is not about movement merely existing in code.

It is about making movement official, contract-bound, parity-reviewed, test-pinned, and ready to serve as the model for every later gameplay slice.

## [Milestone technical implementation]

Create one first-class movement feature pack that spans:

- original `src` movement behavior capture,
- V2 authoritative state contract,
- local execution,
- supported concurrent execution where declared,
- apply-path integration,
- replay visibility,
- runtime visibility,
- and certification coverage.

The movement scope in this milestone must preserve the original RPG-core semantics where required, including:

- tile/grid position semantics,
- blocked move handling,
- occupancy rules,
- Manhattan/adjacency-compatible movement expectations where applicable,
- and any intentionally deferred complexity being logged explicitly as divergence rather than silently rewritten.

This milestone must keep scope narrow.
It must not pull in combat, broad pathfinding systems, or complex interaction trees.

## [Milestone important notes]

The first supported gameplay slice sets the standard for the rest of the epic.

If this slice is loose, every later slice will be loose.
If this slice is disciplined, the rest of the gameplay port can stay disciplined.

The danger here is semantic drift disguised as simplification.
A movement system that is “deterministic” but no longer behaves like the original RPG movement contract is not a successful first slice.
It is a quiet fork.

## [Milestone acceptance criteria]

At the end of this milestone:

- deterministic grid movement is an officially supported gameplay slice in `src`,
- intended original movement behavior is preserved where required,
- divergences are explicit where intentional,
- the local path is authoritative,
- supported concurrent behavior is explicitly scoped,
- movement is visible to replay/runtime/certification,
- and movement is ready to be benchmarked and optimized.

## Task

- [ ] (checkbox) - [Task 1] - Freeze the exact scope of the first supported movement slice
- [ ] (checkbox) - [Task 2] - Capture original `src` movement behavior through characterization tests or scenario fixtures
- [ ] (checkbox) - [Task 3] - Define the V2 authoritative state, work contract, and apply contract for movement
- [ ] (checkbox) - [Task 4] - Implement or finalize the local movement reference path in `src`
- [ ] (checkbox) - [Task 5] - Implement or finalize the supported concurrent movement path for declared safe scope
- [ ] (checkbox) - [Task 6] - Integrate movement into replay, runtime visibility, and certification surfaces
- [ ] (checkbox) - [Task 7] - Add parity, equivalence, lifecycle, and certification tests for movement
- [ ] (checkbox) - [Task 8] - Declare movement as the first officially supported RPG slice and publish its support boundary

---

# [Milestone 3] - Benchmarking, Profiling, and Hot-Path Optimization Foundation

## [Milestone Description]

Milestone 3 is the beginning of real performance work.

Up to this point, the epic has mostly built the trustworthy optimization substrate:

- profiles,
- tick budgets,
- pressure signals,
- lifecycle-safe runtime behavior,
- supported concurrency boundaries,
- certification structure,
- and one official gameplay slice whose preserved semantics are now explicit.

That groundwork is necessary, but it is not yet an optimization program.

This milestone turns performance into an explicit implementation track.

Its purpose is to create a reliable benchmarking and profiling foundation, then use that foundation to reduce processing time and increase sustainable TPS for declared scenarios, profiles, and hardware classes without altering preserved RPG-core semantics.

## [Milestone technical implementation]

Create one benchmark, profiling, and optimization foundation that can support real TPS improvement work without sacrificing:

- determinism,
- lifecycle truth,
- boundedness,
- supported concurrency truth,
- proof honesty,
- or old-`src` semantic parity where parity is part of the support contract.

This milestone must produce:

- stable benchmark scenarios,
- per-phase and per-subsystem timing,
- baseline throughput measurements,
- regression thresholds,
- and the first hot-path optimization passes for the baseline engine plus the official movement slice.

This milestone must not:

- make universal TPS claims,
- optimize unsupported gameplay paths,
- optimize against noisy or incomplete measurement,
- or “improve performance” by silently rewriting gameplay semantics that are supposed to be preserved.

## [Milestone important notes]

Optimization before benchmark truth is noise.
Optimization without scoped claim boundaries is marketing theater.
Optimization without lifecycle/runtime truth is how teams make systems faster and less trustworthy at the same time.
Optimization that changes preserved gameplay behavior is not optimization.
It is drift.

## [Milestone acceptance criteria]

At the end of this milestone:

- the team has stable benchmark scenarios,
- TPS and tick cost can be measured honestly,
- performance regressions can be detected,
- hot-path costs are visible,
- the first supported gameplay slice plus engine substrate have undergone the first real optimization pass,
- and parity-sensitive behavior remains guarded.

## Task

- [ ] (checkbox) - [Task 1] - Define the benchmark and profiling contract for `src`
- [ ] (checkbox) - [Task 2] - Create stable benchmark scenarios for baseline runtime and the movement slice
- [ ] (checkbox) - [Task 3] - Add per-phase and per-subsystem timing instrumentation
- [ ] (checkbox) - [Task 4] - Establish baseline TPS and tick-cost measurements by scenario, profile, and hardware class
- [ ] (checkbox) - [Task 5] - Identify the first hot paths in the baseline engine and movement slice
- [ ] (checkbox) - [Task 6] - Optimize the highest-value hot paths justified by benchmark evidence
- [ ] (checkbox) - [Task 7] - Add performance regression thresholds and regression reporting
- [ ] (checkbox) - [Task 8] - Publish the first trustworthy performance claim boundary for declared conditions
- [ ] (checkbox) - [Task 9] - Add semantic-parity regression guards so optimization cannot silently rewrite preserved gameplay behavior

---

# [Milestone 4] - Second Supported RPG Slice: Deterministic Resource Interaction Core

## [Milestone Description]

Milestone 4 widens the supported gameplay surface beyond movement, but still in a controlled way.

Its purpose is to add the second narrow RPG-core slice after movement has already been attached and benchmarked.

The second slice must follow the actual old-`src` gameplay path rather than a generic “interaction” abstraction.

The correct category here is deterministic **resource interaction core**, centered on the old loop around:

- loot channeling,
- harvest channeling,
- inventory slot and weight pressure,
- resource-node interaction,
- and blocked or aborted resource interaction outcomes.

This milestone exists to prove that the V2 porting pattern is repeatable and that the supported gameplay surface can widen without drifting away from the original RPG-core loop.

## [Milestone technical implementation]

Create one second supported RPG-core slice that is:

- native to the V2 contract,
- validated against original intended behavior where relevant,
- local-first in semantic meaning,
- explicitly scoped for concurrent support if allowed,
- and covered by lifecycle, replay, and certification proof.

This milestone must preserve discipline.
It is not yet the right time for broad combat, quest systems, rich AI trees, or full economy systems.

This milestone should focus on the bounded resource-interaction loop first.
Town-service and broader progression-resolution systems may follow later, but they must not be smuggled into this milestone under vague wording.

## [Milestone important notes]

The danger here is greed and abstraction drift.

Once movement works, teams usually want to add everything.
That is how discipline collapses.

The second danger is inventing a generic “interaction core” that sounds reusable but no longer matches the old engine’s actual RPG-core logic.

This milestone is successful only if it proves that the supported gameplay surface can widen without losing trust standards **and** without leaving the original gameplay path.

## [Milestone acceptance criteria]

At the end of this milestone:

- a deterministic resource interaction slice is officially supported,
- the slice is ported into `src` natively,
- parity and divergence rules are explicit,
- runtime/lifecycle/certification behavior are covered,
- and the engine now supports more than one gameplay slice under the V2 contract while remaining on the old RPG-core path.

## Task

- [ ] (checkbox) - [Task 1] - Select and freeze the exact scope of the deterministic resource interaction slice
- [ ] (checkbox) - [Task 2] - Capture original `src` behavior for loot, harvest, inventory pressure, and node interaction using characterization tests or fixtures
- [ ] (checkbox) - [Task 3] - Define the V2 authoritative state and work contract for the resource interaction slice
- [ ] (checkbox) - [Task 4] - Implement the local reference execution path for the resource interaction slice
- [ ] (checkbox) - [Task 5] - Implement the supported concurrent path for the resource interaction slice if explicitly allowed
- [ ] (checkbox) - [Task 6] - Integrate the resource interaction slice into engine visibility, replay, and certification surfaces
- [ ] (checkbox) - [Task 7] - Add parity, contract, lifecycle, and certification tests for the resource interaction slice
- [ ] (checkbox) - [Task 8] - Declare the support boundary for the resource interaction slice and publish any intentional divergences from original `src`

---

# [Milestone 5] - Supported Gameplay Surface Consolidation

## [Milestone Description]

Milestone 5 expands the proof and support model from “engine trust plus one or two slices” into one coherent supported gameplay surface.

Its purpose is to consolidate the now-attached slices into one explicit supported gameplay matrix:

- what behaviors are officially supported,
- under what profiles,
- under what execution modes,
- with what lifecycle guarantees,
- with what benchmark expectations,
- with what certification scenarios,
- and with what preserved original-`src` semantics or intentional divergences.

This milestone is where the epic stops certifying mostly engine infrastructure and starts certifying engine-plus-gameplay behavior in a disciplined way.

This does not mean broad gameplay explosion.
It means the supported gameplay surface becomes explicit, measurable, reviewable, and certifiable as one integrated contract.

## [Milestone technical implementation]

Create one gameplay-support and proof expansion layer that:

- broadens certification around real gameplay slices,
- broadens benchmark coverage around real gameplay slices,
- consolidates supported-surface language,
- strengthens release-gate expectations around supported gameplay,
- consolidates preserved-semantics and divergence truth,
- and prepares the project for heavier later systems without pretending they are already supported.

This milestone must still resist premature combat, AI, or quest breadth.

## [Milestone important notes]

This milestone is the difference between:

- “we have some gameplay working”
  and
- “we can state exactly what gameplay surface is supported and proven.”

Without this milestone, later systems will be built on ambiguous support claims.

The biggest trap here is overclaim.
The second trap is semantic amnesia, where the project forgets which old-`src` behaviors were preserved and which were intentionally changed.

## [Milestone acceptance criteria]

At the end of this milestone:

- the supported gameplay surface is explicit,
- movement and the resource interaction slice are both certified under declared conditions,
- benchmark and certification matrices include real gameplay behavior,
- release-gate expectations reflect supported gameplay truth,
- preserved old-`src` semantics and intentional divergences are both explicit,
- and the project is ready to consider heavier next-phase systems without losing proof discipline.

## Task

- [ ] (checkbox) - [Task 1] - Define the supported gameplay surface matrix for the current V2 phase
- [ ] (checkbox) - [Task 2] - Expand certification scenarios to cover integrated supported gameplay slices
- [ ] (checkbox) - [Task 3] - Expand benchmark scenarios to cover integrated supported gameplay loops
- [ ] (checkbox) - [Task 4] - Integrate supported gameplay truth into release-gate expectations and proof bundle requirements
- [ ] (checkbox) - [Task 5] - Consolidate report language and proof language around supported gameplay claims
- [ ] (checkbox) - [Task 6] - Add gameplay-surface regression guards for parity, determinism, lifecycle, and proof integrity
- [ ] (checkbox) - [Task 7] - Publish the supported-surface package: support matrix, boundaries, known limitations, claim scope, and divergence truth

---

# Shared Milestone Exit Checklist

The following are not core milestone tasks unless the milestone is specifically about them.
They are required close-out checks for every milestone in this phase.

- [ ] Documentation updated
- [ ] Divergence log updated
- [ ] Regression guards added or updated where relevant
- [ ] Support boundary declared or updated
- [ ] Lifecycle impact reviewed
- [ ] Certification/proof impact reviewed
- [ ] Benchmark impact reviewed if applicable
- [ ] Known limitations recorded
- [ ] Old-`src` parity expectation reviewed where relevant

**Tier:** standard
**Type:** chore
**Priority:** P1
