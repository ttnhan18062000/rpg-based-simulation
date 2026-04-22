# [Milestone 2] - Authoritative Action and Typed Update Substrate Closure

## [Milestone Description]

Milestone 2 closes the remaining authoritative action/update representation model.

Its purpose is to ensure that gameplay intent and gameplay side effects are represented as structured authoritative substrate objects rather than hidden mutation behavior.

This milestone is about representation, not authoritative application.

It covers:

- action proposal structure,
- typed authoritative update structure,
- reason and target normalization,
- and the separation between worker thought and authoritative state mutation.

It does not yet close conflict resolution or apply-path behavior itself.

## [Milestone technical implementation]

Complete the authoritative action/update substrate in a way that matches both the preserved legacy replacement surface and the V2 authority model.

This milestone must:

- close remaining gaps in typed action proposal structure,
- close remaining gaps in typed update buckets or equivalent authoritative update domains,
- normalize legacy reason/target shapes into structured representations where required,
- ensure worker-side code produces intent rather than direct world mutation,
- ensure update structures are granular enough for later partial rejection and replay visibility,
- and eliminate or fence off hidden mutation paths that bypass authoritative substrate models.

This milestone must not:

- treat partially typed structures as complete closure,
- absorb apply-path behavior into representation-layer tasks,
- or preserve legacy shape leaks that weaken authoritative intent/update truth.

## [Milestone important notes]

The trap here is accepting a substrate that is “typed in some places” but still semantically fuzzy.

If action intent and authoritative side effects are still fuzzy, later phases will keep re-embedding logic in the wrong layer.

## [Milestone acceptance criteria]

At the end of Milestone 2:

- authoritative action intent shape is explicit,
- authoritative update shape is explicit,
- reason/target structure is normalized where required,
- worker-side mutation shortcuts are no longer part of supported behavior,
- and one authoritative action/update substrate exists for later phases.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit Phase 7 action/update rows against the current `src_v2` substrate implementation

#### [Task Description]

Start from evidence, not assumptions.

#### [Task technical implementation]

Review all Phase 7 action/update substrate rows and map them to current `src_v2` implementation points.

Identify:

- already closed structures,
- partially typed structures,
- legacy coercion points still in use,
- and direct-mutation shortcuts still bypassing the intended substrate.

#### [Task possible affected files]

- `src_v2/core/**`
- `src_v2/engine/**`
- `src_v2/actions/**`
- `docs/engine/replacement_ledger.md`
- `docs/engine/phase7_backlog.md`

#### [Task important notes]

Do not start coding before you know which substrate gaps are real.

#### [Task check list]

- [ ] Current representation points are mapped
- [ ] Partial structures are identified
- [ ] Mutation shortcuts are identified
- [ ] Coercion gaps are identified
- [ ] Audit notes are reviewable

#### [Task acceptance criteria]

The project has a concrete gap audit for Phase 7 action/update substrate rows.

---

### [ ] (checkbox) - [Task 2] - Complete the authoritative action proposal model for supported substrate scope

#### [Task Description]

Make action intent explicit, structured, and stable.

#### [Task technical implementation]

Refine or complete the action proposal model so it can carry the supported substrate truth without hidden side effects.

This task should:

- close missing fields needed for authoritative intent,
- normalize actor/verb/target/reason/update linkage,
- ensure proposal shape is deterministic and serialization-safe,
- and reject convenience fields that smuggle world mutation state into intent objects.

#### [Task possible affected files]

- `src_v2/actions/**`
- `src_v2/core/models/**`
- `tests_v2/**`
- substrate contract docs

#### [Task important notes]

An action proposal is intent, not a half-applied world diff.

#### [Task check list]

- [ ] Proposal shape is explicit
- [ ] Intent fields are complete for supported scope
- [ ] Serialization shape is stable
- [ ] Hidden mutation payloads are avoided
- [ ] Proposal model remains deterministic

#### [Task acceptance criteria]

The supported substrate has one explicit authoritative action proposal model.

---

### [ ] (checkbox) - [Task 3] - Complete the typed authoritative update model and update-domain boundaries

#### [Task Description]

Make authoritative side effects explicit and domain-aware.

#### [Task technical implementation]

Refine or complete the typed update model so side effects are represented through explicit authoritative domains.

This task should:

- define or finish update-domain buckets,
- ensure each supported side effect maps into one or more explicit update types,
- avoid “miscellaneous” escape hatches that collapse semantics,
- and keep update granularity sufficient for later partial-rejection safety.

#### [Task possible affected files]

- `src_v2/core/models/**`
- `src_v2/engine/**`
- `src_v2/apply/**`
- `tests_v2/**`

#### [Task important notes]

A giant generic update payload is just legacy ambiguity wearing type hints.

#### [Task check list]

- [ ] Update domains are explicit
- [ ] Side effects map into typed updates
- [ ] Escape-hatch blobs are avoided
- [ ] Granularity is sufficient for later rejection isolation
- [ ] Update model remains supportable

#### [Task acceptance criteria]

The supported substrate has one typed authoritative update model with explicit domain boundaries.

---

### [ ] (checkbox) - [Task 4] - Normalize legacy reason and target coercion into supported structured representations

#### [Task Description]

Stop carrying loose legacy shapes into authoritative substrate truth.

#### [Task technical implementation]

Identify any remaining legacy-style reason or target representations and normalize them into structured V2 models.

This task should:

- define supported coercion rules,
- remove ad hoc parsing behavior,
- preserve only required legacy compatibility where explicitly justified,
- and ensure coercion outputs are deterministic and documented.

#### [Task possible affected files]

- `src_v2/actions/**`
- `src_v2/core/models/**`
- `tests_v2/parity/**`
- docs for structured reason/target contract

#### [Task important notes]

Legacy compatibility is not an excuse for substrate fuzziness.

#### [Task check list]

- [ ] Loose reason shapes are identified
- [ ] Loose target shapes are identified
- [ ] Coercion rules are explicit
- [ ] Ad hoc conversions are removed
- [ ] Outputs are deterministic

#### [Task acceptance criteria]

Supported legacy reason/target inputs are normalized into explicit structured representations.

---

### [ ] (checkbox) - [Task 5] - Eliminate or fence off worker-side direct mutation paths that bypass authoritative substrate models

#### [Task Description]

Enforce the rule that worker thought emits intent, not world mutation.

#### [Task technical implementation]

Audit worker-side decision paths and remove or isolate any code that directly mutates authoritative world state outside the intended substrate.

This task should:

- redirect mutation into authoritative intent/update paths,
- add tripwires or guardrails where feasible,
- and narrow support claims if any legacy shortcut must remain temporarily.

#### [Task possible affected files]

- `src_v2/engine/**`
- `src_v2/ai/**`
- `src_v2/core/state/**`
- `tests_v2/**`

#### [Task important notes]

If worker thought can still mutate authority directly, the substrate is not closed.

#### [Task check list]

- [ ] Direct mutation shortcuts are audited
- [ ] Supported paths emit intent instead of mutation
- [ ] Guardrails are added where needed
- [ ] Temporary exceptions are documented if any remain
- [ ] Support claims match actual enforcement

#### [Task acceptance criteria]

Worker-side direct mutation is no longer part of supported authoritative behavior.

---

### [ ] (checkbox) - [Task 6] - Add direct contract tests for action/update substrate structure and mutation boundaries

#### [Task Description]

Prove the substrate model directly instead of only through higher-level gameplay behavior.

#### [Task technical implementation]

Add focused tests for:

- action proposal shape,
- typed update shape,
- reason/target normalization,
- no-direct-mutation boundaries,
- and serialization stability for supported substrate objects.

#### [Task possible affected files]

- `tests_v2/core/test_action_proposal_contract.py`
- `tests_v2/core/test_typed_update_contract.py`
- `tests_v2/core/test_reason_target_coercion.py`
- `tests_v2/core/test_no_worker_direct_mutation.py`

#### [Task important notes]

Do not rely only on downstream behavior tests to prove substrate closure.

#### [Task check list]

- [ ] Proposal contract tests exist
- [ ] Update contract tests exist
- [ ] Coercion tests exist
- [ ] Mutation-boundary tests exist
- [ ] Tests are part of standard validation flow

#### [Task acceptance criteria]

The authoritative action/update substrate is directly proven by focused contract tests.

---

### [ ] (checkbox) - [Task 7] - Publish the authoritative action/update substrate contract for Phase 7

#### [Task Description]

Freeze the substrate representation model into an explicit reference artifact.

#### [Task technical implementation]

Publish one substrate contract package describing:

- supported action intent shape,
- supported typed update shape,
- normalization rules,
- mutation-boundary rules,
- and known exclusions.

#### [Task possible affected files]

- `docs/engine/action_update_substrate_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase7_substrate_notes.md`

#### [Task important notes]

If the contract is not explicit, later phases will reinterpret the substrate in their own image.

#### [Task check list]

- [ ] Intent shape is documented
- [ ] Update shape is documented
- [ ] Coercion rules are documented
- [ ] Mutation boundaries are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit authoritative action/update substrate contract.
