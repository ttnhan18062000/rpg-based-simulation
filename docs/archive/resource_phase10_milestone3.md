# [Milestone 3] - Environment Flags, Broker-Disabled Mode, and Infrastructure-Isolation Closure

## [Milestone Description]

Milestone 3 closes the infrastructure-optional and import-time isolation surface.

Its purpose is to recover the old system’s safe behavior when optional infrastructure is disabled, absent, or intentionally bypassed.

This milestone covers:

- environment-flag behavior where preserved,
- broker-disabled mode behavior,
- safe imports when optional infrastructure is unavailable,
- no-op or fallback behavior where preserved,
- and integration-time isolation expectations.

It is about infrastructure compatibility and safety, not consumer-facing API behavior.

It does not yet close replay/logging/metrics compatibility or API/protocol closure.

## [Milestone technical implementation]

Recover the supported infrastructure-isolation and disabled-mode surface in native `src_v2` terms.

This milestone must:

- recover preserved environment-flag behavior where required,
- recover preserved broker-disabled semantics where required,
- recover safe import-time behavior when optional infrastructure is absent,
- recover safe no-op/fallback accessors where required,
- and define what infrastructure behavior is preserved, divergent, or unsupported.

This milestone must not:

- reintroduce hidden infrastructure dependencies,
- quietly remove disabled-mode behavior and call it simplification,
- or confuse internal architecture cleanliness with external compatibility closure.

## [Milestone important notes]

The trap here is architectural vanity.

A cleaner architecture does not excuse breaking the safe behavior that let the old system run without optional infrastructure present.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported environment-flag behavior is explicit,
- supported broker-disabled behavior is explicit,
- infrastructure-isolation guarantees are explicit where supported,
- preserved versus divergent disabled-mode behavior is explicit,
- and the project has one credible infrastructure-compatibility slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit legacy environment-flag and disabled-mode rows against current `src_v2` infrastructure behavior

#### [Task Description]

Find where disabled-mode and infrastructure-isolation behavior is already real, partial, or fake.

#### [Task technical implementation]

Review all Phase 10 infrastructure rows and map them to current `src_v2` implementation points.

Identify:

- environment flags already present,
- broker-disabled semantics already present,
- safe import behavior already present,
- no-op/fallback accessors already present,
- and places where V2 still assumes infrastructure that the old system allowed to be absent.

#### [Task possible affected files]

- `src_v2/config/**`
- `src_v2/platform/**`
- `src_v2/broker/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Do not trust “works in our dev setup.” This milestone is about explicit absence and disabled-mode safety.

#### [Task check list]

- [ ] Flag behavior is mapped
- [ ] Disabled-mode behavior is mapped
- [ ] Safe import behavior is mapped
- [ ] Fallback/no-op accessors are mapped
- [ ] Audit notes are reviewable

#### [Task acceptance criteria]

The project has a concrete gap audit for environment-flag and disabled-mode rows.

---

### [ ] (checkbox) - [Task 2] - Recover supported environment-flag behavior and explicit disabled-mode semantics

#### [Task Description]

Make infrastructure flags and disabled-mode behavior explicit where preservation requires it.

#### [Task technical implementation]

Implement or refine supported behavior for:

- preserved environment flags,
- preserved disabled-mode toggles,
- explicit disabled-mode branch behavior,
- and clear narrowing or divergence notes where legacy behavior is not preserved.

#### [Task possible affected files]

- `src_v2/config/**`
- `src_v2/platform/**`
- `src_v2/broker/**`
- `tests_v2/config/**`
- `tests_v2/integration/infra/**`

#### [Task important notes]

A hidden environment dependency is a replacement failure, not a small bug.

#### [Task check list]

- [ ] Flag behavior is explicit
- [ ] Disabled-mode behavior is explicit
- [ ] Divergences are explicit where needed
- [ ] Unsupported flags are constrained
- [ ] Behavior remains safe

#### [Task acceptance criteria]

Supported environment-flag and disabled-mode semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 3] - Recover safe import-time and integration-time isolation behavior for optional infrastructure

#### [Task Description]

Make absence of optional infrastructure a supported state where preservation requires it.

#### [Task technical implementation]

Implement or refine supported safe behavior for:

- import without optional infrastructure present,
- safe initialization under disabled mode,
- integration-time no-op or fallback behavior,
- and access patterns that must not crash when infrastructure is absent.

#### [Task possible affected files]

- `src_v2/platform/**`
- `src_v2/broker/**`
- `src_v2/api/**`
- `tests_v2/integration/infra/**`
- `tests_v2/api/**`

#### [Task important notes]

If an import crashes because RabbitMQ or equivalent infra is missing, compatibility is not closed.

#### [Task check list]

- [ ] Safe imports are explicit
- [ ] Disabled initialization is explicit
- [ ] No-op/fallback accessors are explicit
- [ ] Crash-free absence behavior is explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported import-time and integration-time isolation behavior is explicit and enforced.

---

### [ ] (checkbox) - [Task 4] - Add direct compatibility tests for environment flags, disabled mode, and infra isolation

#### [Task Description]

Prove optional-infrastructure compatibility directly.

#### [Task technical implementation]

Add focused tests for:

- environment-flag behavior,
- disabled-mode behavior,
- safe imports without optional infrastructure,
- safe accessor/fallback behavior,
- and integration-time no-crash/no-op expectations.

#### [Task possible affected files]

- `tests_v2/config/**`
- `tests_v2/integration/infra/**`
- `tests_v2/api/**`

#### [Task important notes]

Do not leave disabled-mode proof to manual testing.

#### [Task check list]

- [ ] Flag tests exist
- [ ] Disabled-mode tests exist
- [ ] Safe-import tests exist
- [ ] Fallback/no-op tests exist
- [ ] Integration-isolation tests exist

#### [Task acceptance criteria]

The supported infrastructure-isolation slice is directly proven by compatibility tests.

---

### [ ] (checkbox) - [Task 5] - Publish the environment/disabled-mode/infrastructure-isolation contract for supported Phase 10 scope

#### [Task Description]

Freeze infrastructure compatibility into one explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- supported flag behavior,
- supported disabled-mode behavior,
- supported import-time isolation behavior,
- supported fallback/no-op behavior,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/infrastructure_compat_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase10_compat_notes.md`

#### [Task important notes]

If this contract is not explicit, later cutover work will discover “surprises” that are really just undocumented incompatibilities.

#### [Task check list]

- [ ] Flag behavior is documented
- [ ] Disabled-mode behavior is documented
- [ ] Isolation behavior is documented
- [ ] Fallback rules are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit contract for supported environment, disabled-mode, and infrastructure-isolation compatibility.
