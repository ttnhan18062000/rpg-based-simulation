Here is the updated high-level v2 plan, corrected to match the **actual state of the implemented code**, not the milestone documents on paper.

This version assumes the truth we already established:

- the architecture is mostly present,
- the subsystem boundaries are mostly right,
- but too many guarantees are still partial, placeholder-driven, or weakly enforced,
- so the plan now needs to focus on **completion, hardening, and proof**, not more fine-grained milestone slicing.

---

# High-level v2 plan — from credible prototype to trustworthy engine

This plan replaces the earlier 10 small milestone model with **5 larger completion milestones**.

The goal is no longer to “introduce” subsystems.
Those subsystems already exist. The goal now is to make them:

- real,
- complete,
- test-pinned,
- pressure-trustworthy,
- and usable without hidden caveats.

This plan is shaped by the current implementation reality:

- core architecture exists,
- bounded-state discipline exists,
- replay/governor/scheduler/workers/certification all exist,
- but the engine still has incomplete signals, placeholder enforcement, weak worker contracts, partial shutdown hardening, shallow certification, and unfinished law tests.

---

# Milestone A — Core Runtime Completion and Contract Closure

### Description

Finish the deterministic single-process runtime so the core engine stops being “architecturally correct but partially implemented.”

This milestone exists because the kernel, apply path, scheduler, and authoritative-state model are already present, but key guarantees are still incomplete or only partially proven.

### Technical implementation

Complete and harden:

- kernel phase execution
- authoritative apply path
- scheduler/work-class semantics
- deterministic checkpointing
- authoritative/non-authoritative state boundaries
- periodic/deferred work semantics
- all missing or placeholder law tests

This milestone must explicitly eliminate:

- unfinished core-law tests
- ambiguous work ordering
- placeholder deterministic assumptions
- hidden mutation paths
- milestone-compressed orchestration that masks missing guarantees

### Important notes

Do not add new capabilities here.

This milestone is about making the existing kernel and work model **fully real**.

The main question is no longer “does the subsystem exist?”
It is “is the contract actually enforced?”

### Testing requirements

Add or complete:

- authoritative apply-order tests
- deterministic checkpoint tests
- kernel phase-order tests
- work-class ordering tests
- deferred-work safety tests
- no-hidden-mutation tests

### Acceptance criteria

The single-process engine path is fully deterministic, fully contract-pinned, and free of unfinished core-law behavior.

### Checklist

- [ ] Finish all unfinished core-law tests
- [ ] Remove placeholder logic from kernel execution
- [ ] Freeze deterministic work ordering fully
- [ ] Harden authoritative apply path
- [ ] Prove checkpoint determinism
- [ ] Eliminate hidden state mutation paths
- [ ] Document the completed runtime law set

---

# Milestone B — Real Runtime Signals and Governor Hardening

### Description

Turn runtime protection from “mostly there” into “operationally trustworthy.”

This milestone exists because the governor architecture is correct, but several pressure signals and surfaced operational values are still incomplete, placeholder-based, or too weak to support hard confidence.

### Technical implementation

Complete and harden:

- real queue utilization reporting
- real dropped-work accounting
- real worker/inflight pressure reporting
- real replay pressure reporting
- bounded signal history and trends
- governor mode transitions against actual signals
- anti-thrashing behavior
- policy-to-scheduler integration

This milestone must explicitly eliminate:

- hardcoded zero-value runtime signals
- decorative observability fields
- weak pressure inference
- ambiguous degradation/recovery behavior
- scheduler-policy coupling that changes semantics

### Important notes

Do not treat observability as separate from runtime protection.

If the governor reads fake or partial signals, then the safety model is fake too.

### Testing requirements

Add or harden:

- real-signal governor tests
- anti-thrashing tests
- degradation-order tests
- scheduler-boundary tests under policy
- signal-boundedness tests
- no-governance-state contamination tests

### Acceptance criteria

The governor runs on real bounded signals, sheds only declared cost, recovers deterministically, and does not depend on placeholder telemetry.

### Checklist

- [ ] Replace placeholder operational metrics
- [ ] Complete bounded signal-history model
- [ ] Harden governor transition logic
- [ ] Prove degradation order on real signals
- [ ] Prove deterministic recovery behavior
- [ ] Keep governance outside authoritative state
- [ ] Document real runtime-pressure semantics

---

# Milestone C — Replay, Startup, Shutdown, and Operational Integrity

### Description

Finish the operational lifecycle so the engine can start, persist, and stop under contract instead of best-effort behavior.

This milestone exists because replay and operational controls are structurally present, but shutdown enforcement, sink-pressure handling, startup guarantees, and operational truthfulness are still incomplete.

### Technical implementation

Complete and harden:

- replay staging and overflow policy
- chunk rotation and manifest integrity
- replay sink-pressure handling
- startup validation and safe flag enforcement
- deterministic shutdown sequence
- real timeout-bounded non-authoritative flush behavior
- final authoritative checkpoint emission
- bounded runtime snapshots and surfaced status

This milestone must explicitly eliminate:

- vague “fire-and-forget” behavior
- best-effort shutdown semantics
- operational fields that look real but are placeholders
- loose startup-validation language
- replay lifecycle ambiguity

### Important notes

Replay and shutdown are not secondary concerns.

The old system already proved that persistence and end-of-run behavior can become resource hazards. This milestone exists to prevent that from happening again.

### Testing requirements

Add or harden:

- replay overflow/drop tests
- sink-pressure tests
- manifest integrity tests
- startup-validation tests
- operational-flag boundary tests
- shutdown timeout tests
- authoritative hash emission tests

### Acceptance criteria

The engine can start, run, persist, and shut down safely under the declared contract without relying on comments, hope, or best-effort fallbacks.

### Checklist

- [ ] Harden replay staging and chunk rotation
- [ ] Harden manifest integrity
- [ ] Implement real sink-pressure behavior
- [ ] Enforce startup config validity strictly
- [ ] Implement real shutdown timeout handling
- [ ] Emit final authoritative checkpoint reference
- [ ] Freeze operational status model and docs

---

# Milestone D — Bounded Concurrency That Can Be Trusted

### Description

Move worker execution from bounded prototype to serious execution mode.

This milestone exists because concurrency already exists, but its correctness still depends on thin packet/result contracts, weak assumptions, and incomplete failure semantics.

### Technical implementation

Complete and harden:

- worker packet contract
- worker result contract
- explicit commit-order law
- explicit one-result-per-entity rule or richer commit identity
- worker failure handling
- fallback-to-local semantics
- queue and inflight enforcement
- worker metrics and pressure reporting
- local-vs-concurrent authoritative equivalence proof

This milestone must explicitly eliminate:

- underspecified commit ordering
- ambiguous packet context ordering
- weak fallback semantics
- hidden concurrency assumptions
- “probably equivalent” worker behavior

### Important notes

This milestone is not about maximizing throughput.

It is about making concurrency safe enough to trust.

If bounded concurrency cannot preserve authoritative equivalence, it is not a feature. It is a defect source.

### Testing requirements

Add or harden:

- packet-shape tests
- result-shape tests
- one-result-per-entity contract tests or richer commit-order tests
- worker failure tests
- queue/inflight saturation tests
- fallback equivalence tests
- local-vs-worker deterministic equivalence tests

### Acceptance criteria

Concurrent execution stays within declared bounds, commits deterministically, fails safely, and produces the same authoritative outcome as local execution under supported conditions.

### Checklist

- [ ] Tighten packet/result contracts
- [ ] Freeze deterministic commit law
- [ ] Harden fallback-to-local behavior
- [ ] Add worker failure semantics
- [ ] Prove concurrent/local authoritative equivalence
- [ ] Surface real worker pressure metrics
- [ ] Document safe concurrency contract

---

# Milestone E — Certification, Proof, and Production Readiness

### Description

Turn the engine from a hardened implementation into a provably trustworthy system under declared profiles.

This milestone exists because the certification harness already exists, but it is still too shallow to be the final word on safety, recovery, and semantic equivalence.

### Technical implementation

Complete and harden:

- scenario expectation model
- deterministic baseline binding
- conformance evaluation depth
- recovery and hysteresis certification
- degradation-order certification
- semantic-drift certification
- structured failure taxonomy
- profile/scenario/hardware-class report integrity
- documentation-lawbook/playbook finalization
- CI-enforced terminology and doc alignment

This milestone must explicitly eliminate:

- weak conformance heuristics
- shallow recovery checks
- ambiguous failure reasons
- universal performance language
- documentation-code terminology drift
- confidence based on “green tests” without evidence quality

### Important notes

Certification is not benchmarking.

It is proof.

This milestone is complete only when the engine can demonstrate:

- profile conformance,
- safe degradation,
- safe recovery,
- deterministic equivalence where required,
- and honest hardware-bound throughput reporting.

### Testing requirements

Add or harden:

- certification determinism tests
- degradation-before-failure tests
- recovery-window tests
- structured failure-kind tests
- hardware-class override/reporting tests
- report-language integrity tests
- documentation/playbook integrity tests

### Acceptance criteria

The engine has a real proof system, real documentation-law alignment, and production-readiness claims that are evidence-backed rather than aspirational.

### Checklist

- [ ] Deepen scenario/conformance model
- [ ] Harden baseline-vs-certified equivalence proof
- [ ] Expand structured failure taxonomy
- [ ] Bind reports to profile/scenario/hardware class
- [ ] Add report-language compliance checks
- [ ] Finalize playbook/lawbook and CI guardrails
- [ ] Certify engine under supported profiles honestly

---

## Recommended implementation order

1. Milestone A — Core Runtime Completion and Contract Closure
2. Milestone B — Real Runtime Signals and Governor Hardening
3. Milestone C — Replay, Startup, Shutdown, and Operational Integrity
4. Milestone D — Bounded Concurrency That Can Be Trusted
5. Milestone E — Certification, Proof, and Production Readiness

This order is the right one because it follows reality:

- first make the core law real,
- then make runtime signals and control real,
- then make lifecycle behavior safe,
- then make concurrency trustworthy,
- then prove the whole thing under pressure.

Anything else is backwards.

---

## What changes in execution discipline under this v2 plan

Across all milestones:

- no milestone is complete while core placeholders remain
- no subsystem counts as done because the file exists
- docs, tests, and enforcement must close together
- every milestone must end in a genuinely more usable engine state
- proof and hardening are part of milestone completion, not cleanup

---

## Final delivery condition

This v2 plan is complete only when all of the following are true:

- the single-process path is fully deterministic and contract-pinned,
- the governor acts on real bounded signals,
- replay and shutdown are hardened operational paths,
- worker mode is bounded and authoritative-equivalent,
- certification produces trustworthy structured evidence,
- and docs, code, tests, and reports all speak the same law set.

---

## Priority Plan

What must change in mindset or assumptions
Stop planning around subsystem introduction. Plan around subsystem completion, enforcement, and proof.

What actions must be taken immediately
Move to the 5 larger milestones above. Treat each milestone as a completion gate, not a documentation exercise. Use the current codebase as the baseline and drive out placeholders, weak contracts, and shallow proofs in that order.

What must stop or be eliminated
Stop slicing work into tiny milestone fragments. Stop counting file presence as progress. Stop deferring hardening and evidence to “later.”

The consequences and opportunity cost if you fail
You will keep producing elegant architecture on paper while the engine remains a half-finished prototype in practice. That is the exact trap this v2 plan is meant to avoid.

Next I’d turn this into the detailed implementation plan for **Milestone A** in the same format as before.
