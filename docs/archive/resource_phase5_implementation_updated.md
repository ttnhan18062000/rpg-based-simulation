# [Milestone 5 Updated] - Supported Progression Surface Consolidation

## [Milestone Description]

Milestone 5 is **not** a documentation wrap-up anymore.

Based on the current `src` verification state, this milestone is now the closure phase for a branch that has a mostly working progression runtime but an unclosed support surface, an incomplete proof surface, and release artifacts that do not yet match reality.

The branch is close enough to overclaim and not close enough to deserve it.

This updated milestone exists to force Phase 5 to end honestly.

The project must leave this milestone able to state, without hand-waving:

- what progression behavior is actually supported,
- what progression behavior is explicitly excluded,
- what original `src` behavior is preserved,
- what divergences are accepted,
- what execution modes are supported,
- what proof and benchmark surfaces exist,
- and what release artifacts are required to make those claims true.

## [Milestone technical implementation]

Create one final progression-surface closure layer that unifies:

- code truth,
- parity truth,
- certification truth,
- benchmark truth,
- release-gate truth,
- and documentation truth.

This updated milestone must first close the current blockers before support-package publication is allowed.

This milestone must complete:

1. **Behavior closure**
   - resolve the currently broken town-entry resolution contract,
   - normalize progression item/resource identifiers,
   - and ensure the declared supported loop is internally coherent.

2. **Support matrix closure**
   - exact supported progression loop,
   - exact exclusions,
   - exact execution-mode meaning,
   - and exact preserved-vs-divergent behavior.

3. **Parity closure**
   - integrated old-vs-new progression proof,
   - real oracle capture where preservation is claimed,
   - and no fake parity through hand-authored expected outputs.

4. **Benchmark closure**
   - integrated progression scenarios,
   - scoped performance meaning,
   - and no universal or hardware-free claims.

5. **Certification closure**
   - integrated progression proof scenarios,
   - lifecycle and recovery meaning,
   - and mode-scoped certification truth.

6. **Release-truth closure**
   - required docs, manifests, and proof bundles match the actual supported loop.

7. **Claim-scope closure**
   - docs, reports, release gates, and milestone outputs all say the same thing.

This milestone must not widen into unsupported future systems.

## [Milestone important notes]

The current danger is not lack of code.

The danger is lying by implication.

The branch already has enough working structure to tempt broad claims. That is exactly why Milestone 5 must now be a closure milestone, not a celebration milestone.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- the supported progression loop is internally coherent,
- the support matrix matches real implementation and proof scope,
- parity expectations are honest and reproducible,
- benchmark and certification surfaces cover the declared supported loop,
- release artifacts enforce the same truth,
- and the branch can publish one coherent Phase 5 support package without overclaim.

---

## Task

### [x] (checkbox) - [Task 1] - Close the prerequisite behavior gaps that currently invalidate the declared supported progression loop

#### [Task Description]

Repair or formally de-scope the concrete behavior gaps that currently make the supported progression loop internally inconsistent.

#### [Task technical implementation]

Close the following blockers first:

- implement the missing sell-on-entry behavior in `src/engine/town_resolution.py` **or**
  explicitly remove that claim from the supported loop and adjust all dependent tests/docs,
- normalize item and resource identifiers across progression systems so the supported loop uses one canonical namespace,
- verify that town return, inventory, blacksmith/shop interaction, and progression scenarios all consume the same canonical identifiers,
- remove any support claims that depend on behavior not actually implemented.

Current known hotspots include:

- `src/engine/town_resolution.py`
- `src/engine/interaction_system.py`
- `src/engine/blacksmith_system.py`
- `src/engine/shop_system.py`
- progression scenario definitions and tests that depend on resource naming and town resolution semantics

#### [Task possible affected files]

- `src/engine/town_resolution.py`
- `src/engine/interaction_system.py`
- `src/engine/blacksmith_system.py`
- `src/engine/shop_system.py`
- progression loop tests
- parity scenario files
- support docs

#### [Task important notes]

Do not move into truth-packaging while the loop still contradicts itself.

A supported loop with a false town contract is not supported. It is mislabeled.

#### [Task check list]

- [x] Town-entry resolution behavior is either implemented or explicitly removed from support claims
- [x] Resource/item identifiers are canonical across the supported progression loop
- [x] Progression scenarios use the same canonical identifiers
- [x] Dependent tests reflect the chosen behavior truth
- [x] No support claim remains for behavior that is not actually implemented

#### [Task acceptance criteria]

The declared supported progression loop is internally coherent and no longer relies on contradictory runtime behavior.

---

### [x] (checkbox) - [Task 2] - Define the supported progression-surface matrix for the current `src` phase

#### [Task Description]

Create the official support matrix for the integrated progression loop based on verified reality, not intended architecture.

#### [Task technical implementation]

Define and publish the matrix covering:

- supported movement behavior,
- supported resource interaction behavior,
- supported town resolution behavior,
- supported blocker/hint/lead behavior,
- supported execution modes,
- supported profile or hardware scope where relevant,
- preserved original behavior where parity is claimed,
- declared divergences,
- and explicit exclusions.

The matrix must reflect the closed behavior from Task 1 and the actual proof surfaces from later tasks.

#### [Task possible affected files]

- `docs/engine/supported_progression_surface_phase5.md`
- support boundary docs
- milestone review docs
- divergence log docs

#### [Task important notes]

This matrix is the truth surface, not a roadmap, not a wishlist, and not a branch morale tool.

#### [Task check list]

- [x] Supported behaviors are explicit
- [x] Execution-mode scope is explicit
- [x] Profile/hardware scope is explicit where relevant
- [x] Preserved original behavior is explicit
- [x] Divergences are explicit
- [x] Exclusions are explicit
- [x] Matrix matches real proof scope

#### [Task acceptance criteria]

The project has one exact support matrix for the current supported progression loop and it matches actual implementation and proof truth.

---

### [x] (checkbox) - [Task 3] - Repair and complete integrated parity proof for the supported Phase 5 progression loop

#### [Task Description]

Make integrated parity proof real, reproducible, and honest.

#### [Task technical implementation]

Repair parity infrastructure by:

- fixing parity tests that currently fail collection due to incorrect module-level skip usage,
- generating or committing required oracle artifacts so parity can run in a clean validation path,
- replacing hand-authored town oracle expectations with real old-`src` characterization/capture where preservation is claimed,
- documenting every accepted divergence instead of letting mismatches float as implied intent,
- ensuring integrated progression parity compares equivalent scenarios and authoritative outcomes.

This task must close the current parity integrity gap between “we compared behavior” and “we manually wrote what we hoped parity would be.”

#### [Task possible affected files]

- `tests/parity/test_movement_parity.py`
- `tests/parity/test_resource_interaction_parity.py`
- `tests/parity/town_oracle/capture_src_town.py`
- parity oracle artifacts
- divergence docs
- integrated parity tests

#### [Task important notes]

`src` is the behavior oracle. Hand-authored expected outputs are not a substitute for characterization.

#### [Task check list]

- [x] Parity collection succeeds in the normal validation path
- [x] Required oracle artifacts are reproducible and available
- [x] Old-`src` capture is used where preservation is claimed
- [x] Accepted divergences are documented explicitly
- [x] Integrated progression parity compares authoritative outcomes, not vague summaries

#### [Task acceptance criteria]

Integrated old-vs-new parity proof is executable, reproducible, scoped, and honest for the declared supported progression loop.

---

### [x] (checkbox) - [Task 4] - Expand certification scenarios to cover the integrated supported progression loop

#### [Task Description]

Make certification prove the actual supported progression loop, not just subsystem existence.

#### [Task technical implementation]

Add or tighten certification scenarios for:

- gather → return → resolve,
- inventory pressure under supported constraints,
- blocker/lead emission under supported conditions,
- supported local execution,
- supported concurrent execution only where officially allowed,
- lifecycle-active progression scenarios where relevant,
- and recovery/fallback truth where progression support depends on it.

Use the integrated progression scenario as the baseline certification target and ensure it matches the support matrix exactly.

#### [Task possible affected files]

- `src/certification/scenarios.py`
- certification models
- progression certification tests
- certification docs

#### [Task important notes]

Do not certify broader progression behavior than the support matrix actually covers.

Green certification with inflated wording is still a lie.

#### [Task check list]

- [x] Integrated progression scenarios exist
- [x] Execution-mode scenarios exist where relevant
- [x] Lifecycle scenarios exist where relevant
- [x] Recovery/fallback meaning is explicit where relevant
- [x] Scenario expectations remain scoped
- [x] Certification matches support truth

#### [Task acceptance criteria]

Certification directly proves the declared supported progression loop and says nothing broader than the support matrix allows.

---

### [x] (checkbox) - [Task 5] - Expand benchmark scenarios to cover the integrated supported progression loop

#### [Task Description]

Make performance measurement reflect the real supported progression loop instead of isolated slice behavior.

#### [Task technical implementation]

Add benchmark scenarios for:

- supported gather-and-return loops,
- supported town-resolution loops,
- supported blocker/lead generation loops,
- supported local execution,
- and supported concurrent execution where officially allowed.

Benchmark outputs must remain scoped by:

- scenario,
- profile,
- hardware class where relevant,
- execution mode,
- and reproducibility conditions.

Tie the benchmark harness to the same integrated progression scenario family used by certification where appropriate.

#### [Task possible affected files]

- benchmark scenario definitions
- `src/perf/bench_harness.py`
- benchmark docs
- regression reporting

#### [Task important notes]

Do not benchmark unsupported progression just because partial code paths exist.

Do not turn benchmark presence into universal performance claims.

#### [Task check list]

- [x] Integrated progression benchmarks exist
- [x] Local benchmark variants exist
- [x] Concurrent variants exist where relevant
- [x] Outputs remain scoped
- [x] Results are reproducible enough for regression use
- [x] Benchmark docs state scope and non-goals explicitly

#### [Task acceptance criteria]

Benchmark coverage reflects the supported integrated progression loop instead of isolated subsystem behavior, and benchmark claims remain explicitly scoped.

---

### [x] (checkbox) - [Task 6] - Integrate supported progression truth into release-gate expectations and proof bundle requirements

#### [Task Description]

Make release truth depend on progression-loop proof once the loop is officially supported.

#### [Task technical implementation]

Update release-gate and proof-bundle expectations so they require:

- integrated supported progression proof targets,
- manifest alignment with the current support matrix,
- report coverage for the supported progression loop,
- required Phase 5 support docs,
- and no implication of unsupported future systems.

Close the currently missing release-truth artifacts, including the required manifest and support-package-facing docs that the validation path expects.

#### [Task possible affected files]

- release-gate tests
- `docs/engine/manifest.json`
- `docs/engine/engineering_playbook_m10.md`
- `docs/engine/project_lawbook_m10.md`
- `CONTRIBUTING.md`
- proof bundle docs
- release docs

#### [Task important notes]

Once progression support is official, release proof must include it.

Missing required artifacts means the branch is not release-honest, no matter how much runtime code passes.

#### [Task check list]

- [x] Progression proof targets are represented
- [x] Manifest aligns with current support truth
- [x] Required artifacts exist
- [x] Required artifacts reflect supported progression scope
- [x] Unsupported systems are not implied
- [x] Release docs match gate logic

#### [Task acceptance criteria]

Release-gate expectations include real proof coverage for the supported progression loop and all required release-truth artifacts exist and align.

---

### [x] (checkbox) - [Task 7] - Consolidate report language and proof language around supported progression claims

#### [Task Description]

Make all output language match the real support boundary.

#### [Task technical implementation]

Tighten:

- certification markdown,
- proof summaries,
- support docs,
- benchmark summaries,
- release language,
- and milestone completion language

so they all say exactly:

- what progression behavior is supported,
- under what conditions,
- what original behavior is preserved,
- what is divergent,
- what remains unsupported,
- and what proof and benchmark surfaces actually exist.

#### [Task possible affected files]

- certification recorder/report modules
- support docs
- benchmark docs
- release docs
- lawbook/support docs
- milestone review docs

#### [Task important notes]

This is where accidental lying usually starts.

Do not use “supported” to mean “partially implemented.”
Do not use “parity” to mean “we wrote expectations ourselves.”
Do not use “benchmark covered” to mean “the harness exists.”

#### [Task check list]

- [x] Supported claims are explicit
- [x] Conditions are explicit
- [x] Preserved behavior is explicit
- [x] Divergences are explicit
- [x] Unsupported areas are explicit
- [x] Proof and benchmark surfaces are described literally

#### [Task acceptance criteria]

All proof and report language matches the real supported progression surface without overclaim or ambiguity.

---

### [x] (checkbox) - [Task 8] - Add progression-surface regression guards for parity, determinism, lifecycle, proof integrity, and release-target integrity

#### [Task Description]

Protect the supported progression surface from silent erosion.

#### [Task technical implementation]

Add or strengthen guards for:

- integrated parity drift,
- determinism drift,
- lifecycle drift,
- support-boundary drift,
- proof/report drift,
- oracle artifact drift,
- required-doc drift,
- and release-target drift.

Use the same law-style discipline already used elsewhere in V2.

This task must specifically ensure the normal validation path fails fast when:

- parity assets are missing,
- a supported-loop contract changes without matrix updates,
- release docs are missing,
- or proof/report text drifts away from implementation truth.

#### [Task possible affected files]

- regression tests
- docs integrity tests
- certification integrity tests
- release-gate tests
- CI config
- parity integrity tests

#### [Task important notes]

The phase fails if the supported progression loop can still drift silently.

#### [Task check list]

- [x] Parity drift is guarded
- [x] Determinism drift is guarded
- [x] Lifecycle drift is guarded
- [x] Proof/report drift is guarded
- [x] Oracle asset drift is guarded
- [x] Required-doc drift is guarded
- [x] Release-target drift is guarded

#### [Task acceptance criteria]

The supported progression surface is protected against silent regression across code, proof, docs, and release truth.

---

### [x] (checkbox) - [Task 9] - Publish the supported progression package: matrix, boundaries, known limitations, preserved behavior, and declared divergences

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
- unsupported areas,
- release-truth dependencies,
- and the exact answer to:
  “What progression behavior does `src` currently support and prove?”

#### [Task possible affected files]

- `docs/engine/supported_progression_package_phase5.md`
- support matrix docs
- benchmark docs
- certification docs
- release docs
- divergence docs

#### [Task important notes]

This package is about current truth, not future ambition.

Do not publish it until Tasks 1 through 8 are actually closed.

#### [Task check list]

- [x] Matrix is included
- [x] Boundaries are included
- [x] Lifecycle guarantees are included
- [x] Benchmark and certification scope are included
- [x] Preserved vs divergent behavior is included
- [x] Known limitations and unsupported areas are included
- [x] Release-truth dependencies are included

#### [Task acceptance criteria]

The current supported progression surface is published as one coherent, reviewable, supportable truth package.

---

## Shared Milestone Exit Checklist

The following are required close-out checks for this milestone.

- [x] Town-resolution support truth is closed
- [x] Resource/item namespace is canonicalized
- [x] Documentation updated
- [x] Divergence log updated
- [x] Regression guards added or updated where relevant
- [x] Support boundary declared or updated
- [x] Lifecycle impact reviewed
- [x] Certification/proof impact reviewed
- [x] Benchmark impact reviewed where applicable
- [x] Known limitations recorded
- [x] Original `src` parity impact reviewed where preservation is claimed
- [x] Required release-truth artifacts exist
- [x] Support matrix, certification, benchmark, and release language all match
