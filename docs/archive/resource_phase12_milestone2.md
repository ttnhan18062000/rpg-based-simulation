---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 2] - Supported Runtime Entrypoint and Consumer Cutover

## [Milestone Description]

Milestone 2 moves the supported entry and consumer-facing runtime surface to `src`.

Its purpose is to make `src` the default operational runtime for the cutover-allowed surface.

This milestone covers:

- supported CLI/entry usage,
- supported runtime server/serve paths,
- supported consumer entrypoints,
- supported headless/default runtime invocation,
- and supported direct operator-facing execution paths.

It is about real operational routing, not new feature work.

It does not yet close CI/release workflow migration or full operational artifact transition.

## [Milestone technical implementation]

Cut over supported runtime entry surfaces to `src` in a controlled way.

This milestone must:

- switch supported default entrypoints to `src`,
- switch supported serve/headless/runtime consumers to `src`,
- preserve explicit constraints for unsupported or divergent surfaces,
- validate that operator-visible behavior remains within the ratified cutover boundary,
- and keep fallback/rollback paths visible while cutover is still in progress.

This milestone must not:

- silently reroute unsupported consumers,
- treat partial entry migration as full operational cutover,
- or blur cutover success with residual dual-runtime behavior.

## [Milestone important notes]

The trap here is fake defaultness.

If old `src` is still the thing people really depend on, then you have not cut over, no matter what the roadmap says.

## [Milestone acceptance criteria]

At the end of Milestone 2:

- supported runtime entrypoints default to `src`,
- supported consumers run through `src`,
- unsupported/divergent surfaces remain constrained,
- and the project has one credible runtime-entry cutover slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit all supported runtime entrypoints and direct consumer execution paths before switching defaults

#### [Task Description]

Map the real operational runtime surface before changing it.

#### [Task technical implementation]

Review all Phase 12-supported runtime entry surfaces and confirm:

- current routing path,
- old `src` dependency points,
- `src` equivalent path,
- operator-visible contract expectations,
- and rollback/fallback dependencies.

#### [Task possible affected files]

- `src/__main__.py`
- `src/__main__.py`
- runtime entry docs
- `docs/engine/phase12_cutover_ownership.md`

#### [Task important notes]

Do not switch defaults before you know which entrypaths are still genuinely live.

#### [Task check list]

- [x] Current runtime paths are mapped
- [x] Old-src dependencies are mapped
- [x] V2 equivalents are mapped
- [x] Contract expectations are explicit
- [x] Audit is reviewable

#### [Task acceptance criteria]

The project has a concrete audit of supported runtime entry and consumer execution paths.

---

### [ ] (checkbox) - [Task 2] - Switch supported default CLI and serve/headless entrypoints to `src`

#### [Task Description]

Make `src` the real default runtime for the supported entry surface.

#### [Task technical implementation]

Update the supported runtime entry surface so cutover-eligible default entrypoints and supported serve/headless paths route to `src` by default.

This task should:

- preserve ratified argument/entry contracts,
- preserve rollback/fallback toggles while needed,
- and avoid rerouting anything outside the approved cutover boundary.

#### [Task possible affected files]

- `src/__main__.py`
- launcher/wrapper scripts
- deployment/runbook docs
- `tests/e2e/**`

#### [Task important notes]

Changing the default without preserving the ratified contract is not cutover. It is a new product.

#### [Task check list]

- [x] Default entry routes to `src`
- [x] Serve/headless routes to `src`
- [x] Allowed fallback remains explicit
- [x] Unsupported scope is not rerouted
- [x] Operator-facing behavior remains bounded

#### [Task acceptance criteria]

Supported runtime entrypoints now default to `src`.

---

### [ ] (checkbox) - [Task 3] - Validate direct operator-facing execution behavior under the new default runtime

#### [Task Description]

Confirm that the switch is operationally real, not just structurally configured.

#### [Task technical implementation]

Run black-box validation on supported operator-facing execution flows, including:

- default launch behavior,
- serve/headless invocation,
- expected output/report paths,
- and basic failure handling under the new routing.

#### [Task possible affected files]

- `tests/e2e/**`
- `tests/cli/**`
- runbook validation notes

#### [Task important notes]

If operators still need old `src` muscle memory to succeed, the cutover is fake.

#### [Task check list]

- [x] Default launch is validated
- [x] Serve/headless launch is validated
- [x] Output/report expectations are validated
- [x] Failure handling is validated
- [x] Validation is documented

#### [Task acceptance criteria]

Supported operator-facing execution behavior is validated under the `src` default runtime.

---

### [ ] (checkbox) - [Task 4] - Publish the supported runtime-entry cutover baseline

#### [Task Description]

Turn runtime cutover from a config change into an explicit operational fact.

#### [Task technical implementation]

Publish one runtime cutover baseline summarizing:

- what entrypoints now default to `src`,
- what consumers are now served by `src`,
- what fallback still exists,
- and what remains outside the cutover boundary.

#### [Task possible affected files]

- `docs/engine/phase12_runtime_cutover_baseline.md`
- `docs/engine/phase12_entry_package.md`
- `docs/engine/phase12_cutover_allowed_surface.md`

#### [Task important notes]

This artifact should be boring and precise, not celebratory.

#### [Task check list]

- [x] New defaults are explicit
- [x] New consumer routing is explicit
- [x] Remaining fallback is explicit
- [x] Out-of-scope paths are explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

The project has one explicit supported runtime-entry cutover baseline.
