---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 6] - Replay-Visible Deterministic State Closure and Phase 7 Exit Package

## [Milestone Description]

Milestone 6 is the exit gate for Phase 7.

Its purpose is to prove and publish the deterministic substrate that later phases are now required to trust.

This milestone does not widen semantic support.
It does not start combat, strategic, or compatibility recovery.

It packages the completed substrate into one explicit support/proof boundary and closes the phase honestly.

## [Milestone technical implementation]

Create one Phase 7 exit package that turns the completed substrate into a reviewable and enforceable baseline.

This milestone must:

- verify that replay-visible authoritative state shape matches the supported deterministic substrate,
- verify that authoritative outcomes, snapshots, and serialized state are coherent enough for later proof work,
- reconcile replacement-ledger statuses for closed Phase 7 rows,
- publish the supported deterministic substrate boundary,
- publish known intentional divergences, unsupported remainder, and still-blocked rows,
- and publish one formal “Phase 7 complete” package for later phases.

This milestone must not:

- overclaim semantic replacement beyond the substrate,
- describe partial substrate closure as full-engine closure,
- or leave later phases to infer what Phase 7 actually settled.

## [Milestone important notes]

The trap here is exaggeration.

Substrate work is expensive and invisible, so there will be pressure to market this phase as bigger than it is.

Do not do that.

If you overclaim Phase 7, Phase 8 and Phase 9 will inherit fake certainty and burn time on misdiagnosed problems.

## [Milestone acceptance criteria]

At the end of Milestone 6:

- replay-visible deterministic substrate truth is explicitly defined,
- closed Phase 7 rows are updated in the replacement ledger,
- Phase 7 support boundaries are explicit,
- known divergences and unsupported remainder are explicit,
- still-blocked downstream rows remain visible,
- and the branch has a formal “Phase 7 complete” exit package.

---

## Task

### [x] (checkbox) - [Task 1] - Verify replay-visible authoritative state shape against the completed deterministic substrate contracts

#### [Task Description]

Prove that the substrate closure is visible in the state shapes later phases will actually consume.

#### [Task technical implementation]

Run a focused verification pass across:

- authoritative outcomes,
- snapshot exports,
- replay-visible state artifacts,
- and deterministic serialization outputs,

to confirm they align with the completed Phase 7 substrate contracts.

#### [Task possible affected files]

- `src/replay/**`
- `tests/replay/**`
- `docs/engine/phase7_proof_bundle.md`

#### [Task important notes]

If replay-visible truth does not match the substrate contracts, the phase is not actually closed.

#### [Task check list]

- [ ] Authoritative outcomes are verified
- [ ] Snapshot exports are verified
- [ ] Replay artifacts are verified
- [ ] Serialization outputs are verified
- [ ] Mismatches are recorded if found

#### [Task acceptance criteria]

Replay-visible authoritative state shape is verified against the completed Phase 7 substrate contracts.

---

### [x] (checkbox) - [Task 2] - Consolidate the direct proof bundle for Phase 7 substrate closure

#### [Task Description]

Turn all Phase 7 substrate evidence into one reviewable proof package.

#### [Task technical implementation]

Collect and index:

- action/update substrate tests,
- apply/conflict tests,
- snapshot/integrity tests,
- world/init/order determinism tests,
- replay-visible state verification,
- and supporting contracts/docs.

#### [Task possible affected files]

- `docs/engine/phase7_proof_bundle.md`
- `docs/engine/release_proof/phase7/*`
- `tests/**`

#### [Task important notes]

If the proof bundle is scattered, later phases will guess what Phase 7 actually proved.

#### [Task check list]

- [ ] Direct tests are indexed
- [ ] Contracts are indexed
- [ ] Replay verification is indexed
- [ ] Known limitations are attached
- [ ] Proof package is reviewable

#### [Task acceptance criteria]

The project has one discoverable proof bundle for completed Phase 7 substrate closure.

---

### [x] (checkbox) - [Task 3] - Update replacement-ledger statuses and closure evidence for completed Phase 7 rows

#### [Task Description]

Convert implementation work into authoritative replacement-governance truth.

#### [Task technical implementation]

For each completed Phase 7 row:

- attach closure evidence,
- update row status as appropriate,
- update divergence notes where needed,
- and keep still-open or partially blocked rows visible instead of burying them.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/divergence_log.md`
- `docs/engine/remaining_replacement_scope.md`

#### [Task important notes]

If the ledger is not updated, Phase 7 is not actually complete from a governance standpoint.

#### [Task check list]

- [ ] Closed rows are updated
- [ ] Evidence is attached
- [ ] Divergence notes are updated where needed
- [ ] Open rows remain visible
- [ ] Governance artifacts stay consistent

#### [Task acceptance criteria]

Completed Phase 7 rows are reflected accurately in the replacement ledger.

---

### [x] (checkbox) - [Task 4] - Publish the supported deterministic substrate boundary after Phase 7 closure

#### [Task Description]

Restate exactly what Phase 7 actually completed.

#### [Task technical implementation]

Publish or refresh one support-boundary package covering:

- authoritative action/update substrate,
- authoritative apply-path behavior,
- snapshot/state integrity guarantees,
- deterministic world/init/order guarantees,
- replay-visible deterministic state guarantees,
- and known exclusions or unsupported remainder.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase7_exit_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Do not let later phases infer Phase 7 support by rumor.

#### [Task check list]

- [ ] Action/update support is explicit
- [ ] Apply-path support is explicit
- [ ] Snapshot/integrity support is explicit
- [ ] World/init/order support is explicit
- [ ] Known exclusions are explicit

#### [Task acceptance criteria]

The project has one explicit statement of deterministic substrate support after Phase 7 closure.

---

### [x] (checkbox) - [Task 5] - Publish known divergences, unsupported remainder, and still-blocked downstream rows after Phase 7

#### [Task Description]

Make the remaining limits visible before the project moves into broader semantic recovery.

#### [Task technical implementation]

Publish one concise remainder package covering:

- intentional substrate divergences,
- still-unsupported substrate remainder,
- downstream rows still blocked after Phase 7,
- and what later phases must not over-assume.

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/unsupported_scope_register.md`
- `docs/engine/phase7_remainder.md`

#### [Task important notes]

If you hide the remainder, Phase 8 will inherit fiction instead of a baseline.

#### [Task check list]

- [ ] Divergences are listed
- [ ] Unsupported remainder is listed
- [ ] Blocked downstream rows are listed
- [ ] Later assumptions are constrained
- [ ] Package is concise and reviewable

#### [Task acceptance criteria]

The project has one visible remainder package after Phase 7 closure.

---

### [x] (checkbox) - [Task 6] - Publish the formal “Phase 7 complete” exit package and Phase 8 handoff baseline

#### [Task Description]

Close the phase with one package that later semantic work must inherit.

#### [Task technical implementation]

Publish one Phase 7 exit package containing:

- substrate contracts,
- proof bundle,
- updated replacement ledger,
- support boundary,
- remainder package,
- and the formal statement of what Phase 7 completed and what Phase 8 is now allowed to assume.

#### [Task possible affected files]

- `docs/engine/phase7_exit_package.md`
- `docs/engine/phase8_readiness_input.md`
- milestone review docs

#### [Task important notes]

This is the line between “substrate got stronger” and “later phases now have a deterministic baseline they are required to trust.”

#### [Task check list]

- [ ] Exit package is published
- [ ] Contracts are linked
- [ ] Proof bundle is linked
- [ ] Ledger updates are linked
- [ ] Phase 8 assumptions are explicit

#### [Task acceptance criteria]

The project has a complete and reviewable Phase 7 exit package and Phase 8 handoff baseline.
