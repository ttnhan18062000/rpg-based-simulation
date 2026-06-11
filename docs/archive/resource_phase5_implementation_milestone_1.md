---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

Below is the detailed Phase 5 implementation plan in the same structure as before.

# Detailed Implementation Plan — Phase 5 of `src`

This plan assumes Phase 4 has already moved `src` into a materially better state, but that the branch still has unfinished truth and progression-loop work.

Phase 5 is not a broad expansion phase.

It is the phase where the project must recover the next missing part of the original RPG-core loop and prove that the new runtime is still building the same game in progression terms.

The core loop this phase is trying to recover is:

- deterministic movement,
- bounded loot and harvest interaction,
- inventory pressure,
- town-based resource resolution,
- blocker and lead generation,
- and repeatable resource-seeking progression.

This document expands the high-level Phase 5 plan into implementation-ready milestone detail using the same milestone and task structure as the earlier plans.

---

# [Milestone 1] - Phase 4 Exit Closure and Phase 5 Readiness

## [Milestone Description]

Milestone 1 is the gate between the current Phase 4 branch state and legitimate Phase 5 work.

Its purpose is to make sure Phase 5 does not inherit unresolved truth debt from Phase 4.

By this point, the branch may already have:

- stronger movement behavior,
- a bounded resource interaction slice,
- improved replay behavior,
- and stronger code-focused tests.

That is not enough.

This milestone exists because Phase 5 should not proceed while:

- parity proof still lives outside the standard validation path,
- release-truth artifacts are broken or incomplete,
- support claims remain ambiguous,
- or the resource contract still advertises things it does not really govern.

This milestone does not introduce new gameplay.
It closes the previous phase honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 5.

This milestone must complete the exit-closure work for the current supported slices and truth surfaces in five areas:

1. **Movement proof closure**
   - movement parity must be part of the normal proof path,
   - not just helper scripts or side validation tools.

2. **Resource interaction proof closure**
   - the current resource interaction slice must gain initial old-`src` differential proof where preservation is required.

3. **Release-truth closure**
   - docs, manifest, and release-proof artifacts must exist and match the code/test expectations again.

4. **Support-boundary closure**
   - current supported movement and resource-interaction scope must be explicit and publishable.

5. **Resource-contract closure**
   - any declared resource contract that is still only partially real must either be completed or narrowed honestly.

This milestone must not:

- widen gameplay breadth,
- introduce town systems before the gate is closed,
- or use partial green test numbers as a substitute for phase completion.

## [Milestone important notes]

The trap here is treating “better than before” as phase-ready.

That is how teams carry unresolved ambiguity into the next layer and then spend the next phase compensating for earlier dishonesty.

This milestone succeeds only if Phase 5 starts from a branch that can describe its current supported slices and proof status without evasive language.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- movement parity is enforced in the normal validation flow,
- resource interaction has at least initial differential validation against original `src`,
- release-truth surfaces are restored,
- support boundaries are explicit,
- resource-contract ambiguity is resolved or narrowed honestly,
- and the branch has an explicit “Phase 5 ready” gate.

---

## Task

### [ ] (checkbox) - [Task 1] - Promote movement parity verification into the standard proof/test path

#### [Task Description]

Take the existing movement parity work and turn it into an ordinary validation requirement instead of an optional side workflow.

#### [Task technical implementation]

Move movement verification from script-oriented support into a standard `tests` gate.

This task should:

- reuse current movement oracle fixtures where possible,
- normalize movement expectations against original `src`,
- run parity assertions under pytest,
- and make failures visible in normal CI/test execution.

Ensure the supported movement scope stays narrow and literal:

- grid movement,
- blocked movement,
- occupancy behavior,
- dead-actor behavior,
- and any explicitly supported edge cases.

#### [Task possible affected files]

- `tests/parity/test_movement_parity.py`
- `tests/gameplay/test_movement_contract.py`
- `tests/gameplay/parity/*`
- existing movement oracle helpers
- CI/test target configuration

#### [Task important notes]

Do not keep the official movement slice in a second-class proof path.

#### [Task check list]

- [ ] Existing oracle capture is reused or stabilized
- [ ] Parity assertions are executed by default test flow
- [ ] Supported movement scope is explicit
- [ ] Failures are visible in standard CI/local runs
- [ ] Movement support docs reference the same proof path

#### [Task acceptance criteria]

Movement parity is enforced as part of the normal validation model for the official movement slice.

---

### [ ] (checkbox) - [Task 2] - Add initial differential validation for the current resource interaction slice against original `src`

#### [Task Description]

Introduce the first old-vs-new proof layer for resource interaction behavior.

#### [Task technical implementation]

Build initial characterization and differential tests for supported resource-interaction cases:

- harvest completion,
- loot completion,
- slot-full failure,
- weight-full failure,
- interruption/reset behavior,
- and supported depletion/respawn behavior where parity is intended.

Compare original `src` outcomes to `src` outcomes for the declared supported subset only.

Record intentional differences explicitly rather than silently absorbing them into the new contract.

#### [Task possible affected files]

- `tests/parity/test_resource_interaction_parity.py`
- comparison fixtures against original `src`
- divergence log docs
- gameplay parity support helpers

#### [Task important notes]

Do not declare the resource interaction slice “preserved” until the old-vs-new comparison exists.

#### [Task check list]

- [ ] Supported parity scope is frozen
- [ ] Normal cases are compared
- [ ] Blocked/failure cases are compared
- [ ] Depletion/respawn behavior is compared where required
- [ ] Intentional mismatches are recorded

#### [Task acceptance criteria]

The current supported resource interaction slice has initial old-vs-new differential proof where preservation is required.

---

### [ ] (checkbox) - [Task 3] - Restore or regenerate missing release/documentation proof artifacts and integrity checks

#### [Task Description]

Bring the release/documentation truth surface back into sync with the actual repository state.

#### [Task technical implementation]

Restore or regenerate the required files and integrity expectations currently expected by the release/doc tests.

This includes:

- required manifest files,
- required handbook or playbook files,
- required release-proof directory expectations,
- and any missing documentation artifacts referenced by tests.

Make sure the docs are not placeholders that contradict current support reality.

#### [Task possible affected files]

- `docs/engine/manifest.json`
- `docs/engine/engineering_playbook_m10.md`
- `CONTRIBUTING.md`
- release proof docs
- docs integrity tests

#### [Task important notes]

Green engine tests with broken release truth still means the branch is not phase-ready.

#### [Task check list]

- [ ] Missing required docs are restored
- [ ] Manifest aligns with real release expectations
- [ ] Integrity tests pass
- [ ] Docs do not overclaim support
- [ ] Release artifacts align with current branch truth

#### [Task acceptance criteria]

The release/documentation truth surface is restored and consistent with the actual supported branch state.

---

### [ ] (checkbox) - [Task 4] - Reconfirm and publish the current support boundary for movement and resource interaction

#### [Task Description]

Package the current official support surface clearly before Phase 5 extends it.

#### [Task technical implementation]

Publish or refresh one support-boundary package covering:

- supported movement behavior,
- supported resource interaction behavior,
- supported execution modes,
- supported profile/hardware scope if relevant,
- known limitations,
- and declared exclusions.

This package should become the reference input for Phase 5 design decisions.

#### [Task possible affected files]

- `docs/engine/phase4_exit_support_boundary.md`
- support surface docs
- benchmark/certification claim docs
- divergence log

#### [Task important notes]

A vague support boundary guarantees Phase 5 drift.

#### [Task check list]

- [ ] Movement support is explicit
- [ ] Resource interaction support is explicit
- [ ] Execution mode scope is explicit
- [ ] Known limitations are explicit
- [ ] Unsupported behavior is explicit

#### [Task acceptance criteria]

The branch has one explicit support boundary for the supported slices entering Phase 5.

---

### [ ] (checkbox) - [Task 5] - Resolve remaining declared-resource contract ambiguity such as CPU-governance scope

#### [Task Description]

Stop carrying resource-contract language that the runtime does not actually fulfill.

#### [Task technical implementation]

Audit declared resource contract fields and decide, for each ambiguous element, whether Phase 5 starts with:

- full implementation,
- explicit temporary exclusion,
- or narrowed claim wording.

CPU is the most obvious current example.
Either:

- thread CPU through runtime snapshot, pressure signals, governor interpretation, measurement points, and conformance,
  or
- explicitly narrow the support claim so CPU is not presented as a governed truth surface yet.

#### [Task possible affected files]

- `src/observability/*`
- `src/certification/*`
- `src/config/profiles.py`
- support docs
- resource contract docs/tests

#### [Task important notes]

Do not carry decorative contract fields into the next phase.

#### [Task check list]

- [ ] Declared resource fields are audited
- [ ] CPU-governance decision is explicit
- [ ] Runtime truth matches declared scope
- [ ] Conformance scope matches declared scope
- [ ] Docs and tests use the same language

#### [Task acceptance criteria]

The resource contract entering Phase 5 is either fully real for supported items or explicitly narrowed.

---

### [ ] (checkbox) - [Task 6] - Freeze the Phase 4 exit package: support status, proof status, known limitations, and declared divergences

#### [Task Description]

Close Phase 4 with one truth package that Phase 5 can depend on.

#### [Task technical implementation]

Publish a concise package describing:

- supported slices,
- proof status,
- benchmark status,
- lifecycle/replay status,
- known limitations,
- and declared divergences from original `src`.

This should be short enough to review and strong enough to stop Phase 5 from reopening Phase 4 arguments casually.

#### [Task possible affected files]

- `docs/engine/phase4_exit_package.md`
- milestone review docs
- divergence log
- support boundary docs

#### [Task important notes]

Do not use Phase 5 planning to hide unresolved Phase 4 limitations.

#### [Task check list]

- [ ] Supported slices are listed
- [ ] Proof status is listed
- [ ] Limitations are listed
- [ ] Divergences are listed
- [ ] Package matches actual code/tests

#### [Task acceptance criteria]

Phase 4 ends with one explicit truth package the next phase can build on.

---

### [ ] (checkbox) - [Task 7] - Publish the formal “Phase 5 ready” gate

#### [Task Description]

Turn the previous tasks into one explicit entry decision.

#### [Task technical implementation]

Create one review gate that requires:

- movement parity in the standard proof path,
- initial resource differential proof,
- release/doc truth restored,
- support boundary published,
- resource contract ambiguity resolved or narrowed,
- and the Phase 4 exit package completed.

#### [Task possible affected files]

- `docs/engine/phase5_readiness_gate.md`
- review checklist docs
- CI/release gate docs

#### [Task important notes]

This is the line between “still cleaning Phase 4” and “actually entering Phase 5.”

#### [Task check list]

- [ ] Gate conditions are explicit
- [ ] Gate conditions are test-backed where possible
- [ ] Approval criteria are reviewable
- [ ] Known limitations are attached
- [ ] Phase 5 entry is no longer ambiguous

#### [Task acceptance criteria]

The branch has a precise, reviewable, and honest entry gate for Phase 5.
