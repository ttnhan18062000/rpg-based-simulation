---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 6] - Differential Proof, Support Ratification, and Phase 9 Exit Package

## [Milestone Description]

Milestone 6 turns the recovered Phase 9 semantic slices into auditable replacement truth and closes the phase honestly.

Its purpose is to ensure strategic/social/progression support is proven rather than merely implemented.

This milestone covers:

- characterization of preserved legacy behavior,
- differential old-vs-new proof where preservation is required,
- explicit divergence logging where preservation is not required,
- support-boundary ratification,
- replacement-ledger updates,
- and the handoff baseline for Phase 10.

It does not widen semantic support.
It proves, classifies, and packages the recovered slice.

## [Milestone technical implementation]

Create one proof and ratification pass across the supported Phase 9 slice.

This milestone must:

- add or consolidate characterization tests against original `src` where needed,
- add differential tests for preserved strategic/social/progression behavior,
- log intentional divergences explicitly,
- ratify the supported boundary for preserved and divergent behavior,
- update the replacement ledger for completed Phase 9 rows,
- publish known unsupported remainder,
- and publish one formal “Phase 9 complete” package that later phases must inherit.

This milestone must not:

- confuse richer-looking behavior with preserved behavior,
- defer divergence logging until compatibility/cutover phases,
- or overclaim support because the branch now feels more like a full RPG again.

## [Milestone important notes]

The trap here is the strongest illusion in the whole project.

Once strategy, social consequence, and progression start interacting, the branch will feel dramatically more complete. That is exactly when teams start lying about what is proven.

## [Milestone acceptance criteria]

At the end of Milestone 6:

- preserved Phase 9 behavior has proof where required,
- intentional divergences are logged,
- unsupported remainder remains explicit,
- the support boundary is ratified from evidence,
- replacement-ledger updates are complete,
- and the branch has a formal “Phase 9 complete” handoff baseline.

---

## Task

### [ ] (checkbox) - [Task 1] - Build characterization coverage for preserved Phase 9 legacy behaviors where proof is still weak

#### [Task Description]

Capture what original `src` actually does before claiming parity.

#### [Task technical implementation]

Add or consolidate characterization tests and fixtures for preserved Phase 9 behaviors, including where needed:

- strategic continuity cases,
- cognition-capacity cases,
- blocker/lead/knowledge cases,
- social/contract cases,
- and progression/reward cases.

#### [Task possible affected files]

- `tests/parity/**`
- characterization fixtures
- `docs/engine/phase9_proof_bundle.md`

#### [Task important notes]

If legacy behavior is not characterized, parity claims are guesswork.

#### [Task check list]

- [ ] Strategic cases are characterized
- [ ] Knowledge/social cases are characterized
- [ ] Progression cases are characterized
- [ ] Fixture scope is explicit
- [ ] Weak-proof areas are reduced

#### [Task acceptance criteria]

Preserved Phase 9 legacy behavior has enough characterization coverage to support differential proof.

---

### [ ] (checkbox) - [Task 2] - Add differential old-vs-new proof for preserved strategic and cognition behavior

#### [Task Description]

Prove preserved long-horizon mind behavior against original `src`.

#### [Task technical implementation]

Build or extend parity tests for the supported preserved strategic/cognitive subset, including where relevant:

- project continuity,
- switching/retention,
- bounded active-slice behavior,
- cognition-capacity derivation,
- and explainability/overload behavior.

#### [Task possible affected files]

- `tests/parity/test_strategic_parity.py`
- `tests/parity/test_cognition_parity.py`
- parity fixtures
- divergence notes

#### [Task important notes]

Do not call long-horizon strategy “preserved” until direct old-vs-new proof exists.

#### [Task check list]

- [ ] Supported preserved strategic scope is frozen
- [ ] Continuity cases are compared
- [ ] Capacity cases are compared
- [ ] Explainability cases are compared where required
- [ ] Intentional mismatches are recorded

#### [Task acceptance criteria]

The supported preserved strategic/cognitive slice has direct old-vs-new differential proof where required.

---

### [ ] (checkbox) - [Task 3] - Add differential old-vs-new proof for preserved blocker/lead, social, and progression behavior

#### [Task Description]

Prove the remaining Phase 9 semantic surfaces against original `src`.

#### [Task technical implementation]

Build or extend parity tests for the supported preserved subset of:

- blocker/lead/knowledge continuity,
- betrayal/trust/recruitment/contract behavior,
- progression/class/skill/attribute/reward semantics.

#### [Task possible affected files]

- `tests/parity/test_resource_intelligence_parity.py`
- `tests/parity/test_social_contract_parity.py`
- `tests/parity/test_progression_parity.py`
- parity fixtures
- divergence notes

#### [Task important notes]

Do not let “it feels like the old game again” stand in for old-vs-new evidence.

#### [Task check list]

- [ ] Blocker/lead parity scope is frozen
- [ ] Social parity scope is frozen
- [ ] Progression parity scope is frozen
- [ ] Supported preserved cases are compared
- [ ] Intentional mismatches are recorded

#### [Task acceptance criteria]

The supported preserved blocker/lead/social/progression slice has direct old-vs-new differential proof where required.

---

### [ ] (checkbox) - [Task 4] - Update divergence logs and unsupported-scope records for non-preserved Phase 9 rows

#### [Task Description]

Make every accepted mismatch or non-supported case explicit.

#### [Task technical implementation]

For every non-preserved Phase 9 row:

- record intentional divergence rationale where applicable,
- record unsupported rationale where applicable,
- and update the support matrix and replacement ledger accordingly.

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/unsupported_scope_register.md`
- `docs/engine/replacement_ledger.md`
- `docs/engine/support_matrix.md`

#### [Task important notes]

An undocumented mismatch is not a harmless omission.
It is a false support claim.

#### [Task check list]

- [ ] Divergences are logged
- [ ] Unsupported cases are logged
- [ ] Support matrix is updated
- [ ] Ledger status is updated
- [ ] No material mismatch is left implicit

#### [Task acceptance criteria]

All non-preserved Phase 9 rows have explicit divergence or unsupported-scope records.

---

### [ ] (checkbox) - [Task 5] - Ratify the supported strategic/social/progression boundary from proof evidence

#### [Task Description]

Derive the real Phase 9 support boundary from evidence instead of narrative.

#### [Task technical implementation]

Aggregate the proof results and publish the supported Phase 9 boundary covering:

- preserved supported scope,
- divergent-but-supported scope,
- unsupported scope,
- and open semantic remainder.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase9_exit_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Support should be derived from proof, not from how complete the branch feels.

#### [Task check list]

- [ ] Preserved support is explicit
- [ ] Divergent-but-supported scope is explicit
- [ ] Unsupported scope is explicit
- [ ] Open remainder is explicit
- [ ] Boundary is evidence-backed

#### [Task acceptance criteria]

The supported Phase 9 boundary is ratified directly from proof evidence.

---

### [ ] (checkbox) - [Task 6] - Publish the Phase 9 proof bundle for strategic/social/progression semantics

#### [Task Description]

Turn all Phase 9 evidence into one discoverable proof package.

#### [Task technical implementation]

Collect and index:

- strategic/cognition contract tests,
- blocker/lead/knowledge contract tests,
- social/contract contract tests,
- progression/reward contract tests,
- characterization coverage,
- differential parity coverage,
- divergence and unsupported-scope updates,
- and support-boundary conclusions.

#### [Task possible affected files]

- `docs/engine/phase9_proof_bundle.md`
- `docs/engine/release_proof/phase9/*`
- `tests/**`

#### [Task important notes]

If the proof bundle is scattered, later phases will guess what Phase 9 actually proved.

#### [Task check list]

- [ ] Direct tests are indexed
- [ ] Characterization tests are indexed
- [ ] Parity tests are indexed
- [ ] Divergence records are linked
- [ ] Support conclusions are linked

#### [Task acceptance criteria]

The project has one discoverable proof bundle for completed Phase 9 semantics.

---

### [ ] (checkbox) - [Task 7] - Update replacement-ledger statuses and closure evidence for completed Phase 9 rows

#### [Task Description]

Convert Phase 9 implementation work into authoritative replacement-governance truth.

#### [Task technical implementation]

For each completed Phase 9 row:

- attach closure evidence,
- update row status as appropriate,
- update divergence notes where needed,
- and keep still-open or partially blocked rows visible rather than burying them.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/divergence_log.md`
- `docs/engine/remaining_replacement_scope.md`

#### [Task important notes]

If the ledger is not updated, the phase is not actually complete from a governance perspective.

#### [Task check list]

- [ ] Closed rows are updated
- [ ] Evidence is attached
- [ ] Divergence notes are updated where needed
- [ ] Open rows remain visible
- [ ] Governance artifacts stay consistent

#### [Task acceptance criteria]

Completed Phase 9 rows are reflected accurately in the replacement ledger.

---

### [ ] (checkbox) - [Task 8] - Publish the formal “Phase 9 complete” exit package and Phase 10 readiness input

#### [Task Description]

Close the phase with one package that later compatibility work must inherit.

#### [Task technical implementation]

Publish one Phase 9 exit package containing:

- strategic/social/progression contracts,
- the proof bundle,
- the updated replacement ledger,
- the support boundary,
- the remainder package,
- and the formal statement of what Phase 9 completed and what Phase 10 is now allowed to assume.

#### [Task possible affected files]

- `docs/engine/phase9_exit_package.md`
- `docs/engine/phase10_readiness_input.md`
- milestone review docs

#### [Task important notes]

This is the line between “the game feels much more complete” and “the long-horizon semantic baseline is now real and reviewable.”

#### [Task check list]

- [ ] Exit package is published
- [ ] Contracts are linked
- [ ] Proof bundle is linked
- [ ] Ledger updates are linked
- [ ] Phase 10 assumptions are explicit

#### [Task acceptance criteria]

The project has a complete and reviewable Phase 9 exit package and Phase 10 handoff baseline.
