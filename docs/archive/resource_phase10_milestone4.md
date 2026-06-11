---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 4] - Replay, Logging, Metrics, and Observability Compatibility Closure

## [Milestone Description]

Milestone 4 closes the operational artifact surface.

Its purpose is to recover the parts of the old system that operators, tooling, and release workflows depended on outside pure gameplay semantics.

This milestone covers:

- replay artifact compatibility where preserved,
- structured logging expectations where preserved,
- metrics/observability compatibility where preserved,
- report/artifact shape expectations where preserved,
- and compatibility of truth-bearing operational surfaces used by humans or automation.

It is not about inventing new observability. It is about recovering the required compatibility surface honestly.

It does not yet close API/protocol behavior or final-system/headless compatibility.

## [Milestone technical implementation]

Recover the supported operational-artifact compatibility surface in native `src` terms.

This milestone must:

- recover preserved replay/report artifact behavior where required,
- recover preserved structured logging behavior where required,
- recover preserved metrics/observability behavior where required,
- ensure compatibility surfaces remain truthful and bounded,
- and define what operational artifact behavior is preserved, divergent, or unsupported.

This milestone must not:

- let better internal observability excuse broken external artifact expectations,
- blur release-proof/report truth with broader product truth,
- or overclaim compatibility where only a new artifact shape exists.

## [Milestone important notes]

The trap here is thinking “nobody cares about logs/reports/metrics if the engine works.”

Wrong.

These surfaces are often what automation and operators trust first.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported replay/logging/metrics/report behavior is explicit,
- truth-bearing operational surfaces remain bounded and honest,
- preserved versus divergent artifact behavior is explicit,
- and the project has one credible operational-compatibility slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit replay, logging, metrics, and report rows against current `src` operational artifact behavior

#### [Task Description]

Find where operational compatibility is already real, partial, or fake.

#### [Task technical implementation]

Review all Phase 10 operational-artifact rows and map them to current `src` implementation points.

Identify:

- replay artifact behavior already present,
- structured logging behavior already present,
- metrics or observability surfaces already present,
- report/proof artifact behavior already present,
- and where artifact shape still drifts from preserved expectations.

#### [Task possible affected files]

- `src/replay/**`
- `src/observability/**`
- `src/certification/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Do not assume “we emit artifacts” means “we are artifact-compatible.”

#### [Task check list]

- [ ] Replay behavior is mapped
- [ ] Logging behavior is mapped
- [ ] Metrics behavior is mapped
- [ ] Report/artifact shape is mapped
- [ ] Audit notes are reviewable

#### [Task acceptance criteria]

The project has a concrete gap audit for replay/logging/metrics/report rows.

---

### [ ] (checkbox) - [Task 2] - Recover supported replay and report artifact compatibility semantics

#### [Task Description]

Make truth-bearing artifacts explicit where preservation requires them.

#### [Task technical implementation]

Implement or refine supported behavior for:

- replay file/artifact semantics,
- report bundle or proof artifact shape,
- artifact naming/location rules where preserved,
- and stable compatibility rules for consumers that rely on those artifacts.

#### [Task possible affected files]

- `src/replay/**`
- `src/certification/**`
- `tests/replay/**`
- `tests/certification/**`

#### [Task important notes]

If the artifact exists but its consumer contract is broken, compatibility is still broken.

#### [Task check list]

- [ ] Replay artifact rules are explicit
- [ ] Report/proof artifact rules are explicit
- [ ] Naming/location rules are explicit
- [ ] Consumer-shape rules are explicit
- [ ] Preserved vs divergent behavior is clear

#### [Task acceptance criteria]

Supported replay/report artifact semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 3] - Recover supported structured logging and metrics compatibility semantics

#### [Task Description]

Make operational surfaces explicit where preservation requires them.

#### [Task technical implementation]

Implement or refine supported behavior for:

- structured logging fields and behavior,
- metrics emission semantics where preserved,
- observability-surface compatibility where preserved,
- and bounded truthful behavior for those surfaces.

#### [Task possible affected files]

- `src/observability/**`
- `src/logging/**`
- `tests/e2e/**`
- `tests/integration/**`

#### [Task important notes]

Do not let “better new logs” stand in for preserved log/metric compatibility.

#### [Task check list]

- [ ] Logging rules are explicit
- [ ] Metrics rules are explicit
- [ ] Observability compatibility is explicit
- [ ] Truth-boundary rules are explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported logging/metrics/observability compatibility semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 4] - Add direct compatibility tests for replay, logs, metrics, and reports

#### [Task Description]

Prove operational artifact compatibility directly.

#### [Task technical implementation]

Add focused tests for:

- replay artifact presence and shape,
- report/proof artifact presence and shape,
- structured log output expectations,
- metrics/observability output expectations,
- and truth-boundary behavior where preserved.

#### [Task possible affected files]

- `tests/replay/**`
- `tests/certification/**`
- `tests/e2e/**`
- `tests/integration/**`

#### [Task important notes]

Do not leave operational compatibility to informal manual inspection.

#### [Task check list]

- [ ] Replay tests exist
- [ ] Report tests exist
- [ ] Logging tests exist
- [ ] Metrics tests exist
- [ ] Truth-boundary tests exist

#### [Task acceptance criteria]

The supported operational-artifact slice is directly proven by compatibility tests.

---

### [ ] (checkbox) - [Task 5] - Publish the replay/logging/metrics/report compatibility contract for supported Phase 10 scope

#### [Task Description]

Freeze operational compatibility into one explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- supported replay artifact behavior,
- supported log behavior,
- supported metrics/observability behavior,
- supported report/proof artifact behavior,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/operational_artifact_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase10_compat_notes.md`

#### [Task important notes]

If this contract is not explicit, later cutover work will over-assume operational compatibility.

#### [Task check list]

- [ ] Replay rules are documented
- [ ] Log rules are documented
- [ ] Metrics rules are documented
- [ ] Report rules are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit contract for supported replay/logging/metrics/report compatibility.
