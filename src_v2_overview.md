# V2 Engine Epic Overview

## Purpose

This document explains, at a high level, what the V2 epic is, why it exists, what has already been implemented in `src_v2` and `tests_v2`, what the end goal is, and how the work is intended to progress from the start to completion.

This is the top-level orientation document for the V2 source and test effort.

---

## 1. Why this epic exists

The V2 epic exists because the engine needed a runtime that is:

- deterministic,
- profile-bounded,
- operationally truthful,
- concurrency-safe,
- lifecycle-safe,
- and certifiable.

The project is not just trying to “build another engine implementation.”
It is trying to build an engine that can make precise claims about:

- correctness,
- resource use,
- degradation behavior,
- recovery behavior,
- replay and shutdown behavior,
- concurrency equivalence,
- and release readiness.

The main lesson behind V2 is that architecture shape alone is not enough.

A system can look well-designed and still fail because:

- authoritative state boundaries are weak,
- runtime signals are fake or approximate,
- shutdown behavior is only best effort,
- concurrency is present but not trustworthy,
- or certification reports overclaim what the engine actually proves.

V2 exists to prevent that.

---

## 2. What V2 is trying to become

V2 is intended to become a trustworthy simulation runtime with these properties:

### Deterministic

Given the same:

- seed,
- authoritative inputs,
- runtime profile,
- and supported execution mode,

the engine must produce the same authoritative outcome where determinism is required.

### Authoritative

All semantic truth must live in authoritative state and pass through one authoritative apply path.

### Bounded

Runtime behavior must obey declared budgets, including:

- RAM,
- worker count,
- queue depth,
- replay buffer usage,
- observability overhead,
- tick budget,
- and work debt.

### Truthful

The engine must report operational pressure honestly:

- not decorative metrics,
- not hidden failures,
- not vague “best effort” behavior.

### Safe under lifecycle pressure

Startup, replay, snapshotting, finalization, and shutdown must all obey contract.

### Trustworthy under supported concurrency

The local path remains the semantic baseline, and concurrent execution must be treated as a bounded execution mode that is only trusted where equivalence is proven.

### Certifiable

The engine must emit machine-readable evidence and scoped human-readable reports that say exactly what was proven and under what conditions.

---

## 3. What “V2 source and tests” means

The V2 effort is implemented primarily through two parallel structures:

### `src_v2`

This contains the engine runtime itself:

- core models,
- configuration,
- engine loop,
- scheduling,
- apply path,
- governance,
- replay,
- runtime status,
- concurrency support,
- and certification support. :contentReference[oaicite:0]{index=0}

### `tests_v2`

This contains the law-oriented proof surface for the engine:

- profile contract tests,
- startup validation tests,
- authoritative state contract tests,
- scheduler and engine behavior tests,
- anti-thrashing and governor behavior tests,
- replay and shutdown tests,
- concurrency tests,
- certification tests,
- release-gate tests,
- and documentation integrity tests. :contentReference[oaicite:1]{index=1}

The point is not simply to “have tests.”
The point is to make the engine provable.

---

## 4. The starting design philosophy

From the beginning, the V2 effort has followed these ideas.

### 4.1 Single-process semantics first

The local single-process runtime is the baseline source of semantic truth.

That means:

- tick semantics,
- work ordering,
- authoritative mutation,
- and checkpoint/hash identity

must be frozen there first.

Everything else is layered on top of that.

### 4.2 One authoritative mutation path

The engine is designed so that authoritative changes do not happen everywhere.

They are supposed to flow through one authoritative apply path, rather than leaking through helpers, observability, replay, or workers.

### 4.3 Runtime profiles are real contract, not documentation

A profile is not a nice label.
It is supposed to define the resource envelope the runtime is allowed to use. :contentReference[oaicite:2]{index=2}

### 4.4 Runtime truth matters

If a governor reacts to fake or weak signals, then runtime protection is fake.
So V2 treats runtime signals, lifecycle outcomes, and proof artifacts as part of the trust surface.

### 4.5 Certification must stay honest

The engine must not hide observed failures behind green-looking output.
That is why V2 explicitly tracks allowed failures as observed failures rather than erasing them.

---

## 5. What we have now

The current V2 branch already contains a substantial amount of implemented structure.

## 5.1 Configuration and contract layer

The configuration layer already defines:

- `RuntimeProfile`,
- `HardwareClass`,
- profile validation rules,
- forbidden flags,
- contradictory startup conditions,
- and profile immutability expectations.

The tests already verify:

- valid profile creation,
- invalid profile rejection,
- profile immutability,
- forbidden flag rejection,
- contradictory replay/startup config rejection,
- and unsafe budget detection. :contentReference[oaicite:5]{index=5}

## 5.2 Authoritative core state

The engine already has explicit authoritative models such as:

- `AuthoritativeState`,
- `EntityState`,
- and authoritative update structures. :contentReference[oaicite:6]{index=6}

The tests verify that authoritative state stays clean and does not include observational or legacy contamination. :contentReference[oaicite:7]{index=7}

## 5.3 Runtime engine structure

The current V2 runtime includes:

- kernel orchestration,
- runtime modes,
- pressure signals,
- runtime status,
- scheduling,
- authoritative apply,
- replay support,
- and shutdown/finalization behavior. :contentReference[oaicite:8]{index=8}

## 5.4 Runtime control and anti-thrashing

The engine already has:

- explicit governor modes,
- recovery thresholds,
- dwell time,
- confidence windows,
- and anti-thrashing behavior.

The tests explicitly check:

- confidence-window-based recovery,
- recovery stabilization,
- and monotonic one-step recovery behavior. :contentReference[oaicite:10]{index=10}

## 5.5 Replay and lifecycle support

The runtime already includes replay infrastructure and lifecycle-aware shutdown behavior.
The newer branch also propagates shutdown outcome from the kernel into certification instead of relying on scenario-name simulation inside the harness. :contentReference[oaicite:11]{index=11}

This is an important change because lifecycle truth is part of the epic’s trust model.

## 5.6 Concurrency support

The runtime already includes a worker/concurrency seam.

The broader epic work established that:

- local execution is the semantic reference,
- concurrent execution is only supposed to be trusted for supported slices,
- and supported work must preserve authoritative ordering and equivalence under declared conditions.

The current direction is to keep that concurrency support narrow and provable rather than broad and speculative.

## 5.7 Certification and release-proof structure

The certification layer already exists in code:

- `MeasurementPoint`,
- `ScenarioExpectations`,
- `FailureKind`,
- `CertificationResult`,
- `ConformanceEvaluator`,
- `CertificationHarness`,
- `CertificationRecorder`,
- and scenario definitions. :contentReference[oaicite:12]{index=12}

The tests already verify:

- honest allowed-failure behavior,
- envelope violations,
- degradation-sequence failures,
- recovery failures,
- report language compliance,
- proof bundle existence,
- release-target binding,
- and release proof freshness/provenance checks. :contentReference[oaicite:13]{index=13}

---

## 6. What has already improved significantly

There has already been meaningful progress beyond the original skeleton.

### 6.1 Honest allowed failures

Whitelisted failures are now preserved honestly:

- `conformance_passed=True`
- real failure kind preserved
- `allowed_failure_observed=True`
- failure reason retained

That behavior is already implemented and tested.

### 6.2 Lifecycle-aware certification

The harness now derives lifecycle outcome from real kernel shutdown behavior instead of forcing it by scenario name. :contentReference[oaicite:15]{index=15}

### 6.3 Better runtime signal separation

The engine has moved toward using `worker_utilization` and `queue_utilization` explicitly rather than relying on one vague capacity metric in the certification and kernel paths. :contentReference[oaicite:16]{index=16}

### 6.4 Stronger recovery and conformance tests

The tests are not only checking happy paths.
They are also checking:

- recovery failures,
- lifecycle expectations,
- proof integrity,
- and scoped report language. :contentReference[oaicite:17]{index=17}

---

## 7. What is still not complete

This epic is not complete.

The architecture exists.
Many tests exist.
Some hardening is already real.

But several parts are still not fully closed.

## 7.1 Baseline semantic isolation is still not perfect

The engine still needs the single-process path to remain the unquestioned semantic source of truth without later concerns polluting that law surface.

## 7.2 Runtime truth still needs final cleanup

Even though runtime signals are much better than before, signal source-truth and schema consistency still need to be fully closed.

## 7.3 Lifecycle truth is improved but still being hardened

Certification now consumes lifecycle outcome from real shutdown behavior, which is a major improvement, but lifecycle semantics still need to be fully aligned and finalized.

## 7.4 Proof-bundle conventions still need discipline

The branch recently exposed exactly why proof bundle naming and artifact expectations must stay coherent across:

- recorder output,
- tests,
- and release-gate assumptions.

## 7.5 Real RPG attachment is still only beginning

The epic has been preparing the runtime so that it can support real RPG logic safely.
That process has started, but the official first attached slice still needs to be declared and proven under the engine’s contract.

---

## 8. The milestone structure of the epic

The entire epic has been organized around five completion milestones.

---

## Milestone A — Core Runtime Completion and Contract Closure

This milestone is about the deterministic single-process baseline.

Its job is to make sure:

- tick semantics are exact,
- phase order is exact,
- authoritative mutation is singular,
- work ordering is deterministic,
- checkpoint/hash behavior is authoritative-only,
- and baseline runtime law is fully test-pinned.

This milestone is not about adding new capability.
It is about making the base runtime unquestionably real.

---

## Milestone B — Real Runtime Signals and Governor Hardening

This milestone is about runtime truth.

Its job is to make sure:

- runtime signals are real,
- history is bounded,
- degradation and recovery are exact,
- anti-thrashing is proven,
- scheduler policy under pressure is declared,
- and runtime status tells the truth.

This is where “monitoring” becomes part of the safety model instead of just diagnostics.

---

## Milestone C — Replay, Startup, Shutdown, and Operational Integrity

This milestone is about lifecycle truth.

Its job is to make sure:

- startup rejects invalid conditions early,
- replay is bounded,
- overflow and sink pressure are explicit,
- manifest structure is meaningful,
- shutdown is deterministic and bounded,
- and final authoritative truth survives non-authoritative trouble.

This is where the engine becomes operationally trustworthy.

---

## Milestone D — Bounded Concurrency That Can Be Trusted

This milestone is about trustworthy supported concurrency.

Its job is to make sure:

- worker input/output contracts are exact,
- authoritative commit order does not depend on race timing,
- fallback is explicit and bounded,
- supported concurrent work is provably equivalent to the local baseline,
- and concurrent execution is only trusted where it is actually proven.

This is also the milestone where real RPG logic starts becoming legitimate on the worker path.

---

## Milestone E — Certification, Proof, and Release Trust

This milestone is about the engine’s claim system.

Its job is to make sure:

- scenario expectations are exact,
- failure taxonomy is explicit,
- allowed failures stay honest,
- equivalence/reproducibility claims are scoped,
- proof bundles are complete,
- and release gating depends on real proof, not decorative artifacts.

This is the milestone that turns “we think it works” into “we can state what it proves.”

---

## 9. The current strategic position

The epic has shifted over time.

At the beginning, the main problem was:

- build the architecture.

Now the main problem is:

- stop letting the strongest parts outrun the weakest parts.

Right now, the strongest areas are:

- certification structure,
- lifecycle-aware conformance,
- and bounded runtime hardening.

The weaker areas are:

- final semantic baseline closure,
- full runtime source-truth closure,
- final proof-bundle and release-gate consistency,
- and official first RPG slice attachment.

That means the epic is no longer blocked by “missing pieces.”
It is blocked by “unfinished closure.”

---

## 10. The first official RPG attach point

One of the key goals of the epic is to reach the point where real RPG behavior can be attached safely.

That does **not** mean “add all gameplay systems.”

It means attach one narrow, provable, deterministic domain slice first.

The correct first slice is:

- deterministic movement,
- or another equally narrow low-side-effect action.

Why movement first:

- it creates visible authoritative change,
- it exercises apply law,
- it fits local and supported concurrent proof,
- it is easier to certify,
- and it does not explode the state space the way combat or inventory chains would.

So the epic’s practical progression is:

- close substrate trust,
- then make movement the first official supported RPG slice,
- then broaden only one narrow slice at a time.

---

## 11. What success looks like

The epic is successful when the engine can truthfully say:

- this is the authoritative runtime model,
- this is the resource envelope,
- these are the exact startup/shutdown/replay rules,
- these runtime modes and recovery rules are real,
- this supported concurrent slice is proven equivalent to the baseline,
- these certification scenarios were executed,
- these failures were or were not observed,
- and this release is or is not allowed under those exact conditions.

That is the goal.

Not:

- “it mostly works,”
- “the architecture is there,”
- or “the tests look impressive.”

The goal is precise trust.

---

## 12. What must not happen

The epic should not drift into these mistakes:

### 12.1 More planning than execution

The milestone and epic structure are already detailed enough.
At this point, the risk is not lack of planning.
The risk is using planning as delay.

### 12.2 Broad gameplay before substrate trust

Adding combat, inventory webs, quest chains, or rich AI too early would create a bigger-looking codebase and a less trustworthy engine.

### 12.3 Decorative proof

A proof bundle directory is not enough.
Artifact existence without semantic integrity is fake trust.

### 12.4 Fake runtime truth

A governor using weak or decorative signals is not runtime protection.

### 12.5 Masked failures

Allowed failures must stay visible.
Green output that hides observed failure is not acceptable.

---

## 13. What should happen next

At a high level, the next work should continue in this order:

1. finish remaining contract repairs and lifecycle truth fixes,
2. finish baseline/runtime truth closure,
3. formalize the first official supported RPG slice,
4. prove it locally and under supported concurrency,
5. then broaden certification around that real attached slice.

That is the correct path.

---

## 14. Final summary

This epic is the implementation of a V2 engine runtime and proof system.

From the start, its purpose has been to build an engine that is:

- deterministic,
- bounded,
- operationally honest,
- lifecycle-safe,
- concurrency-safe under declared scope,
- and certifiable.

We already have a substantial V2 source and test base:

- runtime profiles,
- authoritative state,
- engine orchestration,
- governor behavior,
- replay/lifecycle support,
- certification models,
- proof reporting,
- release gating,
- and a large law-oriented test surface.

What remains is not “invent the architecture.”
What remains is:

- harden the remaining truth gaps,
- keep the proof system honest,
- and attach the first real RPG slice without breaking the trust model.

That is the epic from the start.
