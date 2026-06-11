---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 2] - CLI, Entrypoint, and Execution-Mode Compatibility Closure

## [Milestone Description]

Milestone 2 closes the user- and operator-facing entry surface.

Its purpose is to recover the original system’s execution contracts where replacement requires them.

This milestone covers:

- default entry behavior,
- serve/cli/inspect contract behavior where preserved,
- argument compatibility,
- execution-mode defaults,
- expected output-path and startup/shutdown behavior,
- and equivalent headless-entry semantics where required.

It is about how the system is entered and run, not internal gameplay semantics.

It does not yet close broker-disabled behavior, observability compatibility, or API/protocol surfaces.

## [Milestone technical implementation]

Recover the supported CLI and entrypoint surface in native `src` terms.

This milestone must:

- recover preserved default entry semantics where required,
- recover preserved subcommand and argument behavior where required,
- recover preserved startup/shutdown expectations where required,
- recover expected replay/output-path semantics where required,
- and define what parts of entry/CLI behavior are preserved, intentionally divergent, or unsupported.

This milestone must not:

- silently change operator-visible behavior and call it cleanup,
- absorb protocol or observability work owned by later milestones,
- or overclaim compatibility where only internal equivalents exist.

## [Milestone important notes]

The trap here is underestimating “how people run the system.”

If V2 cannot stand in for the real entry surface, it is not replacement-ready, no matter how strong the internals are.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported entry/CLI behavior is explicit,
- startup/shutdown semantics are explicit where supported,
- execution-mode compatibility is explicit where supported,
- preserved versus divergent entry behavior is explicit,
- and the project has one credible entry-surface compatibility slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit legacy CLI and entrypoint rows against current `src` entry behavior

#### [Task Description]

Find where the system-entry surface is already real, partial, or fake.

#### [Task technical implementation]

Review all Phase 10 entry-surface rows and map them to current `src` implementation points.

Identify:

- default entry behavior already present,
- serve/cli/inspect contracts already present,
- argument compatibility already present,
- replay/output-path expectations already present,
- and startup/shutdown semantics that still drift from the preserved surface.

#### [Task possible affected files]

- `src/__main__.py`
- `src/cli/**`
- `src/api/**`
- `docs/engine/replacement_ledger.md`
- `docs/engine/phase10_backlog.md`

#### [Task important notes]

Do not start rebuilding the entry surface before you know which visible contracts are actually missing.

#### [Task check list]

- [ ] Default entry behavior is mapped
- [ ] Subcommands/arguments are mapped
- [ ] Output-path semantics are mapped
- [ ] Startup/shutdown semantics are mapped
- [ ] Audit notes are reviewable

#### [Task acceptance criteria]

The project has a concrete gap audit for CLI and entrypoint rows.

---

### [ ] (checkbox) - [Task 2] - Recover supported default entry behavior and preserved subcommand semantics

#### [Task Description]

Make entry behavior explicit rather than “whatever the new runtime currently happens to do.”

#### [Task technical implementation]

Implement or refine supported entry behavior so preserved execution contracts are explicit, including where required:

- default `python -m src` behavior,
- serve/cli/inspect subcommands,
- argument names and defaults,
- and controlled failure behavior for invalid arguments.

#### [Task possible affected files]

- `src/__main__.py`
- `src/cli/**`
- `tests/e2e/**`
- `tests/cli/**`

#### [Task important notes]

A command surface that “mostly works” is not compatibility.

#### [Task check list]

- [ ] Default entry behavior is explicit
- [ ] Subcommand behavior is explicit
- [ ] Argument defaults are explicit
- [ ] Invalid-argument behavior is explicit
- [ ] Behavior remains deterministic

#### [Task acceptance criteria]

Supported entry and subcommand semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 3] - Recover supported output-path, startup, and shutdown compatibility semantics

#### [Task Description]

Make operator-visible execution expectations explicit where preservation requires them.

#### [Task technical implementation]

Implement or refine supported behavior for:

- replay or output-path semantics,
- startup registry/load/bootstrap expectations,
- logging initialization order where relevant,
- and clean shutdown/teardown expectations where preserved.

#### [Task possible affected files]

- `src/cli/**`
- `src/engine/**`
- `src/api/**`
- `tests/e2e/**`
- `tests/cli/**`

#### [Task important notes]

If startup/shutdown behavior differs in user-visible ways, that is not “internal architecture.” That is compatibility drift.

#### [Task check list]

- [ ] Output-path semantics are explicit
- [ ] Startup behavior is explicit
- [ ] Logging/init behavior is explicit
- [ ] Shutdown/teardown behavior is explicit
- [ ] Preserved vs divergent behavior is clear

#### [Task acceptance criteria]

Supported output-path, startup, and shutdown semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 4] - Add direct black-box tests for CLI and entrypoint compatibility

#### [Task Description]

Prove entry behavior from the outside, not just by importing internal modules.

#### [Task technical implementation]

Add focused tests for:

- default entry mode,
- subcommand argument behavior,
- invalid-argument failure behavior,
- output-path behavior,
- and startup/shutdown expectations.

#### [Task possible affected files]

- `tests/cli/**`
- `tests/e2e/**`
- `tests/integration/**`

#### [Task important notes]

Entry compatibility must be proven black-box. Internal unit tests are not enough.

#### [Task check list]

- [ ] Default-entry tests exist
- [ ] Subcommand tests exist
- [ ] Invalid-argument tests exist
- [ ] Output-path tests exist
- [ ] Startup/shutdown tests exist

#### [Task acceptance criteria]

The supported entry surface is directly proven by black-box compatibility tests.

---

### [ ] (checkbox) - [Task 5] - Publish the CLI and entrypoint compatibility contract for supported Phase 10 scope

#### [Task Description]

Freeze entry behavior into one explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- supported default entry semantics,
- supported subcommand/argument behavior,
- supported startup/shutdown behavior,
- supported output-path semantics,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/cli_entrypoint_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase10_compat_notes.md`

#### [Task important notes]

If this contract is not explicit, later cutover work will quietly rewrite it.

#### [Task check list]

- [ ] Entry behavior is documented
- [ ] Subcommand behavior is documented
- [ ] Startup/shutdown rules are documented
- [ ] Output-path rules are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit contract for supported CLI and entrypoint compatibility.
