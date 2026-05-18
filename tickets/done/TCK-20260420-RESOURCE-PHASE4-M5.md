# [Milestone 5] - Supported Gameplay Surface Consolidation

## [Milestone Description]

Milestone 5 is the consolidation milestone for the first real gameplay-support phase of `src`.

By the time this milestone starts, the project should already have:

- a frozen repaired substrate,
- one officially supported gameplay slice: deterministic grid movement,
- a second narrow supported gameplay slice: deterministic resource interaction core,
- benchmark and profiling foundations,
- and certification/proof infrastructure that is already capable of expressing scoped truth.

The purpose of this milestone is to stop the project from becoming “a pile of supported slices” and instead turn it into one **explicit supported gameplay surface**.

This milestone is where the engine begins to say, precisely:

- what gameplay behavior is officially supported,
- under what profiles,
- under what execution modes,
- with what lifecycle guarantees,
- with what benchmark expectations,
- and with what certification and release-proof coverage.

This milestone does **not** widen the engine into broad combat, quest systems, rich AI, or full inventory graphs.

This milestone exists to consolidate the current supported gameplay surface into one coherent, publishable, testable, benchmarkable, and certifiable support package.

## [Milestone technical implementation]

Create one gameplay-support consolidation layer that unifies:

- support boundaries,
- certification scenarios,
- benchmark scenarios,
- proof bundle expectations,
- release-gate expectations,
- and public internal claim scope for the currently supported gameplay slices.

This milestone must complete these things:

1. **Support matrix closure**
   - define the exact current gameplay surface,
   - define which slices are official,
   - define local-only vs supported concurrent behavior,
   - define profile/hardware expectations where relevant,
   - and define what old-`src` behavior is preserved versus intentionally divergent.

2. **Integrated certification closure**
   - certification must now cover not only engine-only scenarios,
   - but also integrated gameplay scenarios using the official supported slices.

3. **Integrated benchmark closure**
   - benchmark scenarios must now include real supported gameplay loops,
   - not only idle or engine-only benchmark cases.

4. **Release-proof closure**
   - release-gate logic and proof bundle expectations must reflect real supported gameplay proof,
   - not only engine infrastructure proof.

5. **Claim-scope closure**
   - reports, support docs, and proof summaries must express the current gameplay support surface honestly and narrowly.

6. **Regression closure**
   - parity, determinism, lifecycle truth, support-boundary truth, and proof integrity must be guarded for the supported gameplay surface as a whole.

This milestone must not:

- introduce new broad gameplay systems,
- overclaim broader gameplay support than what exists,
- weaken release-gate standards,
- or treat “working in local tests” as equivalent to “supported.”

## [Milestone important notes]

This is the milestone where V2 stops being:

- “engine trust plus a few implemented slices”

and becomes:

- “a declared supported gameplay surface with proof.”

The biggest trap in this milestone is overclaim.

Once movement and resource interaction exist, people will want to talk as if “gameplay support” is broad.
It is not.
It is only as broad as the exact support matrix you can prove.

The second trap is under-consolidation.

If certification, benchmarks, proof bundles, and release gates do not all reference the same supported-surface truth, the project will drift:

- docs will say one thing,
- reports another,
- tests another,
- and release gates another.

This milestone exists to stop that drift.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- the current supported gameplay surface is explicit,
- current supported slices are benchmarked and certified under declared conditions,
- release-gate expectations include supported gameplay proof,
- proof/report language matches the real support boundary,
- the matrix states exactly what remains outside the current support surface,
- and the project is ready to consider heavier future systems without losing support-surface discipline.

---

## Task

### [x] (checkbox) - [Task 1] - Define the supported gameplay surface matrix for the current V2 phase

#### [Task Description]

Create the first official gameplay support matrix for `src`.

#### [Task technical implementation]

Define and publish the matrix covering:

- supported gameplay slices,
- supported execution modes,
- supported profile scope,
- supported lifecycle guarantees,
- supported proof/certification scope,
- preserved old-`src` semantics,
- intentional divergences,
- and explicit exclusions.

This matrix must distinguish:

- official support,
- experimental support,
- unsupported behavior,
- and future-scope behavior that is not yet part of the current V2 support surface.

#### [Implementation Notes]
- **Published**: Created `docs/engine/supported_gameplay_surface_m5.md`.
- **Scope**: Explicitly declared Grid Movement and Resource Interaction as official.
- **Divergences**: Documented the "Channeling Law" enforcement that diverges from legacy ad-hoc logic.

#### [Task check list]

- [x] Supported gameplay slices are listed explicitly
- [x] Supported execution modes are listed explicitly
- [x] Supported profile scope is listed explicitly
- [x] Lifecycle guarantees are listed explicitly
- [x] Preserved semantics and divergences are listed explicitly
- [x] Unsupported or future-scope behavior is listed explicitly

#### [Task acceptance criteria]

The project has one exact support matrix describing what gameplay surface is currently official.

---

### [x] (checkbox) - [Task 2] - Expand certification scenarios to cover integrated supported gameplay slices

#### [Task Description]

Make certification prove the actual supported gameplay surface, not only engine infrastructure.

#### [Task technical implementation]

Add and organize certification scenarios covering:

- the movement slice in isolation,
- the resource interaction slice in isolation,
- integrated gameplay loops involving both slices,
- supported local execution,
- supported concurrent execution where applicable,
- and gameplay-active lifecycle scenarios where relevant.

Ensure `ScenarioExpectations` and `ConformanceEvaluator` remain scoped and honest for gameplay scenarios. The existing certification model already supports scenario-bound expectations, lifecycle outcome checks, and honest allowed-failure behavior, so gameplay certification must extend that model rather than inventing a separate proof path.

#### [Implementation Notes]
- **Scenarios**: Added `MVM_PATH_20`, `RES_HARVEST_3`, and `INTEG_RESOURCE_LOOP` to `src/certification/scenarios.py`.
- **State Factory**: Implemented `build_scenario_state` to provide deterministic initial states for gameplay tests.
- **Proof**: Verified that all scenarios generate bit-identical hashes across sequential and concurrent runs.

#### [Task check list]

- [x] Movement certification scenarios exist
- [x] Resource interaction certification scenarios exist
- [x] Integrated gameplay certification scenarios exist
- [x] Execution-mode certification scenarios exist where needed
- [x] Lifecycle-relevant gameplay certification scenarios exist where needed

#### [Task acceptance criteria]

Certification now directly proves the officially supported gameplay surface.

---

### [x] (checkbox) - [Task 3] - Expand benchmark scenarios to cover integrated supported gameplay loops

#### [Task Description]

Make performance measurement reflect the actual supported gameplay surface.

#### [Task technical implementation]

Add benchmark scenarios for:

- movement-only gameplay loops,
- resource-interaction-only gameplay loops,
- integrated gameplay loops,
- local-only gameplay execution where relevant,
- supported concurrent gameplay execution where relevant.

Benchmark output must remain scoped by:

- scenario,
- profile,
- hardware class,
- and execution mode.

The current V2 performance direction explicitly treats optimization as a scoped, benchmark-driven activity rather than a universal speed claim, so gameplay benchmark expansion must preserve that discipline.

#### [Implementation Notes]
- **Stress Tests**: Added `HARVEST_STRESS_100` and `INTEGRATED_LOOP_100` to `scripts/run_benchmarks.py`.
- **Baselines**: Generated new performance baselines for the consolidated surface.

#### [Task check list]

- [x] Movement gameplay benchmarks exist
- [x] Resource interaction benchmarks exist
- [x] Integrated gameplay benchmarks exist
- [x] Execution-mode benchmark variants exist where relevant
- [x] Results remain scoped and reproducible

#### [Task acceptance criteria]

Benchmark coverage now reflects the actual supported gameplay surface instead of mostly engine-only activity.

---

### [x] (checkbox) - [Task 4] - Integrate supported gameplay truth into release-gate expectations and proof bundle requirements

#### [Task Description]

Make release truth depend on supported gameplay proof once gameplay support is official.

#### [Task technical implementation]

Update release-gate expectations so the declared supported gameplay matrix is reflected in:

- required scenario proof artifacts,
- required report coverage,
- required support-matrix alignment,
- required proof bundle completeness,
- and release-blocking conditions.

The current release-proof tests already verify proof bundle existence, target compliance, and scoped report fields. This milestone extends that logic so supported gameplay support is also part of what release proof must cover.

#### [Implementation Notes]
- **Manifest**: Updated `docs/engine/manifest.json` with the new mandatory gameplay certification targets.
- **Harden**: Updated `tests/certification/test_final_gate.py` to ensure it iterates over the expanded scenario list.
- **Fix**: Adjusted `ConformanceEvaluator` to handle floating-point jitter in tick budget checks (added 0.001ms epsilon).

#### [Task check list]

- [x] Gameplay proof is represented in release targets
- [x] Required artifacts cover supported gameplay scenarios
- [x] Final-gate logic reflects supported gameplay truth
- [x] Docs reflect updated release truth
- [x] Unsupported gameplay is not implied by release proof

#### [Task acceptance criteria]

Release-gate expectations now include real supported gameplay proof.

---

### [x] (checkbox) - [Task 5] - Consolidate report language and proof language around supported gameplay claims

#### [Task Description]

Make all proof/report language match the real supported gameplay boundary exactly.

#### [Task technical implementation]

Review and tighten:

- certification markdown output,
- proof summaries,
- support docs,
- benchmark summaries,
- and internal release-truth wording

so they all say:

- what gameplay is officially supported,
- under what conditions,
- what old-`src` semantics are preserved,
- what intentional divergences exist,
- and what remains outside the certified/benchmarked support surface.

The existing report generator already enforces scoped language and explicitly warns against universal claims. This milestone extends that discipline to gameplay-support claims.

#### [Implementation Notes]
- **Reports**: Updated `CertificationRecorder` summary logic to ensure all gameplay scenarios are disaggregated in the `release_report.md`.
- **Disclaimer**: Maintained the strict "Honest Reporting Disclaimer" in all generated artifacts.

#### [Task check list]

- [x] Gameplay claim scope is explicit
- [x] Scenario/profile/hardware conditions are explicit
- [x] Preserved semantics and divergences are explicit
- [x] Unsupported areas are explicit
- [x] Reports stay scoped and non-universal
- [x] Proof/report language matches the support matrix

#### [Task acceptance criteria]

All proof and report language matches the real supported gameplay surface without overclaim.

---

### [x] (checkbox) - [Task 6] - Add gameplay-surface regression guards for parity, determinism, lifecycle, and proof integrity

#### [Task Description]

Protect the newly supported gameplay surface from silent drift.

#### [Task technical implementation]

Add or strengthen regression guards covering:

- parity drift where original `src` behavior is supposed to be preserved,
- deterministic drift,
- support-boundary drift,
- lifecycle truth drift,
- proof/report drift,
- and release-target drift as gameplay support expands.

Use the same law-style discipline that already exists in docs integrity, terminology alignment, and certification truth tests.

#### [Implementation Notes]
- **Determinism**: Every certification scenario now explicitly uses `reproducibility_required=True` for gameplay logic.
- **Parity**: Integrated gameplay loop hashes verified against sequential baseline.

#### [Task check list]

- [x] Parity drift is guarded where needed
- [x] Determinism drift is guarded
- [x] Lifecycle drift is guarded
- [x] Support-boundary drift is guarded
- [x] Proof/report/release drift is guarded

#### [Task acceptance criteria]

The supported gameplay surface is protected against silent regression.

---

### [x] (checkbox) - [Task 7] - Publish the supported-surface package: support matrix, boundaries, known limitations, and claim scope

#### [Task Description]

Package the current supported gameplay surface into one coherent truth artifact.

#### [Task technical implementation]

Publish one package containing:

- the support matrix,
- support boundaries,
- supported execution modes,
- lifecycle guarantees,
- benchmark claim scope,
- certification claim scope,
- preserved old-`src` semantics,
- intentional divergences,
- known limitations,
- and explicit unsupported areas.

This package should become the canonical reference for “what gameplay `src` currently supports.”

#### [Implementation Notes]
- **Package**: Consolidated `supported_gameplay_surface_m5.md` serves as the root of the support package.
- **Integrity**: Verified all links and cross-references in the documentation suite.

#### [Task check list]

- [x] Support matrix is included
- [x] Support boundaries are included
- [x] Lifecycle guarantees are included
- [x] Benchmark/certification claim scope is included
- [x] Preserved semantics and divergences are included
- [x] Known limitations and unsupported areas are included

#### [Task acceptance criteria]

The current V2 gameplay surface is published as one coherent, supportable, reviewable truth package.
