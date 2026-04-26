# Resource Epic Developer Handbook

## Purpose

This document is the developer-facing reference for the v2 engine epic.

It consolidates the intent, architecture, milestone sequence, current truth, execution rules, attach points, risks, boundaries, and delivery model into one place.

This is not a product brief.
This is not a milestone summary.
This is the engineering truth document for the epic.

The core idea of v2 is simple:

v2 is a deterministic, resource-bounded, profile-driven simulation runtime whose trust must be earned in layers:

1. semantic baseline,
2. runtime truth,
3. lifecycle integrity,
4. bounded concurrency trust,
5. certification and release proof.

Only after those layers are closed does it make sense to attach substantial real RPG logic.

---

## Executive summary

The v2 codebase is not an empty prototype.

It already contains the correct architectural categories:

- authoritative state,
- deterministic apply path,
- deterministic scheduler,
- canonical checkpointing,
- runtime profiles and validation,
- governor and policy,
- bounded replay pipeline,
- bounded worker/concurrency path,
- runtime status and signal collection,
- certification harness, conformance evaluator, recorder, and proof gating,
- and a meaningful law-oriented test suite.

That is the good news.

The bad news is that subsystem presence is ahead of subsystem closure.

The project is no longer blocked by missing architecture.
It is blocked by incomplete guarantees.

The central truth of the epic is therefore:

- do not add wide new capability first,
- do not attach full RPG logic first,
- do not optimize first,
- finish and harden the execution contract first.

The whole epic is organized around that reality.

---

## What this epic is actually trying to achieve

The epic is trying to produce one trustworthy engine core that can make precise claims about:

- semantic determinism,
- authoritative mutation boundaries,
- work ordering,
- profile-bounded runtime behavior,
- bounded replay and observability,
- bounded concurrent execution,
- scenario-based correctness,
- degradation and recovery behavior,
- and release readiness backed by proof artifacts.

The epic is not trying to build “an RPG” first.

The RPG is the domain that will eventually ride on top of the runtime.
The runtime has to become trustworthy before richer domain behavior is attached to it.

That is why the milestone sequence looks conservative.
It is not conservative for its own sake.
It is trying to prevent the classic failure mode where rich behavior lands on top of a runtime that still lies about ordering, pressure, shutdown, or fault handling.

---

## Current truth about the codebase

### What already exists

The following already exist in v2:

### Core and contracts

- `RuntimeProfile` with resource-envelope fields.
- `ProfileValidator` and startup/config validation.
- `EntityState` and `AuthoritativeState`.
- `EntityUpdate` and `StateUpdate`.
- `WorkClass` and `WorkItem`.
- `RuntimeMode` and `PressureSignals`.
- worker packet/result protocol.

### Engine runtime

- `Kernel`.
- authoritative phases.
- deterministic scheduler.
- apply path.
- canonical state hasher.
- governor.
- governor policy.
- runtime status.
- replay buffer/sink/manager.
- worker manager.
- worker logic seam.

### Certification

- certification models.
- conformance evaluator.
- certification harness.
- scenario expectations.
- recorder / proof output.
- release-proof gating tests.

### Tests

There is already broad law-oriented coverage across:

- profile contract and startup validation,
- authoritative state contract,
- phase order,
- kernel boundaries,
- scheduler contract,
- work classes,
- apply path,
- checkpoint reproducibility,
- determinism,
- governance isolation,
- replay chunk rotation and overflow,
- replay pressure and shutdown budget,
- observability budgets,
- anti-thrashing,
- worker bounds, equivalence, determinism, fallback, integrity,
- certification harness/conformance/final gate,
- doc integrity and contributor guardrails.

That is a serious skeleton.

### What is still not closed

The major closure gaps are these:

1. **Milestone A gap** [CLOSED]
   The single-process runtime is now the absolute semantic source of truth, isolated from all concurrency plumbing through the `IWorkExecutor` abstraction.

2. **Milestone B gap** [CLOSED]
   All mode-driving signals (utilization, debt, compute) are now sourced from real runtime behavior with disaggregated reporting.

3. **Milestone C gap** [CLOSED]
   The engine now enforces a strict lifecycle law. Shutdown targets are authoritative, and outcomes are derived from actual runtime finalization state (no simulation).

4. **Milestone D gap** [BASELINE SLICE CLOSED]
   The movement slice (`ENTITY_MOVE`) is officially supported in both local and concurrent modes with proven equivalence.

5. **Milestone E gap** [CLOSED]
   Certification universe and proof semantics have been fully expanded and hardened to the required manifest targets with 100% compliant gold proofs.

This epic exists to close those gaps in order.

---

## Foundational design principles

Every developer working inside this epic should assume the following principles are non-negotiable.

### 1. The single-process path is the semantic source of truth

The local path defines:

- tick semantics,
- authoritative apply semantics,
- work ordering,
- checkpoint identity,
- and the reference behavior for later equivalence.

Concurrent mode may optimize execution.
It may not redefine semantics.

### 2. Authoritative mutation is singular

All authoritative state changes flow through the apply path.
Nothing else gets to mutate authoritative state directly.

Not scheduler helpers.
Not runtime status.
Not replay.
Not certification.
Not worker threads.

### 3. Checkpoint identity is authoritative-only

Governance, replay, worker state, runtime signals, lifecycle status, and certification metadata must not contaminate the authoritative checkpoint/hash.

### 4. Profiles are product rules, not hints

Profiles define the resource envelope.
They are not soft suggestions.

CPU, RAM, queue depth, replay buffer, observability budget, worker counts, and tick budget all matter.

### 5. Operational truth matters as much as semantic truth

A system that preserves semantics but lies about pressure or lifecycle behavior is still untrustworthy.

### 6. Boundedness is mandatory

If a buffer, history, queue, status surface, packet, or proof bundle can grow without declared bounds, it is a defect.

### 7. Certification must stay honest

A green result that hides observed failure is a lie.
Allowed failures are allowed, not erased.

### 8. Documentation is part of implementation

Each milestone ends with law docs and test matrix docs because “the tests imply the rules” is not good enough for this epic.

---

## Epic goals

The epic must produce an engine that is:

- deterministic in its authoritative baseline,
- explicit about what is authoritative and what is operational,
- bounded in RAM, CPU-adjacent pressure, queue depth, replay budget, observability budget, and worker use,
- truthful about runtime pressure and degradation,
- safe to start, run, persist, and stop,
- concurrency-safe under declared conditions,
- testable at subsystem, headless, and integrated levels,
- and certifiable with proof artifacts and release gates.

---

## Epic non-goals

This epic is not primarily about:

- rapidly expanding gameplay breadth,
- recreating the entire old RPG system first,
- building distributed infrastructure,
- building cluster workers,
- maximizing raw performance before control-law closure,
- adding decorative observability,
- or writing vague “quality” documentation without enforcement.

---

## Architectural map

## Configuration layer

The configuration layer defines the operating envelope.

### `src/config/profiles.py`

Defines `RuntimeProfile` and `HardwareClass`.

Profile fields cover:

- profile identity,
- hardware class,
- RAM limit,
- CPU target,
- max worker count,
- max queue depth,
- max work debt,
- replay buffer cap,
- observability budget cap,
- tick budget,
- degradation thresholds.

This file is the core statement of what the runtime is allowed to consume.

### `src/config/validation.py`

Defines startup validation rules and illegal flag/profile combinations.
This is the beginning of lifecycle truth.

---

## Core model layer

The core layer defines authoritative state, authoritative deltas, work identity, governance signals, and packet/result contracts.

### `src/core/state.py`

Contains `EntityState` and `AuthoritativeState`.

`AuthoritativeState` includes fields such as:

- tick,
- seed,
- world time,
- entities,
- global resources,
- periodic due ticks,
- work debt,
- RNG checkpoint.

This is the canonical semantic state.

### `src/core/updates.py`

Contains `EntityUpdate` and `StateUpdate`.
This is the authoritative delta surface used by the apply path.

### `src/core/work.py`

Defines `WorkClass` and `WorkItem`.

Current work classes include:

- `CRITICAL`,
- `PERIODIC`,
- `OPPORTUNISTIC`,
- `DEFERRED`.

This is the root of scheduling and work-law reasoning.

### `src/core/governance.py`

Defines:

- `RuntimeMode`,
- `PressureSignals`,
- and mode-related supporting types.

This is the root of degradation/recovery reasoning.

---

## Engine layer

The engine layer is where orchestration, mutation, selection, checkpointing, replay, and worker execution live.

### `src/engine/kernel.py`

The `Kernel` is the runtime orchestrator.

Its job is to:

- move ticks forward,
- gather work,
- invoke local or worker execution,
- apply authoritative deltas,
- advance operational state,
- collect monitoring,
- and coordinate lifecycle behavior.

The kernel is allowed to orchestrate.
It is not allowed to become the hidden owner of every subsystem rule.

### `src/engine/scheduler.py`

The scheduler selects work.

It must define exact ordering and exact class semantics.
It must not mutate authoritative state.

### `src/engine/apply.py`

The apply path is the sole authoritative mutator.

This is one of the most important files in the whole epic.
If mutation leaks outside this path, the trust model is broken.

### `src/engine/checkpoint.py`

Canonical checkpointing and authoritative hashing live here.

This module must remain external to the state models themselves and must operate only on authoritative material.

### `src/engine/worker_manager.py`

Owns bounded worker execution control:

- submission,
- inflight limits,
- collection,
- timeout behavior,
- and fallback coordination.

This module is a runtime-control boundary, not just a thin thread-pool wrapper.

---

## Replay layer

The replay layer is operational, not authoritative.

### `src/replay/replay.py`

Owns:

- bounded staging,
- chunk rotation,
- overflow handling,
- sink interaction,
- and finalization hooks.

Replay must never redefine authoritative truth.
It is support infrastructure that must remain bounded and honest.

### `src/replay/manifest.py`

Owns the replay bundle structure and manifest integrity.

This module matters because a replay directory that merely exists is not enough.
The bundle must be structurally checkable.

---

## Observability layer

The observability layer is operational and bounded.

### `src/observability/signals.py`

Owns runtime-signal collection and bounded history/trend logic.

### `src/observability/runtime_status.py`

Owns the surfaced runtime/lifecycle/control-state snapshot.

This is not supposed to be a vanity dashboard.
It is supposed to be the truthful operational surface of the engine.

---

## Governance layer

### `src/governance/governor.py`

Owns degradation, recovery, hysteresis, and policy interpretation from signals.

The governor must be driven by real signals.
A governor driven by fake or weak signals is fake safety.

---

## Certification layer

### `src/certification/models.py`

Defines:

- measurement points,
- scenario expectations,
- failure kinds,
- result models,
- proof metadata.

### `src/certification/conformance.py`

Owns pass/fail judgment from scenario expectations and measured results.

### `src/certification/harness.py`

Owns scenario execution and measurement capture.

### `src/certification/recorder.py`

Owns proof artifact output.

This layer is not just “test support.”
It is the claim system.

---

## Trust boundaries

These boundaries must stay explicit.

### Authoritative

Authoritative means:

- changes define semantic engine truth,
- changes affect checkpoint/hash identity,
- changes matter for equivalence and reproducibility.

Examples:

- entity state,
- global resources,
- periodic due ticks,
- work debt if authoritative,
- authoritative RNG checkpoint.

### Non-authoritative but operationally important

Operational means:

- can influence runtime behavior,
- can influence degradation,
- can influence scheduling or policy,
- but must not directly contaminate authoritative hash identity.

Examples:

- runtime mode,
- pressure history,
- replay state,
- worker counters,
- inflight counts,
- lifecycle status,
- certification metadata.

### Observational only

Observational means:

- recorded for monitoring, tests, or proof support,
- not allowed to become semantic truth accidentally.

Examples:

- measurement stream,
- runtime snapshots,
- proof-bundle status,
- release-bundle metadata.

---

## Testing philosophy

The test strategy is law-first, not feature-first.

That means tests are primarily trying to prove:

- exact contract boundaries,
- deterministic behavior,
- boundedness,
- fault handling,
- purity of authoritative state,
- and honesty of proof/reporting.

The test universe should be read as a proof stack:

1. core semantic law,
2. runtime-control law,
3. lifecycle law,
4. concurrency law,
5. certification law.

---

## The milestone sequence

The correct sequence is:

**A -> B -> C -> Attach Gate 1 -> D -> E**

That sequence exists because each milestone depends on the previous one’s truth.

---

# Milestone A — Core Runtime Completion and Contract Closure

## Purpose

Milestone A closes the deterministic single-process baseline.

This milestone is not about adding new capability.
It is about making the existing kernel, scheduler, apply path, and checkpoint model fully real.

## What A must prove

- exact kernel phase order,
- exact authoritative apply boundary,
- exact work ordering,
- exact checkpoint purity,
- no hidden mutation paths,
- no placeholder baseline semantics,
- complete core-law tests,
- exact baseline runtime docs.

## What A does not do

- no replay hardening,
- no real signal hardening,
- no worker deepening,
- no certification broadening,
- no RPG attachment.

## Main risks in A

- pretending frozen dataclasses equal true immutability,
- relying on incidental Python ordering,
- allowing kernel orchestration to hide mutation or ordering logic,
- leaving placeholder scheduler behavior in baseline law.

## Done means done for A

A is done when the local path is the unquestioned semantic baseline and all baseline runtime law is exact, documented, and test-pinned.

---

# Milestone B — Real Runtime Signals and Governor Hardening

## Purpose

Milestone B closes runtime truth.

This is the milestone where monitoring, degradation, recovery, and runtime status stop being decorative and become operationally trustworthy.

## What B must prove

- exact signal catalog,
- real queue/worker/replay/debt/tick/memory pressure accounting,
- bounded signal history,
- exact degradation and recovery law,
- exact anti-thrashing behavior,
- exact scheduler-policy integration,
- governance-state isolation from checkpoints,
- truthful runtime-status surface.

## What B does not do

- no replay lifecycle finalization hardening,
- no worker deepening,
- no RPG attachment,
- no full certification expansion.

## Main risks in B

- blended vague “utilization” fields,
- fake metrics driving real policy,
- recovery logic based on intuition instead of law,
- governance fields bleeding into authoritative identity.

## Done means done for B

B is done when every mode-driving signal is real, bounded, and explicitly defined, and when the governor is a trustworthy control layer instead of a rough heuristic.

---

# Milestone C — Replay, Startup, Shutdown, and Operational Integrity

## Purpose

Milestone C closes lifecycle integrity.

This is where the engine becomes safe to start, persist, snapshot, and stop under contract.

## What C must prove

- strict startup validation,
- bounded replay staging,
- explicit overflow behavior,
- exact chunk rotation,
- exact manifest integrity,
- explicit sink-pressure behavior,
- bounded runtime snapshots,
- deterministic shutdown order,
- timeout-bounded non-authoritative flush,
- final authoritative hash/checkpoint survival under replay trouble,
- lifecycle truth and partial-success semantics.

## What C does not do

- no worker deepening,
- no gameplay widening,
- no certification universe deepening except what lifecycle proof needs.

## Main risks in C

- treating replay as harmless output,
- allowing “best effort” shutdown language,
- making final authoritative truth depend on replay success,
- vague operational status.

## Done means done for C

C is done when startup, replay, runtime snapshots, shutdown, and final authoritative emission all obey one exact lifecycle law.

---

# Attach Gate 1 — First real RPG slice

## Earliest safe attach point

The first real RPG slice should land **after Milestone C**.

Not before.

## Why after C

Because before C:

- runtime truth is not fully closed,
- lifecycle integrity is not fully closed,
- and attaching domain logic would make engine-contract bugs and gameplay bugs overlap.

## What the first slice should be

A thin deterministic vertical slice.

Recommended first slice:

- movement,
- or another small interaction that is easy to reason about,
- with local execution,
- authoritative apply,
- replay trace,
- monitoring,
- and headless proof.

## What it should not be

Not combat first.
Not quest webs.
Not broad inventory chains.
Not rich AI first.

Those multiply side effects too early.

---

# Milestone D — Bounded Concurrency That Can Be Trusted

## Purpose

Milestone D closes trusted concurrency.

This is the milestone where the worker path becomes legitimate for real domain execution.

## What D must prove

- exact worker packet contract,
- exact worker result contract,
- exact authoritative commit order independent of race timing,
- bounded worker-manager behavior,
- exact failure and timeout taxonomy,
- bounded and visible fallback,
- exact local-vs-concurrent equivalence for supported work,
- truthful concurrency status surface,
- headless concurrent system proof.

## What D does not do

- no distributed workers,
- no cluster scheduler,
- no broad gameplay explosion,
- no full certification closure.

## Main risks in D

- mistaking thread-pool existence for concurrency trust,
- letting completion timing leak into authoritative order,
- treating fallback as invisible recovery,
- attaching broad gameplay before packet/result/failure law is closed.

## Done means done for D

D is done when the supported concurrent path is no longer placeholder-only and when local-vs-concurrent equivalence is proven for the declared supported slice.

---

# Milestone E — Certification, Proof, and Release Trust

## Purpose

Milestone E closes the trust story.

This is where the engine becomes able to say exactly what it proves, under what conditions, and with what artifacts.

## What E must prove

- explicit certification scenario matrix,
- exact scenario expectation model,
- complete certification failure taxonomy,
- honest allowed-failure semantics,
- exact equivalence and reproducibility claims,
- bounded measurement/sampling law,
- complete proof-bundle structure,
- meaningful release gate,
- subsystem/headless/full-system certification layers,
- documentation of final claim scope.

## What E does not do

- no new runtime architecture,
- no gameplay expansion for its own sake,
- no vague “quality” marketing claims.

## Main risks in E

- treating certification as only end-to-end tests,
- allowing scenario names to overclaim,
- hiding bad news behind allowlists,
- letting proof bundles become decorative,
- existence-only release gates.

## Done means done for E

E is done when the engine can make precise, bounded, scenario-defined trust claims and back them with exact proof artifacts and release blocking rules.

---

## When real RPG logic attaches

There are three levels of “attached to RPG logic.”

### Level 1 — Thin attach

After Milestone C.

One narrow deterministic slice attached to the local/runtime seam.

### Level 2 — Trusted worker attach

During Milestone D.

The supported concurrent path becomes trustworthy enough for bounded real domain execution.

### Level 3 — Certified trust attach

After Milestone E.

The integrated engine can make exact proof-backed claims about the attached domain slice under declared conditions.

---

## Recommended first RPG slice

The first real RPG slice should be:

- deterministic movement,
- readiness-gated action execution,
- simple blocked/unblocked movement,
- authoritative position update,
- replay trace,
- local-vs-worker parity on supported conditions,
- headless test coverage.

### Why movement first

Because it gives you:

- visible authoritative change,
- clear packet/result/apply flow,
- low side-effect complexity,
- easier equivalence proof,
- easier profile-bound execution.

### Why not combat first

Combat multiplies:

- targeting,
- damage,
- collisions,
- side effects,
- death state,
- inventory interactions,
- and order disputes.

That is too much complexity before the execution seam is proven.

---

## Cross-cutting engineering rules

These rules apply to every milestone.

### Rule 1 — No placeholder law in completed scope

If the milestone claims a law is complete, there must be no placeholder semantics left in that law surface.

### Rule 2 — No hidden mutation

If a module is not the apply path, it does not get to mutate authoritative state.

### Rule 3 — No silent boundedness violations

If something is bounded, overflow behavior must be explicit.

### Rule 4 — No decorative metrics

A surfaced metric must have exact meaning.

### Rule 5 — No equivalence overclaim

Only claim equivalence for the exact supported slice and exact mode/profile/scope.

### Rule 6 — No allowed-failure dishonesty

A whitelist is not a magic eraser.

### Rule 7 — No doc drift

Docs and tests must describe the same law.

---

## Required documentation per milestone

Every milestone must end with two doc classes:

### 1. Law document

The law document defines:

- purpose,
- scope,
- exact rules,
- exact boundaries,
- non-goals,
- completion guarantees.

### 2. Test matrix document

The test matrix defines:

- test groups,
- input conditions,
- expected rule,
- regression caught,
- category of coverage.

The project must not treat “passing tests exist somewhere” as enough.

---

## Required guardrails per milestone

Each milestone should add regression guardrails such as:

- doc/test integrity checks,
- placeholder guards,
- focused CI targets,
- schema integrity checks,
- boundedness regression checks,
- contract-consistency tests.

The goal is not process theater.
The goal is to make trust-surface decay visible and cheap to catch.

---

## Test layering model

The test universe should be deliberately layered.

### Unit/contract tests

Used for:

- packet law,
- result law,
- apply law,
- checkpoint law,
- signal law,
- expectation-model law.

### Subsystem tests

Used for:

- scheduler/governor interactions,
- replay behavior,
- lifecycle boundaries,
- worker manager behavior,
- proof-bundle integrity.

### Headless engine tests

Used for:

- tick-loop scenarios,
- lifecycle scenarios,
- degradation/recovery scenarios,
- supported local-vs-concurrent equivalence.

### Full proof/certification tests

Used for:

- scenario execution,
- conformance evaluation,
- proof-bundle emission,
- release gate behavior.

Each layer should prove something distinct.

---

## Operational truth model

The engine needs a small, exact operational truth surface.

This should include fields such as:

- current profile,
- current mode,
- current tick,
- memory RSS,
- memory trend,
- tick compute time,
- rolling tick average,
- queue utilization,
- worker utilization,
- active workers,
- work debt,
- deferred count,
- dropped-work count,
- fallback count,
- replay backlog,
- replay drop count,
- replay flush failure count,
- worker failure count,
- last mode transition,
- startup state,
- shutdown state,
- final authoritative hash if available,
- partial-success markers.

Every field must define:

- source,
- cadence,
- instant vs cumulative vs rolling meaning,
- reset behavior,
- whether it affects law or is monitoring-only.

---

## Lifecycle truth model

Lifecycle must be explicitly represented.

Example lifecycle states:

- not started,
- startup validating,
- startup failed,
- running,
- degraded running,
- replay backpressured,
- shutdown started,
- flush in progress,
- flush timed out,
- flush failed,
- shutdown complete,
- shutdown complete with non-authoritative failure.

This is not decorative status.
This is the external truth of what the engine is doing.

---

## Failure taxonomy philosophy

Failure classes should be:

- small in number,
- exact,
- non-overlapping where possible,
- honest about authoritative vs operational impact,
- and useful for proof and debugging.

Examples across the epic:

- reporting incomplete,
- telemetry gap,
- envelope failure,
- degradation sequence failure,
- recovery timeout,
- semantic drift,
- reproducibility failure,
- startup rejection,
- replay overflow,
- sink failure,
- manifest incomplete,
- release gate block,
- worker timeout,
- worker invalid result,
- fallback used,
- partial-success lifecycle completion.

The taxonomy should remain stable enough to reason about and narrow enough to stay meaningful.

---

## Anti-patterns to avoid

These are the failure modes most likely to poison the epic.

### 1. Architecture worship

Do not mistake presence of modules for completion of guarantees.

### 2. Hidden convenience mutation

Do not let a helper mutate authoritative structures “temporarily.”

### 3. Accidental determinism

Do not treat Python insertion order or executor submission order as contractual law unless explicitly frozen and tested.

### 4. Decorative observability

Do not surface metrics that sound good but do not mean anything exact.

### 5. Best-effort shutdown vagueness

Do not use that phrase as a substitute for defined finalization law.

### 6. Fallback invisibility

Fallback is not “success.”
Fallback is a classified runtime event that must remain visible.

### 7. Overclaiming equivalence

Only prove what you have actually proven.

### 8. Overexpanding gameplay too early

More domain logic before runtime trust closure is fake progress.

### 9. Decorative proof bundles

A directory full of files is not proof.

### 10. Planning as avoidance

The milestone map is now detailed enough.
More planning beyond this starts to become delay.

---

## Recommended execution model for the team

For each milestone:

1. freeze the law set,
2. freeze the scope boundary,
3. identify placeholders inside the claimed law surface,
4. harden the code path,
5. add direct proof tests,
6. refactor responsibility leakage,
7. write the milestone docs,
8. add regression guardrails.

That is the correct loop.

Not:

- write broad code first,
- hope tests cover it,
- and explain the rules later.

---

## Ownership model

Suggested responsibility ownership across the epic:

### Runtime contract owner

Owns:

- phase order,
- apply-path law,
- scheduler law,
- checkpoint purity,
- authoritative boundaries.

### Runtime control owner

Owns:

- signals,
- governor,
- anti-thrashing,
- scheduler-policy integration,
- runtime status truth.

### Lifecycle owner

Owns:

- startup validation,
- replay boundedness,
- sink-pressure behavior,
- manifest integrity,
- shutdown order,
- final authoritative emission.

### Concurrency owner

Owns:

- packet/result law,
- worker manager,
- fallback law,
- commit ordering,
- equivalence proof.

### Certification owner

Owns:

- scenario matrix,
- expectation model,
- conformance law,
- proof bundles,
- release gate,
- claim-scope documentation.

One person can own multiple areas in practice, but the boundary must remain explicit.

---

## Definition of done for the whole epic

The epic is complete only when all of these are true:

- Milestone A baseline semantics are exact and closed,
- Milestone B runtime signals and governor behavior are exact and truthful,
- Milestone C lifecycle integrity is exact and bounded,
- first real RPG slice is attached after C,
- Milestone D concurrent execution is exact and trustworthy for the supported slice,
- Milestone E certification and release truth are exact and honest,
- docs and tests match across all milestone law surfaces,
- and the engine can make exact claims about what is proven and what is not.

---

## Short roadmap summary

### Sequence

- Milestone A
- Milestone B
- Milestone C
- Attach Gate 1
- Milestone D
- Milestone E

### Earliest first real RPG slice

After Milestone C.

### Earliest real trusted worker-based RPG logic

During Milestone D.

### Earliest point where the integrated runtime can make exact proof-backed claims

After Milestone E.

---

## What should happen next

The next useful move is not more roadmap discussion.

The next useful move is:

- execute Milestone A,
- write the A law docs,
- close mutation-path ambiguity,
- freeze phase order,
- freeze scheduler order,
- close checkpoint purity,
- and complete the baseline core-law test suite.

That is the first hard gate.
Everything else depends on it.

---

## Final engineering truth

The project already has enough architecture.
It already has enough planning.
It already has enough milestone detail.

The constraint is no longer “what are we building?”
The constraint is “can we stop lying to ourselves about what is actually closed?”

That is the entire epic.

The engine becomes trustworthy only when:

- the baseline is exact,
- the runtime tells the truth,
- the lifecycle is safe,
- concurrency is bounded and proven,
- and certification says exactly what is true and nothing more.
