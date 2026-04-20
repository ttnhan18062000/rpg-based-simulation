# [Milestone 1] - Substrate Freeze and Baseline Readiness

## [Milestone Description]

Milestone 1 is the transition from repair mode to build mode.

Its purpose is to freeze the repaired `src_v2` substrate so future gameplay implementation does not continue building on moving assumptions.

At this point, the engine should already have:

- stable profile and startup validation,
- a stable authoritative state/apply structure,
- runtime control and anti-thrashing behavior,
- lifecycle-aware shutdown/certification flow,
- stable proof artifact generation expectations,
- and closed the blocking resource-truth issues that would make a freeze dishonest.

This milestone does **not** introduce the first official gameplay slice yet.

It creates the stable platform that later RPG-core slices will stand on.

## [Milestone technical implementation]

Create one stable implementation baseline for future RPG-core porting and feature work.

This milestone must complete the freeze of the current substrate in six areas:

1. **Semantic baseline freeze**
   - local single-process semantics remain the reference truth,
   - authoritative mutation remains singular,
   - current deterministic laws are pinned as the gameplay build target.

2. **Runtime truth freeze**
   - runtime signals, status fields, and lifecycle vocabulary stop drifting,
   - current schema becomes the stable integration target for future slices.

3. **Proof contract freeze**
   - proof bundle naming,
   - certification result vocabulary,
   - report surface,
   - and required artifacts become stable enough that gameplay milestones can depend on them.

4. **Concurrency boundary freeze**
   - currently supported concurrent work remains explicit,
   - unsupported work remains explicit,
   - no hidden broadening happens during gameplay milestones.

5. **Transitional cleanup**
   - remove substrate leftovers from the repair phase,
   - remove compatibility ambiguity,
   - and publish the current boundary of the platform.

6. **Behavior-preservation freeze**
   - original `src` and original `tests` are frozen as the temporary behavior oracle for intended RPG-core logic,
   - every official gameplay slice must either preserve intended old behavior,
   - or log an explicit, narrow, reviewable intentional divergence.

This milestone must not:

- introduce combat,
- widen AI behavior,
- introduce inventory webs,
- or widen gameplay breadth in parallel with freeze work.

## [Milestone important notes]

The trap here is letting “mostly fixed” masquerade as “stable enough.”

If baseline/runtime/lifecycle/proof vocabulary continues drifting while gameplay slices are attached, every later milestone becomes harder:

- harder to compare to original `src`,
- harder to benchmark,
- harder to certify,
- harder to review.

This milestone is successful only if the team can stop re-litigating substrate assumptions during Milestones 2 through 5.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- the local semantic baseline is frozen,
- runtime signal and lifecycle vocabulary are frozen,
- proof bundle/report expectations are frozen,
- supported concurrency scope is frozen,
- transitional substrate ambiguity is removed,
- the `src`/`tests` parity-or-divergence rule is frozen,
- and the team has one explicit “ready for gameplay attachment” platform.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the repaired semantic baseline contract for `src_v2`

#### [Task Description]

Turn the repaired runtime baseline into one explicit contract that later gameplay slices must obey.

#### [Task technical implementation]

Freeze and publish the baseline law for:

- authoritative state ownership,
- apply-path exclusivity,
- baseline tick semantics,
- deterministic state transition expectations,
- and what counts as baseline semantic truth versus operational truth.

This task should anchor future gameplay work to the local reference path first, even where supported concurrent execution exists later.

#### [Task possible affected files]

- `docs/engine/runtime_completion_contract_ma.md`
- `docs/engine/project_lawbook_m10.md`
- `src_v2/engine/kernel.py`
- `src_v2/engine/apply.py`
- baseline law tests

#### [Task important notes]

Do not redesign the baseline.
Freeze the repaired baseline.

#### [Task check list]

- [ ] Baseline semantic truth is documented
- [ ] Apply-path exclusivity is explicitly restated
- [ ] Local reference path is identified as semantic baseline
- [ ] Operational state is separated from authoritative state
- [ ] Tests still match the frozen law

#### [Task acceptance criteria]

The repaired local `src_v2` runtime is explicitly frozen as the semantic build target for all later gameplay slices.

---

### [ ] (checkbox) - [Task 2] - Freeze runtime signal, runtime status, and lifecycle outcome vocabulary

#### [Task Description]

Stabilize the runtime truth surface so gameplay features can integrate without chasing schema churn.

#### [Task technical implementation]

Freeze:

- runtime signal names,
- runtime status fields,
- lifecycle outcome names,
- shutdown/finalization result vocabulary,
- and any surfaced status used by certification or proof generation.

Review for lingering schema ambiguity and remove anything transitional.

#### [Task possible affected files]

- `src_v2/observability/signals.py`
- `src_v2/observability/runtime_status.py`
- `src_v2/engine/kernel.py`
- lifecycle/result model files
- `docs/engine/*status*`
- relevant tests

#### [Task important notes]

This is not about adding more metrics.
It is about locking the current truth surface.

#### [Task check list]

- [ ] Signal names are stable
- [ ] Runtime status field names are stable
- [ ] Lifecycle outcome names are stable
- [ ] Timeout/success/failure vocabulary is stable
- [ ] Tests and docs use the same vocabulary

#### [Task acceptance criteria]

Future gameplay code can consume runtime status and lifecycle results without schema drift.

---

### [ ] (checkbox) - [Task 3] - Freeze proof bundle artifact naming and required certification artifact rules

#### [Task Description]

Stabilize the proof/report layer so gameplay milestones can depend on it safely.

#### [Task technical implementation]

Freeze:

- required JSON proof artifact naming,
- required markdown report naming,
- required manifest snapshot behavior,
- scenario-specific report conventions,
- compatibility output expectations,
- and final gate assumptions.

Ensure recorder behavior, release-gate assumptions, and integrity tests all align.

#### [Task possible affected files]

- `src_v2/certification/recorder.py`
- `src_v2/certification/harness.py`
- `docs/engine/manifest.json`
- release-proof docs
- certification and docs tests

#### [Task important notes]

Do not keep half-migrated artifact contracts.
One explicit bundle contract must exist.

#### [Task check list]

- [ ] Canonical proof artifact names are frozen
- [ ] Compatibility artifacts are explicit
- [ ] Required artifacts are documented
- [ ] Final gate assumptions match emitted files
- [ ] Integrity tests match the frozen contract

#### [Task acceptance criteria]

The proof bundle is a stable integration surface for future gameplay certification work.

---

### [ ] (checkbox) - [Task 4] - Freeze the currently supported concurrency scope and explicitly mark unsupported work kinds

#### [Task Description]

Prevent gameplay milestones from accidentally broadening concurrent execution support without proof.

#### [Task technical implementation]

Document and enforce:

- which work kinds are currently supported concurrently,
- which gameplay slices remain local-only,
- what packet/result/equivalence expectations are already valid,
- and what still remains out of scope.

Ensure scheduler/kernel/worker paths enforce the same declared boundary.

#### [Task possible affected files]

- `src_v2/core/work.py`
- `src_v2/engine/kernel.py`
- `src_v2/engine/worker_manager.py`
- concurrency docs
- concurrency tests

#### [Task important notes]

This is a support-boundary freeze, not a concurrency expansion milestone.

#### [Task check list]

- [ ] Supported concurrent work kinds are explicit
- [ ] Unsupported work kinds are explicit
- [ ] Code paths enforce the same support boundary
- [ ] Docs reflect the same boundary
- [ ] Tests fail on undeclared scope expansion

#### [Task acceptance criteria]

Concurrency scope is stable enough that future gameplay slices cannot silently leak into unsupported execution modes.

---

### [ ] (checkbox) - [Task 5] - Remove remaining transitional, dead, or compatibility-only substrate paths

#### [Task Description]

Clean out the leftovers from the repair phase so the team does not keep integrating against stale paths.

#### [Task technical implementation]

Audit and remove:

- dead compatibility branches,
- obsolete status fields,
- stale comments,
- transitional path aliases no longer needed,
- and any half-supported substrate shims that exist only because of earlier migration work.

#### [Task possible affected files]

- `src_v2/engine/*`
- `src_v2/certification/*`
- `src_v2/observability/*`
- `docs/*`
- regression tests

#### [Task important notes]

Do not delete things blindly.
Only remove what the frozen substrate no longer wants to support.

#### [Task check list]

- [ ] Dead branches removed
- [ ] Transitional aliases removed or documented
- [ ] Stale comments cleaned
- [ ] Compatibility-only paths reviewed
- [ ] Tests updated where needed

#### [Task acceptance criteria]

The frozen substrate no longer carries unnecessary ambiguity from the repair phase.

---

### [ ] (checkbox) - [Task 6] - Add substrate drift guardrails and baseline compatibility checks

#### [Task Description]

Make substrate drift visible and cheap to catch.

#### [Task technical implementation]

Add or strengthen guardrails for:

- signal/status schema drift,
- lifecycle vocabulary drift,
- proof artifact drift,
- supported concurrency boundary drift,
- baseline contract drift,
- and declared-resource truth drift.

#### [Task possible affected files]

- docs integrity tests
- certification integrity tests
- runtime schema tests
- CI targets
- milestone guard docs

#### [Task important notes]

This is not process theater.
It is to stop silent drift before gameplay work accelerates.

#### [Task check list]

- [ ] Schema drift tests exist
- [ ] Artifact drift tests exist
- [ ] Baseline drift tests exist
- [ ] Declared-resource truth tests exist
- [ ] CI targets are defined
- [ ] Known support boundary is guarded

#### [Task acceptance criteria]

Substrate drift causes visible failure instead of silent erosion.

---

### [ ] (checkbox) - [Task 7] - Publish the official “ready for gameplay attachment” gate

#### [Task Description]

Define the review gate that declares the substrate stable enough for gameplay attachment.

#### [Task technical implementation]

Create one gate that requires:

- frozen baseline contract,
- frozen runtime/lifecycle vocabulary,
- frozen proof bundle contract,
- explicit concurrency boundary,
- frozen parity/divergence rule for official gameplay slices,
- and passing drift guardrails.

#### [Task possible affected files]

- `docs/engine/readiness_gate_m1.md`
- milestone review docs
- CI/review checklist docs

#### [Task important notes]

This is the line between repair mode and gameplay build mode.

#### [Task check list]

- [ ] Gate conditions are explicit
- [ ] Gate conditions are test-backed
- [ ] Review criteria are documented
- [ ] Known limitations are attached
- [ ] Approval path is clear

#### [Task acceptance criteria]

The team can say, with precision, that the platform is ready for gameplay attachment.

---

### [ ] (checkbox) - [Task 8] - Publish one known-boundaries package for the frozen substrate

#### [Task Description]

Package the frozen substrate with explicit support boundaries and known limitations.

#### [Task technical implementation]

Publish one concise package covering:

- what is stable,
- what is officially supported,
- what is intentionally not supported yet,
- what assumptions future gameplay milestones may rely on,
- and what resource/governor/certification boundaries remain in force.

#### [Task possible affected files]

- `docs/engine/substrate_boundaries_m1.md`
- known limitations docs
- support boundary docs

#### [Task important notes]

Do not hide limitations.
The goal is stable honesty.

#### [Task check list]

- [ ] Stable support is listed
- [ ] Unsupported areas are listed
- [ ] Known limitations are listed
- [ ] Gameplay milestones can reference this package
- [ ] Docs are consistent with code/tests

#### [Task acceptance criteria]

The frozen substrate is documented as a stable build platform with explicit boundaries.

---

### [ ] (checkbox) - [Task 9] - Freeze the mandatory `src`-parity / divergence-log rule for every official RPG slice

#### [Task Description]

Prevent future gameplay milestones from quietly changing the RPG-core meaning during the port.

#### [Task technical implementation]

Create and publish one rule that states:

- original `src` and original `tests` are the temporary behavior oracle for intended RPG-core logic,
- official gameplay slices must capture characterization cases before finalization,
- parity is required where intent is preserved,
- and intentional mismatch must be logged in one reviewable divergence log instead of being hidden inside implementation “cleanup.”

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/gameplay_porting_rule_m1.md`
- comparison harness docs
- milestone review docs

#### [Task important notes]

This rule is what prevents the port from becoming a fork by accident.

#### [Task check list]

- [ ] The behavior oracle is documented
- [ ] Characterization-before-finalization is required
- [ ] Divergence logging rules are explicit
- [ ] Review path for divergences is explicit
- [ ] Later milestones reference this rule directly

#### [Task acceptance criteria]

No official RPG slice can be declared complete without either parity evidence or explicit, reviewable divergence evidence.
