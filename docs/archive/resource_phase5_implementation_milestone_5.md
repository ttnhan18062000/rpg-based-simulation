# [Milestone 5] - Supported Progression Surface Consolidation

## [Milestone Description]

Milestone 5 consolidates the supported surface after the progression loop has been recovered to the declared extent.

Its purpose is to stop the branch from remaining a pile of supported subsystems and turn it into one explicit supported progression package.

This is the milestone where the branch should be able to state, precisely:

- what progression behavior is officially supported,
- under what profiles and modes,
- with what lifecycle and replay guarantees,
- with what benchmark and certification coverage,
- and with what preserved original behavior vs intentional divergence.

## [Milestone technical implementation]

Create one progression-surface consolidation layer that unifies:

- support boundaries,
- benchmark boundaries,
- certification boundaries,
- release-gate boundaries,
- documentation language,
- and progression-loop claim scope.

This milestone must complete:

1. **Support matrix closure**
   - exact supported progression loop,
   - exact exclusions,
   - exact execution-mode meaning.

2. **Benchmark closure**
   - integrated progression scenarios,
   - scoped performance meaning,
   - no universal claims.

3. **Certification closure**
   - integrated progression proof scenarios,
   - honest lifecycle and recovery meaning.

4. **Release-truth closure**
   - release gates and proof bundles reflect the real supported progression loop.

5. **Claim-scope closure**
   - docs, reports, and release truth say the same thing.

This milestone must not widen into unsupported future systems.

## [Milestone important notes]

The trap here is overclaim after real progress.

This phase will likely make the branch substantially stronger.
That is exactly when people start speaking too broadly.

This milestone exists to stop that.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- the supported progression surface is explicit,
- benchmark and certification matrices cover the declared loop,
- release expectations match supported gameplay truth,
- preserved vs divergent original behavior is explicit,
- and the branch can end Phase 5 with one coherent support package.

---

## Task

### [ ] (checkbox) - [Task 1] - Define the supported progression-surface matrix for the current `src_v2` phase

#### [Task Description]

Create the official support matrix for the integrated progression loop.

#### [Task technical implementation]

Define and publish the matrix covering:

- supported movement behavior,
- supported resource interaction behavior,
- supported town resolution behavior,
- supported blocker/hint/lead behavior,
- supported execution modes,
- supported profile or hardware scope where relevant,
- and explicit exclusions.

#### [Task possible affected files]

- `docs/engine/supported_progression_surface_phase5.md`
- support boundary docs
- milestone review docs

#### [Task important notes]

This matrix is the truth surface, not a roadmap wishlist.

#### [Task check list]

- [ ] Supported behaviors are explicit
- [ ] Execution-mode scope is explicit
- [ ] Profile/hardware scope is explicit where relevant
- [ ] Exclusions are explicit
- [ ] Matrix matches real proof scope

#### [Task acceptance criteria]

The project has one exact support matrix for the current supported progression loop.

---

### [ ] (checkbox) - [Task 2] - Expand certification scenarios to cover the integrated supported progression loop

#### [Task Description]

Make certification prove the actual supported progression loop, not just engine structure.

#### [Task technical implementation]

Add certification scenarios for:

- gather → return → resolve,
- inventory pressure under supported constraints,
- blocker/lead emission under supported conditions,
- supported local execution,
- supported concurrent execution where officially allowed,
- and lifecycle-active progression scenarios where relevant.

Keep scenario claims narrow and literal.

#### [Task possible affected files]

- `src_v2/certification/scenarios.py`
- certification models
- progression certification tests
- certification docs

#### [Task important notes]

Do not certify broader progression behavior than the support matrix actually covers.

#### [Task check list]

- [ ] Integrated progression scenarios exist
- [ ] Execution-mode scenarios exist where relevant
- [ ] Lifecycle scenarios exist where relevant
- [ ] Scenario expectations remain scoped
- [ ] Certification matches support truth

#### [Task acceptance criteria]

Certification now directly proves the declared supported progression loop.

---

### [ ] (checkbox) - [Task 3] - Expand benchmark scenarios to cover the integrated supported progression loop

#### [Task Description]

Make performance measurement reflect the real supported gameplay loop.

#### [Task technical implementation]

Add benchmark scenarios for:

- supported gather-and-return loops,
- supported town-resolution loops,
- supported blocker/lead generation loops,
- local execution,
- and supported concurrent execution where officially allowed.

Benchmark outputs must remain scoped by:

- scenario,
- profile,
- hardware class where relevant,
- and execution mode.

#### [Task possible affected files]

- benchmark scenario definitions
- performance harness
- benchmark docs
- regression reporting

#### [Task important notes]

Do not benchmark unsupported progression just because it exists in partial code paths.

#### [Task check list]

- [ ] Integrated progression benchmarks exist
- [ ] Local benchmark variants exist
- [ ] Concurrent variants exist where relevant
- [ ] Outputs remain scoped
- [ ] Results are reproducible enough for regression use

#### [Task acceptance criteria]

Benchmark coverage now reflects the supported integrated progression loop instead of isolated slice behavior.

---

### [ ] (checkbox) - [Task 4] - Integrate supported progression truth into release-gate expectations and proof bundle requirements

#### [Task Description]

Make release truth depend on progression-loop proof once the loop is officially supported.

#### [Task technical implementation]

Update release-gate and proof-bundle expectations so they require:

- integrated supported progression proof targets,
- manifest alignment with current support matrix,
- report coverage for the supported progression loop,
- and no implication of unsupported future systems.

#### [Task possible affected files]

- release-gate tests
- `docs/engine/manifest.json`
- proof bundle docs
- release docs

#### [Task important notes]

Once progression support is official, release proof must include it.

#### [Task check list]

- [ ] Progression proof targets are represented
- [ ] Manifest aligns with current support truth
- [ ] Required artifacts reflect supported progression
- [ ] Unsupported systems are not implied
- [ ] Release docs match gate logic

#### [Task acceptance criteria]

Release-gate expectations now include real proof coverage for the supported progression loop.

---

### [ ] (checkbox) - [Task 5] - Consolidate report language and proof language around supported progression claims

#### [Task Description]

Make all output language match the real support boundary.

#### [Task technical implementation]

Tighten:

- certification markdown,
- proof summaries,
- support docs,
- benchmark summaries,
- and release language

so they all say exactly:

- what progression behavior is supported,
- under what conditions,
- what original behavior is preserved,
- what is divergent,
- and what remains unsupported.

#### [Task possible affected files]

- certification recorder/report modules
- support docs
- benchmark docs
- release docs
- lawbook/support docs

#### [Task important notes]

This is where accidental lying usually starts.

#### [Task check list]

- [ ] Supported claims are explicit
- [ ] Conditions are explicit
- [ ] Preserved behavior is explicit
- [ ] Divergences are explicit
- [ ] Unsupported areas are explicit

#### [Task acceptance criteria]

All proof and report language matches the real supported progression surface without overclaim.

---

### [ ] (checkbox) - [Task 6] - Add progression-surface regression guards for parity, determinism, lifecycle, and proof integrity

#### [Task Description]

Protect the supported progression surface from silent erosion.

#### [Task technical implementation]

Add or strengthen guards for:

- integrated parity drift,
- determinism drift,
- lifecycle drift,
- support-boundary drift,
- proof/report drift,
- and release-target drift.

Use the same law-style discipline already used elsewhere in V2.

#### [Task possible affected files]

- regression tests
- docs integrity tests
- certification integrity tests
- release-gate tests
- CI config

#### [Task important notes]

The phase fails if the supported progression loop can still drift silently.

#### [Task check list]

- [ ] Parity drift is guarded
- [ ] Determinism drift is guarded
- [ ] Lifecycle drift is guarded
- [ ] Proof/report drift is guarded
- [ ] Release-target drift is guarded

#### [Task acceptance criteria]

The supported progression surface is protected against silent regression across code, proof, and release truth.

---

### [ ] (checkbox) - [Task 7] - Publish the supported progression package: matrix, boundaries, known limitations, preserved behavior, and declared divergences

#### [Task Description]

Package the current supported progression surface into one canonical truth artifact.

#### [Task technical implementation]

Publish one package containing:

- support matrix,
- support boundaries,
- supported execution modes,
- lifecycle guarantees,
- benchmark scope,
- certification scope,
- preserved original behavior,
- declared divergences,
- known limitations,
- and unsupported areas.

This package should become the canonical answer to:
“What progression behavior does `src_v2` currently support and prove?”

#### [Task possible affected files]

- `docs/engine/supported_progression_package_phase5.md`
- support matrix docs
- benchmark docs
- certification docs
- release docs

#### [Task important notes]

This package is about current truth, not future ambition.

#### [Task check list]

- [ ] Matrix is included
- [ ] Boundaries are included
- [ ] Lifecycle guarantees are included
- [ ] Preserved vs divergent behavior is included
- [ ] Known limitations and unsupported areas are included

#### [Task acceptance criteria]

The current supported progression surface is published as one coherent, reviewable, supportable truth package.

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
