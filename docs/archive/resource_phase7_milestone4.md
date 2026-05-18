# [Milestone 4] - Snapshot Integrity, Isolation, and Serialization Closure

## [Milestone Description]

Milestone 4 closes the snapshot and state-integrity substrate.

Its purpose is to ensure the engine’s read surfaces are not secretly mutable, not aliasing live state, and not producing serialization behavior that undermines determinism or authority.

This milestone covers:

- snapshot immutability,
- deep-copy or equivalent isolation,
- serialization-shape stability,
- and authoritative export/state-comparison discipline.

It does not cover world generation or engine phase order.

## [Milestone technical implementation]

Complete the snapshot and serialization substrate so reads, exports, replay surfaces, and inspection surfaces cannot quietly redefine or contaminate authority.

This milestone must:

- enforce snapshot immutability for supported read surfaces,
- ensure deep isolation where snapshots are expected to be independent from live state,
- close serialization drift that undermines deterministic comparison or replay,
- ensure authoritative state export is comparison-safe,
- and define the supported deterministic state shape used by proof and replay.

This milestone must not:

- rely on accidental non-mutation as the integrity guarantee,
- leave read surfaces ambiguous between live views and frozen snapshots,
- or treat serialization as a mere compatibility detail.

## [Milestone important notes]

The trap here is underestimating snapshot bugs because they look like testing or tooling problems.

They are not.

They are authoritative-state problems.

## [Milestone acceptance criteria]

At the end of Milestone 4:

- snapshot immutability is enforced for supported scope,
- deep isolation guarantees are explicit,
- deterministic serialization shape is explicit,
- authoritative state export is trustworthy for proof and replay,
- and snapshot/state integrity is no longer a hidden risk surface.

---

## Task

### [x] (checkbox) - [Task 1] - Audit snapshot creation, read surfaces, and serialization paths against Phase 7 integrity rows

#### [Task Description]

Map where state integrity is strong, weak, or ambiguous.

#### [Task technical implementation]

Review:

- snapshot construction paths,
- state views exposed to workers/tests/replay/inspection,
- serialization/export paths,
- and any known aliasing or mutation leakage points.

#### [Task possible affected files]

- `src/core/state/**`
- `src/replay/**`
- `src/serialization/**`
- `tests/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

If you do not know which state surfaces are live versus frozen, you do not have integrity closure.

#### [Task check list]

- [ ] Snapshot creation paths are mapped
- [ ] Read surfaces are classified
- [ ] Serialization paths are mapped
- [ ] Aliasing risks are identified
- [ ] Audit notes are reviewable

#### [Task acceptance criteria]

The project has a concrete integrity audit for snapshot and serialization rows.

---

### [x] (checkbox) - [Task 2] - Enforce snapshot immutability for supported authoritative read surfaces

#### [Task Description]

Turn snapshot non-mutation from convention into contract.

#### [Task technical implementation]

Refine snapshot construction and access rules so supported snapshots cannot be mutated as live state.

This task should:

- enforce immutability directly where feasible,
- add guardrails or wrappers where needed,
- and narrow support claims if any mutable read surface must temporarily remain.

#### [Task possible affected files]

- `src/core/state/**`
- `src/core/models/**`
- `tests/core/test_snapshot_immutability.py`

#### [Task important notes]

A snapshot that is merely “not usually mutated” is not a snapshot contract.

#### [Task check list]

- [ ] Supported snapshots are immutable
- [ ] Guardrails exist where needed
- [ ] Temporary exceptions are documented if any remain
- [ ] Mutation failures are test-visible
- [ ] Support claims match reality

#### [Task acceptance criteria]

Snapshot immutability is enforced for supported authoritative read surfaces.

---

### [x] (checkbox) - [Task 3] - Enforce deep isolation or explicit non-aliasing guarantees for snapshot/state views

#### [Task Description]

Prevent live-state aliasing from quietly contaminating authoritative read behavior.

#### [Task technical implementation]

Refine snapshot creation and read surfaces so supported state views do not alias live mutable authority in unsupported ways.

This task should:

- deep-copy where required,
- use frozen/value representations where appropriate,
- and document any intentionally shared immutable structures.

#### [Task possible affected files]

- `src/core/state/**`
- `src/core/models/**`
- `tests/core/test_snapshot_deep_isolation.py`

#### [Task important notes]

If a snapshot shares mutable guts with live state, later parity proof is contaminated.

#### [Task check list]

- [ ] Aliasing risks are removed or fenced off
- [ ] Deep isolation exists where required
- [ ] Shared immutable structures are explicit
- [ ] Tests detect mutation leakage
- [ ] Guarantees are documented

#### [Task acceptance criteria]

Supported snapshots and read views have explicit non-aliasing integrity guarantees.

---

### [x] (checkbox) - [Task 4] - Canonicalize deterministic serialization and authoritative state-export shape

#### [Task Description]

Make state export deterministic enough for proof, replay, and comparison.

#### [Task technical implementation]

Refine serialization/export behavior so supported authoritative state produces a stable, explicit shape suitable for:

- deterministic comparison,
- replay-visible truth,
- and future parity/differential work.

This task should:

- remove unstable ordering where relevant,
- normalize optional/empty/default representation rules where needed,
- and document the supported export shape.

#### [Task possible affected files]

- `src/serialization/**`
- `src/replay/**`
- `tests/core/test_state_serialization_determinism.py`

#### [Task important notes]

Serialization drift is not harmless.
It breaks proof surfaces.

#### [Task check list]

- [ ] Supported export shape is explicit
- [ ] Unstable ordering is removed
- [ ] Representation rules are normalized
- [ ] Replay/proof consumers can use the shape reliably
- [ ] Determinism is test-visible

#### [Task acceptance criteria]

Supported authoritative state export has one canonical deterministic serialization shape.

---

### [x] (checkbox) - [Task 5] - Add direct tests for snapshot immutability, deep isolation, and deterministic serialization

#### [Task Description]

Prove state integrity directly.

#### [Task technical implementation]

Add focused tests for:

- snapshot immutability,
- deep-copy or equivalent isolation,
- no live-state mutation leakage,
- deterministic serialization shape,
- and authoritative export comparability.

#### [Task possible affected files]

- `tests/core/test_snapshot_immutability.py`
- `tests/core/test_snapshot_deep_isolation.py`
- `tests/core/test_state_serialization_determinism.py`
- `tests/replay/test_authoritative_export_shape.py`

#### [Task important notes]

Do not rely only on accidental stability in broad integration tests.

#### [Task check list]

- [ ] Immutability tests exist
- [ ] Deep-isolation tests exist
- [ ] Mutation-leak tests exist
- [ ] Serialization-determinism tests exist
- [ ] Export-shape tests exist

#### [Task acceptance criteria]

Snapshot and serialization integrity are directly proven by focused tests.

---

### [x] (checkbox) - [Task 6] - Publish the snapshot/state-integrity contract for supported substrate scope

#### [Task Description]

Freeze snapshot, isolation, and serialization guarantees into one explicit contract.

#### [Task technical implementation]

Publish one contract package covering:

- snapshot immutability rules,
- isolation guarantees,
- authoritative export rules,
- deterministic serialization shape,
- and known exclusions.

#### [Task possible affected files]

- `docs/engine/snapshot_integrity_contract.md`
- `docs/engine/serialization_contract.md`
- `docs/engine/support_matrix.md`

#### [Task important notes]

If integrity guarantees are not explicit, later phases will assume stronger safety than actually exists.

#### [Task check list]

- [ ] Snapshot rules are documented
- [ ] Isolation rules are documented
- [ ] Export rules are documented
- [ ] Serialization shape is documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit snapshot/state-integrity contract for supported substrate scope.
