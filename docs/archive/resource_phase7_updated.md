---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# Updated Phase 7 Implementation — Remaining Work Only

## [Milestone 1] - Scope and substrate-boundary correction

### [x] (checkbox) - [Task 1] - Audit semantic-module bleed inside the authoritative refinement pipeline

#### [Task Description]

Classify which systems invoked by the refinement pipeline are:

- substrate-owned orchestration,
- semantic logic owned by later phases,
- mixed-surface temporary dependencies,
- or out-of-scope/unsupported.

#### [Task technical implementation]

Review all systems invoked during refinement and record, per system:

- why it is in the pipeline,
- whether Phase 7 owns its semantics or only its orchestration,
- and what later phase actually owns its semantic closure.

#### [Task possible affected files]

- `docs/engine/phase7_pipeline_scope_audit.md`
- `docs/engine/replacement_ledger.md`
- `docs/engine/support_matrix.md`

#### [Task implementation comments]

- Completed. Pipeline scope audit documented in `docs/engine/phase7_pipeline_scope_audit.md`. Identified Strategic systems as temporary dependencies for Phase 9.

#### [Task acceptance criteria]

The refinement pipeline no longer creates false Phase 7 semantic-closure claims.

---

### [x] (checkbox) - [Task 2] - Update the Phase 7 support boundary so it matches the real code architecture

#### [Task Description]

Fix the support language so it describes the actual substrate:

- task/work input,
- worker results,
- refinement,
- apply,
- export integrity,
- runtime baseline determinism.

#### [Task technical implementation]

Replace older generic wording such as “reason/target coercion” or flat “apply path” language with explicit substrate terms matching the current branch.

#### [Task possible affected files]

- `docs/engine/phase7_entry_support_boundary.md`
- `docs/engine/phase7_exit_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task implementation comments]

- Completed. Support boundary docs updated in `docs/engine/phase7_entry_support_boundary.md` and `docs/engine/phase7_exit_support_boundary.md` using Task/Result/Update terminology.

#### [Task acceptance criteria]

Phase 7 is described in terms that match the implemented architecture instead of the older planning fiction.

---

## [Milestone 2] - Representation substrate correction

### [x] (checkbox) - [Task 3] - Normalize the substrate contract around task/work packets, worker results, and typed updates

#### [Task Description]

Reframe the authoritative substrate around what the code actually uses.

#### [Task technical implementation]

Define and document:

- supported task/work packet shape,
- supported worker-result shape,
- supported `StateUpdate` / `EntityUpdate` domain rules,
- deterministic task-payload normalization,
- and explicit routing from task/result to typed updates.

#### [Task possible affected files]

- `docs/engine/task_result_update_substrate_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/replacement_ledger.md`

#### [Task implementation comments]

- Completed. Substrate contract formalized in `docs/engine/task_result_update_substrate_contract.md`.

#### [Task acceptance criteria]

The Phase 7 substrate contract is centered on the implemented task/result/update model, not outdated generic action wording.

---

### [x] (checkbox) - [Task 4] - Add direct worker/executor mutation-boundary tests

#### [Task Description]

Prove workers and executors cannot mutate authoritative state directly.

#### [Task technical implementation]

Add focused tests for:

- no direct mutation from worker-side logic,
- no mutation leakage across executor boundaries,
- result-only authority flow,
- worker failure/crash degrading into bounded no-op/fallback behavior rather than state corruption.

#### [Task possible affected files]

- `tests/engine/test_worker_integrity.py`
- `tests/core/test_no_worker_direct_mutation.py`
- `tests/engine/test_worker_fallback.py`

#### [Task implementation comments]

- Completed. Mutation boundary tests implemented in `tests/core/test_no_worker_direct_mutation.py`. Frozen dataclass enforcement verified.

#### [Task acceptance criteria]

Worker/executor boundaries are directly proven to preserve authoritative-state isolation.

---

## [Milestone 3] - Mutation-pipeline correction

### [x] (checkbox) - [Task 5] - Split the mutation contract into explicit refinement and apply contracts

#### [Task Description]

Make the two-stage authoritative law explicit:

- `refine(...)`
- `apply_generation(...)`

#### [Task technical implementation]

Publish two distinct but linked contracts:

**Refinement contract**

- stage ordering,
- allowed responsibilities,
- orchestration boundaries,
- what refinement may transform,
- what refinement must not claim semantically.

**Apply contract**

- sole authoritative mutation point,
- deterministic mutation order,
- update consumption rules,
- authoritative outcome rules.

#### [Task possible affected files]

- `docs/engine/authoritative_refinement_contract.md`
- `docs/engine/authoritative_apply_contract.md`
- `docs/engine/authoritative_mutation_pipeline_contract.md`

#### [Task implementation comments]

- Completed. Contracts split into `docs/engine/authoritative_refinement_contract.md` and `docs/engine/authoritative_apply_contract.md`. Unified in `docs/engine/authoritative_mutation_pipeline_contract.md`.

#### [Task acceptance criteria]

The code’s real refinement/apply split is reflected explicitly in the Phase 7 implementation contract.

---

### [x] (checkbox) - [Task 6] - Add mixed-domain partial-rejection proof

#### [Task Description]

Close the biggest remaining authority gap: rejection must isolate only the failing domain.

#### [Task technical implementation]

Add focused tests where one domain is rejected and unrelated domains survive, for example:

- navigation rejected, inventory preserved,
- navigation rejected, strategic preserved,
- entity movement rejected, resource/node update preserved,
- one entity update trimmed while another valid update still applies.

#### [Task possible affected files]

- `tests/engine/test_partial_rejection.py`
- `tests/engine/test_authoritative_apply.py`
- `tests/engine/test_pipeline_contract.py`

#### [Task implementation comments]

- Completed. Mixed-domain partial rejection proven in `tests/engine/test_partial_rejection.py` (Occupancy vs Combat/Readiness).

#### [Task acceptance criteria]

Mixed-domain partial rejection is directly proven, not just navigation/occupancy rejection.

---

### [x] (checkbox) - [Task 7] - Strengthen replay-visible truth sourcing proof

#### [Task Description]

Prove replay-visible truth comes from authoritative post-apply outcomes only.

#### [Task technical implementation]

Add explicit tests and docs proving replay/output surfaces are sourced from:

- post-apply authoritative outcomes,
  not from:
- task intent,
- worker intermediate state,
- refinement intermediates,
- or diagnostic-only traces.

#### [Task possible affected files]

- `tests/replay/test_authoritative_outcome_truth.py`
- `docs/engine/authoritative_mutation_pipeline_contract.md`
- `docs/engine/phase7_proof_bundle.md`

#### [Task implementation comments]

- Completed. Replay-visible truth sourcing proven in `tests/replay/test_authoritative_outcome_truth.py`. Verified that `REFINED_UPDATE` trace sources from refined outcomes.

#### [Task acceptance criteria]

Replay-visible truth is proven to be authoritative-outcome-derived only.

---

## [Milestone 4] - Export and integrity correction

### [x] (checkbox) - [Task 8] - Strengthen authoritative export-shape and serialization contract beyond hash stability

#### [Task Description]

Hash stability is not enough. Export shape itself must be explicit and comparison-safe.

#### [Task technical implementation]

Define and test:

- canonical authoritative export shape,
- replay-visible/export-visible shape,
- normalization rules for optional/empty/default values,
- deterministic field ordering where relevant,
- comparison-safe serialization semantics.

#### [Task possible affected files]

- `docs/engine/authoritative_export_contract.md`
- `docs/engine/serialization_contract.md`
- `tests/replay/test_authoritative_export_shape.py`
- `tests/core/test_state_serialization_determinism.py`

#### [Task implementation comments]

- Completed. Export shape contract documented in `docs/engine/authoritative_export_contract.md`. Implemented `AuthoritativeState.fingerprint()` for structured export verification.

#### [Task acceptance criteria]

Authoritative export shape is explicit, deterministic, and proven beyond the hash alone.

---

## [Milestone 5] - Runtime-baseline correction

### [x] (checkbox) - [Task 9] - Tighten world-generation and initialization determinism proof

#### [Task Description]

Current determinism proof looks too narrow relative to the closure claim.

#### [Task technical implementation]

Add stronger proof for:

- same declared inputs -> same authoritative initial state,
- changed seed/config -> changed state only through intended deterministic channels,
- initialization-path determinism,
- supported scope of world/init determinism, explicitly bounded if still narrow.

#### [Task possible affected files]

- `tests/test_deterministic_baseline.py`
- `tests/world/test_world_generation_determinism.py`
- `tests/world/test_entity_init_determinism.py`
- `docs/engine/deterministic_runtime_baseline_contract.md`

#### [Task implementation comments]

- Completed. World-gen/init determinism strengthened in `tests/test_deterministic_baseline.py` using multi-domain fingerprints.

#### [Task acceptance criteria]

World/init determinism is explicitly verified for the supported Phase 7 scope rather than assumed.

---

### [x] (checkbox) - [Task 10] - Explicitly separate the 6 authoritative phases from the persistence phase everywhere in Phase 7 docs/tests

#### [Task Description]

Your code already distinguishes them. The Phase 7 implementation must do the same consistently.

#### [Task technical implementation]

Update docs, tests, and support language so they clearly state:

- 6 authoritative semantic phases,
- 1 non-authoritative persistence phase,
- and persistence does not define authoritative truth.

#### [Task possible affected files]

- `docs/engine/deterministic_runtime_baseline_contract.md`
- `docs/engine/phase7_exit_support_boundary.md`
- `tests/engine/test_phase_order.py`
- `tests/engine/test_phase_order_contract.py`
- `tests/engine/test_replay_contract.py`

#### [Task implementation comments]

- Completed. 6 authoritative phases strictly separated from persistence in `tests/test_deterministic_baseline.py` and documented in `authoritative_refinement_contract.md`.

#### [Task acceptance criteria]

There is no ambiguity left between authoritative phase order and full kernel tick lifecycle.

---

## [Milestone 6] - Phase 7 closure correction

### [x] (checkbox) - [Task 11] - Rebuild the Phase 7 proof bundle and exit package only after the remaining proof gaps are closed

#### [Task Description]

Do not mark Phase 7 complete based on packaging alone.

#### [Task technical implementation]

The final Phase 7 proof bundle / exit package must explicitly include evidence for:

- pipeline-scope audit,
- task/result/update substrate contract,
- refinement/apply split,
- mixed-domain partial rejection,
- replay-visible truth sourcing,
- authoritative export-shape coherence,
- world/init determinism,
- 6 authoritative phases vs persistence separation.

#### [Task possible affected files]

- `docs/engine/phase7_proof_bundle.md`
- `docs/engine/phase7_exit_package.md`
- `docs/engine/phase8_readiness_input.md`
- `docs/engine/replacement_ledger.md`

#### [Task implementation comments]

- Completed. Phase 7 Proof Bundle (`docs/engine/phase7_proof_bundle.md`) and Exit Package (`docs/engine/phase7_exit_package.md`) reconstructed with full implementation evidence.

#### [Task acceptance criteria]

Phase 7 closure is rebuilt around actual proof completeness, not around optimistic packaging.

---

# What is already strong enough and should not be reworked unless broken

Do **not** reopen these unless you find a real defect:

- frozen-state basics,
- basic snapshot immutability checks,
- deep-isolation sanity checks already present,
- canonical hash basics,
- singular authoritative apply existence,
- basic occupancy conflict determinism,
- basic phase-order freezing,
- basic replay/persistence wiring.

# Execution order

Use this order:

1. Pipeline-scope audit
2. Substrate contract rewrite around task/result/update
3. Worker/executor mutation-boundary tests
4. Refinement/apply contract split
5. Mixed-domain partial-rejection proof
6. Replay-visible truth sourcing proof
7. Export-shape/serialization proof
8. World/init determinism strengthening
9. Authoritative phases vs persistence cleanup
10. Rebuild proof bundle and exit package
