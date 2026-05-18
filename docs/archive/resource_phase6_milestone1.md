Below is the full detailed implementation plan for **Phase 6** in the same milestone-and-task structure as the detailed Phase 5 reference. It is built around the corrected post–Phase 5 roadmap: Phase 6 is the **replacement-ledger and scope-ratification phase**, not a gameplay-expansion phase. Its job is to build the authoritative replacement ledger across both checklist families, classify every remaining legacy item, and assign proof path and future phase ownership without mixing those jobs together. That separation is required by the revised roadmap and by the V2 handbook’s support, divergence, and proof standards.

# Detailed Implementation Plan — Phase 6 of `src`

This plan assumes Phase 5 has already moved `src` into a materially better state by recovering a bounded resource/town/progression slice and by improving proof, runtime truth, and support clarity around that slice.

Phase 6 is not a broad semantic expansion phase.

It is the phase where the project must stop operating on implied scope and start operating on an authoritative replacement ledger.

The core problem this phase is trying to solve is:

- the remaining replacement surface is larger than “more gameplay porting,”
- the legacy scope splits into RPG-core semantics and separate system-compatibility surfaces,
- and later phases will become chaotic unless those surfaces are inventoried, classified, and phase-assigned explicitly.

This document expands the high-level Phase 6 plan into implementation-ready milestone detail using the same milestone and task structure as the detailed Phase 5 reference.

---

# [Milestone 1] - Phase 5 Exit Closure and Phase 6 Readiness

## [Milestone Description]

Milestone 1 is the gate between the completed Phase 5 branch state and legitimate Phase 6 work.

Its purpose is to make sure Phase 6 does not inherit unresolved truth debt from Phase 5.

By this point, the branch may already have:

- a stronger bounded resource progression slice,
- a better support package around that slice,
- better benchmark/certification alignment,
- and a more credible runtime proof surface.

That is still not enough.

This milestone exists because Phase 6 should not proceed while:

- the Phase 5 support statement remains broader than the real supported slice,
- known divergences from original `src` remain scattered or implicit,
- proof artifacts are not packaged into one discoverable baseline,
- release-truth surfaces still overclaim replacement readiness,
- or the team is still speaking about “current support” in loose narrative terms instead of a frozen baseline.

This milestone does not build the replacement ledger itself.
It closes the previous phase honestly so the ledger starts from a real baseline instead of a myth.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 6.

This milestone must complete the exit-closure work for the current supported slices and truth surfaces in five areas:

1. **Phase 5 support-surface closure**
   - the supported progression slice must be restated precisely,
   - not inferred from scattered tests or docs.

2. **Phase 5 proof-package closure**
   - current proof artifacts must be discoverable as one baseline package,
   - not split across ad hoc reports.

3. **Divergence and limitation closure**
   - known intentional divergences and unsupported remainder must be frozen explicitly.

4. **Release-truth closure**
   - docs, support statements, and release-language must match the actual branch state.

5. **Phase 6 baseline closure**
   - the project must publish one formal “this is the baseline from which replacement ratification begins” record.

This milestone must not:

- begin legacy-surface inventory work,
- reopen settled Phase 5 implementation unless truth is actually broken,
- or use vague claims like “mostly supported” as a substitute for a real baseline.

## [Milestone important notes]

The trap here is pretending that a strong Phase 5 slice automatically gives you a stable replacement baseline.

It does not.

If support claims, divergence records, proof artifacts, and release-truth language are still loose, then Phase 6 starts from contaminated inputs and every later classification decision becomes unreliable. The handbook explicitly rejects calling a slice “officially supported” unless implementation, proof, divergence logging, runtime truth, boundedness, and docs are all aligned.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- the supported Phase 5 slice is frozen as the official Phase 6 baseline,
- known Phase 5 divergences and known unsupported remainder are consolidated,
- proof artifacts are bundled into one discoverable entry package,
- release/documentation surfaces no longer overclaim support,
- and the branch has an explicit “Phase 6 ready” gate.

---

## Task

### [x] (checkbox) - [Task 1] - Freeze the exact supported Phase 5 slice as the formal Phase 6 baseline

#### [Task Description]

Restate, in one place, exactly what gameplay/runtime surface Phase 5 actually completed and what it did not.

#### [Task technical implementation]

Publish one baseline scope package covering the supported Phase 5 surface only.

This task should:

- restate the supported progression slice in plain language,
- separate supported behavior from experimental behavior,
- separate preserved behavior from merely implemented behavior,
- identify supported execution modes and profile assumptions where relevant,
- and exclude later-phase surfaces that are not truly complete yet.

#### [Task possible affected files]

- `docs/engine/phase5_exit_support_boundary.md`
- `docs/engine/support_matrix.md`
- `docs/engine/replacement_status_overview.md`
- support claim docs
- release/readiness summaries

#### [Task important notes]

Do not let “there is code” masquerade as “officially supported.”

#### [Task check list]

- [x] Supported Phase 5 surface is explicit
- [x] Unsupported remainder is explicit
- [x] Experimental or partial surfaces are not misrepresented
- [x] Execution-mode assumptions are explicit where relevant
- [x] Baseline wording matches actual code/tests

**Implementation Comment**: Frozen via `docs/engine/phase5_exit_support_boundary.md`. This artifact explicitly defines the Move-Harvest-Resolve loop and Blacksmith crafting as the official baseline, while excluding combat and advanced economy.

#### [Task acceptance criteria]

The project has one precise statement of the supported Phase 5 slice that Phase 6 can use as its baseline.

---

### [x] (checkbox) - [Task 2] - Consolidate known Phase 5 divergences, limitations, and unsupported remainder into one truth package

#### [Task Description]

Stop carrying Phase 5 differences and limitations in scattered notes, memory, or commit history.

#### [Task technical implementation]

Create or refresh one Phase 5 truth package that records:

- known preserved behavior,
- known intentional divergences,
- known unsupported behavior,
- known limitations,
- and the rationale for each non-preserved case.

Use the handbook divergence standard directly so every mismatch is either explained or rejected as unfinished.

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/phase5_exit_package.md`
- `docs/engine/known_limitations.md`
- support boundary docs

#### [Task important notes]

An undocumented mismatch is not a harmless omission.
It is a false support claim waiting to happen.

#### [Task check list]

- [x] Preserved behavior already claimed by Phase 5 is listed
- [x] Intentional divergences are listed
- [x] Unsupported remainder is listed
- [x] Limitations are listed
- [x] Every mismatch has rationale or is explicitly unresolved

**Implementation Comment**: Established `docs/engine/phase5_truth_package.md` as the master index. Divergences are detailed in `docs/engine/divergence_log.md` with handbook-compliant rationales (Bug Fix, Contract Hardening, etc.). Limitations are cataloged in `docs/engine/known_limitations.md`.

#### [Task acceptance criteria]

Phase 5 ends with one discoverable truth package for preserved, divergent, unsupported, and limited behavior.

---

### [x] (checkbox) - [Task 3] - Consolidate Phase 5 proof artifacts into a discoverable baseline entry package

#### [Task Description]

Turn the current proof surface into one baseline package rather than a pile of disconnected evidence.

#### [Task technical implementation]

Collect and index the current Phase 5 evidence package:

- parity tests where relevant,
- contract tests,
- lifecycle/replay validation,
- certification/benchmark evidence where applicable,
- and supporting documentation that explains the declared support scope.

The output should be reviewable by someone who did not personally build Phase 5. That is the minimum bar for a real baseline.

#### [Task possible affected files]

- `docs/engine/phase5_proof_bundle.md`
- `docs/engine/release_proof/phase5/*`
- `tests/*`
- benchmark/certification index docs

#### [Task important notes]

If the proof package is not discoverable, Phase 6 classification work will fall back to rumor.

#### [Task check list]

- [x] Proof artifacts are indexed
- [x] Links to supporting tests exist
- [x] Lifecycle/certification implications are referenced where relevant
- [x] Evidence package is readable without tribal knowledge
- [x] Package matches current supported claims

**Implementation Comment**: Created `docs/engine/phase5_proof_bundle.md`. This artifact provides a direct index to parity oracles, contract test suites, and certification results. All claims of "Official Support" are now discoverable and verifiable by external reviewers.

#### [Task acceptance criteria]

The current Phase 5 baseline has one discoverable proof package suitable for Phase 6 use.

---

### [x] (checkbox) - [Task 4] - Reconcile release-truth and support-language surfaces with the actual baseline

#### [Task Description]

Bring release/readiness language back into sync with the real branch state.

#### [Task technical implementation]

Review the current docs, release-proof statements, support matrices, and readiness language.

Narrow or correct any wording that suggests:

- broader semantic replacement than actually exists,
- broader compatibility replacement than actually exists,
- or broader support than the current proof package justifies.

The result should align with the handbook’s “official support” completion gate rather than optimistic language.

#### [Task possible affected files]

- `README.md`
- `docs/engine/support_matrix.md`
- `docs/engine/release_readiness.md`
- `docs/engine/replacement_status_overview.md`
- release-proof docs

#### [Task important notes]

A strong runtime with dishonest release language is still dishonest.

#### [Task check list]

- [x] Overclaims are removed
- [x] Support language matches proof language
- [x] Replacement language matches actual baseline
- [x] Docs and release artifacts say the same thing
- [x] Known limitations remain visible

**Implementation Comment**: Hardened `README.md`, `pitch.md`, and high-level matrices. Removed all overclaims regarding combat or social support. Added explicit baseline warnings and qualified the "substrate-only" nature of standard milestones.

#### [Task acceptance criteria]

Release/documentation truth is aligned with the actual Phase 5 baseline.

---

### [x] (checkbox) - [Task 5] - Freeze the formal Phase 5 exit package for downstream Phase 6 use

#### [Task Description]

Publish one compact baseline artifact that later milestones can cite without reopening Phase 5 arguments.

#### [Task technical implementation]

Publish a concise Phase 5 exit package containing:

- supported slices,
- proof status,
- runtime/certification status where relevant,
- known limitations,
- known divergences,
- and the explicit statement that this package is the entry baseline for Phase 6.

#### [Task possible affected files]

- `docs/engine/phase5_exit_package.md`
- `docs/engine/milestone_reviews/phase5_exit.md`
- `docs/engine/divergence_log.md`

#### [Task important notes]

Do not let later milestones renegotiate the Phase 5 baseline casually.

#### [Task check list]

- [x] Supported slices are listed
- [x] Proof status is listed
- [x] Divergences are listed
- [x] Limitations are listed
- [x] Package is concise and authoritative

**Implementation Comment**: Published `docs/engine/phase5_exit_package.md`. This is the single authoritative source for Phase 6 entry, unifying truth, proof, and support boundaries for the replacement ledger phase.

#### [Task acceptance criteria]

A single Phase 5 exit package exists and is usable as the official Phase 6 input.

---

### [x] (checkbox) - [Task 6] - Publish the formal “Phase 6 ready” gate

#### [Task Description]

Turn the previous tasks into one explicit entry decision.

#### [Task technical implementation]

Create one review gate that requires:

- frozen Phase 5 support boundary,
- consolidated divergence and limitation package,
- discoverable proof bundle,
- reconciled release-truth language,
- and a published Phase 5 exit package.

#### [Task possible affected files]

- `docs/engine/phase6_readiness_gate.md`
- review checklist docs
- release/readiness gate docs

#### [Task important notes]

This is the line between “still cleaning Phase 5” and “actually entering Phase 6.”

#### [Task check list]

- [x] Gate conditions are explicit
- [x] Gate conditions are evidence-backed
- [x] Approval criteria are reviewable
- [x] Known limitations are attached
- [x] Phase 6 entry is no longer ambiguous

**Implementation Comment**: The exit package and accompanying integrity tests (`tests/docs/test_doc_integrity.py`) formally constitute the Phase 6 ready gate. All requirements for Milestone 1 are satisfied.

#### [Task acceptance criteria]

The branch has a precise, reviewable, and honest entry gate for Phase 6.
