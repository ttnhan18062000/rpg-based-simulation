Blunt answer:

**We do not need to finish every v2 milestone before attaching to real RPG logic.**
But we **do** need to finish enough of the runtime milestones that attaching RPG logic does not contaminate the engine with fake safety and fake correctness.

Right now, the worker path is still placeholder-level. In `default_simulation_worker`, the “simulation” is just a readiness reduction, not real domain logic. That means full RPG attachment now would be premature. See [all_src.py](sandbox:/mnt/data/all_src.py).

## High-level milestone path until real RPG attachment

### Milestone A — Core runtime contract closure

Goal: make the single-process kernel actually trustworthy.

What must be true before moving on:

- phase order is frozen
- authoritative apply path is final and deterministic
- no hidden mutation paths remain
- deferred and periodic work semantics are explicit
- checkpoint hashing is stable

Why this comes first:
Without this, any RPG logic you add sits on top of a runtime that still lies about its own guarantees.

What this gives you:

- correctness foundation
- testable kernel
- stable headless baseline

This is the first hard gate.

---

### Milestone B — Real runtime signals and governor hardening

Goal: make monitoring and protection real, not decorative.

What must be true before moving on:

- queue pressure is real
- inflight worker pressure is real
- dropped work is real
- replay pressure is real
- governor transitions respond to actual signals
- degradation and recovery are deterministic

Why this matters before RPG attachment:
You said you care about:

- correctness
- performance and optimization
- fault tolerance
- no crash / monitoring / profiles

You cannot honestly work on any of those while the runtime signals are partly estimated or placeholder-driven.

What this gives you:

- real operational observability
- real profile enforcement
- real degradation logic

This is the second hard gate.

---

### Milestone C — Replay, startup, shutdown, operational integrity

Goal: make the engine safe to start, run, persist, and stop.

What must be true before moving on:

- replay overflow policy is real
- sink-pressure handling is real
- final checkpoint/hash emission is real
- shutdown timeout handling is real
- startup validation is strict
- surfaced runtime status is truthful

Why this matters before RPG attachment:
Because once real RPG logic lands, crashes and shutdown corruption become much more expensive and much harder to debug.

What this gives you:

- fault containment at lifecycle level
- survivable headless execution
- reliable CI/system-test behavior

This is the third hard gate.

---

## Attach Gate 1 — First real RPG slice

This is the **earliest safe point** to attach real RPG logic.

Not full RPG.
A **thin vertical slice**.

That slice should be:

- deterministic movement or interaction
- packet -> worker/local execution -> result -> authoritative apply
- replay trace
- profile monitoring
- fault-injection tests
- local vs worker equivalence tests

Why not combat first:
Combat multiplies complexity fast:

- targeting
- collisions
- damage
- death state
- side effects
- ordering disputes

Movement is the cleanest first slice because it proves the execution seam without exploding the state space.

So the earliest answer is:

**After Milestones A, B, and C, attach the first thin real RPG slice.**

---

### Milestone D — Bounded concurrency that can be trusted

Goal: move from placeholder worker execution to real bounded domain execution.

What must be true here:

- packet contract is tight
- result contract is tight
- commit order is explicit
- worker failure semantics are explicit
- fallback-to-local is safe
- local vs worker authoritative equivalence is proven

This is where the engine becomes ready for:

- real worker-based RPG logic
- concurrent entity actions
- bounded domain execution under profiles

So this is the milestone for **full runtime attachment of real RPG logic**, not just a thin slice.

Meaning:

- after A+B+C: first thin RPG attachment
- during/after D: real bounded RPG execution model

---

### Milestone E — Certification, proof, production readiness

Goal: prove the attached RPG engine is trustworthy under declared profiles.

What must be true here:

- scenario model is deep enough
- failure taxonomy is structured
- conformance checks are real
- semantic drift checks are real
- degradation/recovery proof is real
- profile/scenario/hardware class reporting is honest

This milestone is **not required to begin attachment**.
It **is required** before you claim the integrated RPG engine is production-trustworthy.

So:

- not needed to start real attachment
- needed to finish the trust story

See the milestone structure in [resource_high_level_v2.md](sandbox:/mnt/data/resource_high_level_v2.md).

## The actual plan in one line

**A -> B -> C -> attach first thin RPG slice -> D -> expand to full bounded RPG execution -> E for proof and production readiness**

## What “attached to real RPG logic” should mean

There are three levels. Do not blur them.

### Level 1 — seam attachment

Real domain logic exists in one narrow path.
Example:

- entity move decision
- blocked/unblocked move
- authoritative position update
- replay and monitoring

Earliest safe point: **after C**

### Level 2 — runtime attachment

Real domain logic is part of normal worker/local execution.
Example:

- movement
- basic interactions
- deterministic neighbor-aware decisions
- bounded fallback when workers fail

Earliest safe point: **during D**

### Level 3 — production-trustworthy attachment

Real RPG logic is covered by profile-based proof.
Example:

- full headless certification
- degradation/recovery proof
- structured failure reporting
- honest hardware/profile claims

Earliest safe point: **after E**

## What I would use as the milestone wording

### Milestone A

Close the kernel contract.

### Milestone B

Make runtime signals and monitoring honest.

### Milestone C

Make lifecycle and operational failure handling safe.

### Attach Gate 1

Integrate one thin deterministic RPG slice.

### Milestone D

Make concurrent RPG execution safe and equivalent.

### Milestone E

Prove the integrated engine under real profiles.

## What not to do

Do not wait until E before touching RPG logic. That is too late and too abstract.

Do not attach full RPG logic right now. That is too early and reckless.

Do not start with combat. Start with movement or one simple interaction loop.

## My recommendation

Use this as the practical target:

**We attach the first real RPG slice immediately after Milestone C.**
**We attach the full bounded real RPG execution model in Milestone D.**
**We call it trustworthy only after Milestone E.**

## Priority Plan

**What you must change in mindset or assumptions**
Stop treating “attach to real RPG logic” as one binary event. It is three stages: first slice, full bounded execution, then certified trust.

**What actions you must take immediately**
Drive A, B, and C as hard gates. Define the first slice now: deterministic movement through packet/result/apply/replay/monitoring/headless tests.

**What you must stop or eliminate**
Stop thinking gameplay expansion is the next milestone. The next milestone is runtime truth. Stop treating placeholder worker behavior as a valid attach point.

**The consequences and opportunity cost if you fail to change**
You will bolt RPG complexity onto a runtime that still has partial signals and thin failure semantics. That will make every later bug harder to isolate, harder to certify, and harder to optimize.

Next useful move: turn this into a milestone checklist with exact “done means done” gates for A, B, C, Attach Gate 1, D, and E.
