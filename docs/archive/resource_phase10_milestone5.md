---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 5] - API, Protocol, Transport, and Headless Final-System Compatibility Closure

## [Milestone Description]

Milestone 5 closes the remaining consumer-facing system surface.

Its purpose is to recover the runtime interfaces and final-system execution behavior that make V2 a plausible drop-in replacement for supported consumers.

This milestone covers:

- API route/metadata behavior where preserved,
- websocket or protocol expectations where preserved,
- JSON/MessagePack/compression behavior where preserved,
- headless/final-system execution expectations where preserved,
- and consumer-facing transport semantics that the old system exposed.

It is the broadest compatibility milestone, but it is still bounded to declared replacement scope.

## [Milestone technical implementation]

Recover the supported API/protocol/headless system surface in native `src` terms.

This milestone must:

- recover preserved API/metadata behavior where required,
- recover preserved protocol/transport/compression behavior where required,
- recover preserved headless/final-system execution semantics where required,
- ensure consumer-facing contracts are explicit and testable,
- and define what API/protocol/headless behavior is preserved, divergent, or unsupported.

This milestone must not:

- silently narrow external behavior and call it modernization,
- let internal correctness substitute for external contract compatibility,
- or absorb cutover work that belongs to later phases.

## [Milestone important notes]

The trap here is believing that if the engine core is correct, the system surface is automatically replaceable.

It is not.

Compatibility lives at the edges.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported API/protocol/headless behavior is explicit,
- consumer-facing contracts are explicit and testable,
- preserved versus divergent interface behavior is explicit,
- unsupported remainder is explicit,
- and the project has one credible consumer/system-surface compatibility slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit API, protocol, transport, compression, and headless rows against current `src` consumer behavior

#### [Task Description]

Find where consumer-facing compatibility is already real, partial, or fake.

#### [Task technical implementation]

Review all Phase 10 consumer-surface rows and map them to current `src` implementation points.

Identify:

- API/metadata behavior already present,
- websocket or streaming protocol behavior already present,
- JSON/MessagePack/compression behavior already present,
- headless/final-system behavior already present,
- and where external contract shape still drifts from preserved expectations.

#### [Task possible affected files]

- `src/api/**`
- `src/protocol/**`
- `src/headless/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Do not confuse internal route existence with externally compatible behavior.

#### [Task check list]

- [ ] API behavior is mapped
- [ ] Protocol/transport behavior is mapped
- [ ] Compression behavior is mapped
- [ ] Headless behavior is mapped
- [ ] Audit notes are reviewable

#### [Task acceptance criteria]

The project has a concrete gap audit for API/protocol/headless rows.

---

### [ ] (checkbox) - [Task 2] - Recover supported API route and metadata compatibility semantics

#### [Task Description]

Make consumer-facing API behavior explicit where preservation requires it.

#### [Task technical implementation]

Implement or refine supported behavior for:

- metadata routes,
- response-shape compatibility,
- route presence and naming where preserved,
- and bounded divergence where legacy behavior is intentionally not preserved.

#### [Task possible affected files]

- `src/api/**`
- `tests/api/**`
- `tests/integration/**`

#### [Task important notes]

If an API exists but its route/shape contract changed in important ways, that is not compatibility.

#### [Task check list]

- [ ] Route behavior is explicit
- [ ] Metadata behavior is explicit
- [ ] Response-shape rules are explicit
- [ ] Divergences are explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported API and metadata compatibility semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 3] - Recover supported protocol, transport, and compression compatibility semantics

#### [Task Description]

Make wire-level behavior explicit where preservation requires it.

#### [Task technical implementation]

Implement or refine supported behavior for:

- websocket or streaming protocol expectations,
- JSON vs MessagePack behavior where preserved,
- gzip or compression semantics where preserved,
- and explicit consumer-facing transport behavior.

#### [Task possible affected files]

- `src/protocol/**`
- `src/api/**`
- `tests/api/**`
- `tests/integration/**`

#### [Task important notes]

Compatibility breaks at the wire, not just in business logic.

#### [Task check list]

- [ ] Protocol behavior is explicit
- [ ] Transport behavior is explicit
- [ ] Compression behavior is explicit
- [ ] Consumer contract is explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported protocol/transport/compression compatibility semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 4] - Recover supported headless and final-system execution compatibility semantics

#### [Task Description]

Make non-interactive/system-level execution explicit where preservation requires it.

#### [Task technical implementation]

Implement or refine supported headless/final-system behavior, including where preserved:

- headless runtime execution,
- final artifact or output expectations,
- non-interactive execution assumptions,
- and compatibility of final-system workflows that the old system supported.

#### [Task possible affected files]

- `src/headless/**`
- `src/api/**`
- `src/engine/**`
- `tests/e2e/**`
- `tests/integration/**`

#### [Task important notes]

Do not confuse “the engine can run” with “headless system compatibility is preserved.”

#### [Task check list]

- [ ] Headless behavior is explicit
- [ ] Final output expectations are explicit
- [ ] Non-interactive assumptions are explicit
- [ ] System workflow compatibility is explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported headless/final-system execution semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 5] - Add direct compatibility tests for API, protocol, transport, and headless behavior

#### [Task Description]

Prove consumer-facing compatibility directly.

#### [Task technical implementation]

Add focused tests for:

- API routes and metadata,
- protocol/wire behavior,
- JSON/MessagePack/compression semantics,
- headless execution behavior,
- and final-system output expectations.

#### [Task possible affected files]

- `tests/api/**`
- `tests/integration/**`
- `tests/e2e/**`

#### [Task important notes]

Do not leave consumer-surface compatibility to internal unit tests alone.

#### [Task check list]

- [ ] API tests exist
- [ ] Protocol tests exist
- [ ] Compression tests exist
- [ ] Headless tests exist
- [ ] Final-system tests exist

#### [Task acceptance criteria]

The supported consumer/system-surface slice is directly proven by compatibility tests.

---

### [ ] (checkbox) - [Task 6] - Publish the API/protocol/headless compatibility contract for supported Phase 10 scope

#### [Task Description]

Freeze consumer-facing compatibility into one explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- supported API behavior,
- supported protocol/transport/compression behavior,
- supported headless/final-system behavior,
- consumer-facing shape expectations,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/consumer_surface_contract.md`
- `docs/engine/api_protocol_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase10_compat_notes.md`

#### [Task important notes]

If this contract is not explicit, later cutover work will be based on wishful assumptions.

#### [Task check list]

- [ ] API rules are documented
- [ ] Protocol/transport rules are documented
- [ ] Compression rules are documented
- [ ] Headless rules are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit contract for supported API/protocol/headless compatibility.
