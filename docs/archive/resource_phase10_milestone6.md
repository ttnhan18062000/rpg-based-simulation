# [Milestone 6] - Differential Proof, Compatibility Ratification, and Phase 10 Exit Package

## [Milestone Description]

Milestone 6 turns the recovered Phase 10 compatibility slices into auditable replacement truth and closes the phase honestly.

Its purpose is to ensure compatibility support is proven rather than merely approximated.

This milestone covers:

- characterization of preserved legacy compatibility behavior,
- differential old-vs-new proof where preservation is required,
- explicit divergence logging where preservation is not required,
- support-boundary ratification,
- replacement-ledger updates,
- and the handoff baseline for Phase 11.

It does not widen scope.
It proves, classifies, and packages the supported compatibility slice.

## [Milestone technical implementation]

Create one proof and ratification pass across the supported Phase 10 compatibility slice.

This milestone must:

- add or consolidate characterization tests against original `src` where needed,
- add differential tests for preserved compatibility behavior,
- log intentional divergences explicitly,
- ratify the supported boundary for preserved and divergent compatibility behavior,
- update the replacement ledger for completed Phase 10 rows,
- publish known unsupported remainder,
- and publish one formal “Phase 10 complete” package that later phases must inherit.

This milestone must not:

- confuse “works for us” with preserved compatibility,
- defer divergence logging until cutover time,
- or overclaim system replacement because the branch now has a broad surface area.

## [Milestone important notes]

The trap here is the last comforting lie before ratification:

“It’s basically compatible enough.”

That phrase means you are about to walk into proof or cutover with fake confidence.

## [Milestone acceptance criteria]

At the end of this milestone:

- preserved Phase 10 compatibility behavior has proof where required,
- intentional divergences are logged,
- unsupported remainder remains explicit,
- the compatibility boundary is ratified from evidence,
- replacement-ledger updates are complete,
- and the branch has a formal “Phase 10 complete” handoff baseline.

---

## Task

### [ ] (checkbox) - [Task 1] - Build characterization coverage for preserved Phase 10 legacy compatibility behaviors where proof is still weak

#### [Task Description]

Capture what original `src` actually does before claiming compatibility parity.

#### [Task technical implementation]

Add or consolidate characterization tests and fixtures for preserved Phase 10 behaviors, including where needed:

- CLI/entry behavior,
- disabled-mode/infra-isolation behavior,
- replay/logging/report behavior,
- API/protocol/headless behavior.

#### [Task possible affected files]

- `tests_v2/parity/**`
- characterization fixtures
- `docs/engine/phase10_proof_bundle.md`

#### [Task important notes]

If legacy compatibility behavior is not characterized, parity claims are guesswork.

#### [Task check list]

- [ ] Entry cases are characterized
- [ ] Disabled-mode cases are characterized
- [ ] Artifact cases are characterized
- [ ] API/headless cases are characterized
- [ ] Weak-proof areas are reduced

#### [Task acceptance criteria]

Preserved Phase 10 compatibility behavior has enough characterization coverage to support differential proof.

---

### [ ] (checkbox) - [Task 2] - Add differential old-vs-new proof for preserved entry and disabled-mode compatibility behavior

#### [Task Description]

Prove the entry and infrastructure-isolation surfaces against original `src`.

#### [Task technical implementation]

Build or extend parity tests for the supported preserved subset of:

- default entry behavior,
- subcommand/argument behavior,
- output-path/startup/shutdown behavior,
- environment-flag behavior,
- broker-disabled/import-isolation behavior.

#### [Task possible affected files]

- `tests_v2/parity/test_cli_parity.py`
- `tests_v2/parity/test_disabled_mode_parity.py`
- parity fixtures
- divergence notes

#### [Task important notes]

Do not call these surfaces “compatible” until direct old-vs-new proof exists where preservation is required.

#### [Task check list]

- [ ] Entry parity scope is frozen
- [ ] Disabled-mode parity scope is frozen
- [ ] Supported preserved cases are compared
- [ ] Intentional mismatches are recorded
- [ ] Proof remains bounded to supported scope

#### [Task acceptance criteria]

The supported preserved entry and disabled-mode slice has direct old-vs-new differential proof where required.

---

### [ ] (checkbox) - [Task 3] - Add differential old-vs-new proof for preserved operational-artifact and consumer-surface compatibility behavior

#### [Task Description]

Prove the remaining compatibility surfaces against original `src`.

#### [Task technical implementation]

Build or extend parity tests for the supported preserved subset of:

- replay/report/logging/metrics behavior,
- API/metadata behavior,
- protocol/transport/compression behavior,
- headless/final-system behavior.

#### [Task possible affected files]

- `tests_v2/parity/test_operational_artifact_parity.py`
- `tests_v2/parity/test_api_protocol_parity.py`
- `tests_v2/parity/test_headless_parity.py`
- parity fixtures
- divergence notes

#### [Task important notes]

Do not let “the new artifacts are nicer” stand in for preserved compatibility evidence.

#### [Task check list]

- [ ] Artifact parity scope is frozen
- [ ] API/protocol parity scope is frozen
- [ ] Headless parity scope is frozen
- [ ] Supported preserved cases are compared
- [ ] Intentional mismatches are recorded

#### [Task acceptance criteria]

The supported preserved operational-artifact and consumer-surface slice has direct old-vs-new differential proof where required.

---

### [ ] (checkbox) - [Task 4] - Update divergence logs and unsupported-scope records for non-preserved Phase 10 rows

#### [Task Description]

Make every accepted mismatch or non-supported compatibility case explicit.

#### [Task technical implementation]

For every non-preserved Phase 10 row:

- record intentional divergence rationale where applicable,
- record unsupported rationale where applicable,
- and update the support matrix and replacement ledger accordingly.

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/unsupported_scope_register.md`
- `docs/engine/replacement_ledger.md`
- `docs/engine/support_matrix.md`

#### [Task important notes]

An undocumented compatibility mismatch is not a harmless omission. It is a lie waiting for cutover.

#### [Task check list]

- [ ] Divergences are logged
- [ ] Unsupported cases are logged
- [ ] Support matrix is updated
- [ ] Ledger status is updated
- [ ] No material mismatch is left implicit

#### [Task acceptance criteria]

All non-preserved Phase 10 rows have explicit divergence or unsupported-scope records.

---

### [ ] (checkbox) - [Task 5] - Ratify the supported compatibility boundary from proof evidence

#### [Task Description]

Derive the real Phase 10 support boundary from evidence instead of confidence.

#### [Task technical implementation]

Aggregate the proof results and publish the supported Phase 10 boundary covering:

- preserved supported scope,
- divergent-but-supported scope,
- unsupported scope,
- and open compatibility remainder.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase10_exit_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Support should be derived from proof, not from optimism.

#### [Task check list]

- [ ] Preserved support is explicit
- [ ] Divergent-but-supported scope is explicit
- [ ] Unsupported scope is explicit
- [ ] Open remainder is explicit
- [ ] Boundary is evidence-backed

#### [Task acceptance criteria]

The supported Phase 10 compatibility boundary is ratified directly from proof evidence.

---

### [ ] (checkbox) - [Task 6] - Publish the Phase 10 proof bundle for compatibility semantics

#### [Task Description]

Turn all Phase 10 evidence into one discoverable proof package.

#### [Task technical implementation]

Collect and index:

- CLI/entry compatibility tests,
- disabled-mode/infrastructure-isolation tests,
- replay/logging/report compatibility tests,
- API/protocol/headless compatibility tests,
- characterization coverage,
- differential parity coverage,
- divergence and unsupported-scope updates,
- and support-boundary conclusions.

#### [Task possible affected files]

- `docs/engine/phase10_proof_bundle.md`
- `docs/engine/release_proof/phase10/*`
- `tests_v2/**`

#### [Task important notes]

If the proof bundle is scattered, later phases will guess what Phase 10 actually proved.

#### [Task check list]

- [ ] Direct tests are indexed
- [ ] Characterization tests are indexed
- [ ] Parity tests are indexed
- [ ] Divergence records are linked
- [ ] Support conclusions are linked

#### [Task acceptance criteria]

The project has one discoverable proof bundle for completed Phase 10 compatibility closure.

---

### [ ] (checkbox) - [Task 7] - Update replacement-ledger statuses and closure evidence for completed Phase 10 rows

#### [Task Description]

Convert Phase 10 implementation work into authoritative replacement-governance truth.

#### [Task technical implementation]

For each completed Phase 10 row:

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

Completed Phase 10 rows are reflected accurately in the replacement ledger.

---

### [ ] (checkbox) - [Task 8] - Publish the formal “Phase 10 complete” exit package and Phase 11 readiness input

#### [Task Description]

Close the phase with one package that proof-ratification work must inherit.

#### [Task technical implementation]

Publish one Phase 10 exit package containing:

- compatibility contracts,
- the proof bundle,
- the updated replacement ledger,
- the support boundary,
- the remainder package,
- and the formal statement of what Phase 10 completed and what Phase 11 is now allowed to assume.

#### [Task possible affected files]

- `docs/engine/phase10_exit_package.md`
- `docs/engine/phase11_readiness_input.md`
- milestone review docs

#### [Task important notes]

This is the line between “V2 has many compatible surfaces” and “the supported compatibility baseline is real and reviewable.”

#### [Task check list]

- [ ] Exit package is published
- [ ] Contracts are linked
- [ ] Proof bundle is linked
- [ ] Ledger updates are linked
- [ ] Phase 11 assumptions are explicit

#### [Task acceptance criteria]

The project has a complete and reviewable Phase 10 exit package and Phase 11 handoff baseline.
