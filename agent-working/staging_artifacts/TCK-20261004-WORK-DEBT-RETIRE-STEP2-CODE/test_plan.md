---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE
date: 2026-10-08
tags: [performance, engine, determinism]
---

# Test plan (design): TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE

Method: `grep` and an AST scan of `tests/`, `data/`, `config/`, `docs/` against `origin/main` `5e0994837`. 64 test files mention one of: `work_debt`, `DRAIN_DEBT`, `PeriodicDefinition`, `periodic_due_ticks`, `periodic_updates`, `allow_opportunistic`, `diagnostic_verbosity`, `metrics_detail`, `work_debt_update`, `sim_work_debt`, `WORK_DEBT_BUILDUP`, `inject_work_debt`, `systems_with_debt`.

## 1. Every pinned hash and golden fixture that moves (the PR must list these)

| # | Pin | Where | What happens (Option A, `flat-sha256-v2`) |
|---|---|---|---|
| 1 | `FIXTURE_DIGEST_ON_MAIN = "ec75b106..."` | `tests/unit/engine/test_proof_digest_contract.py:31` | **Moves.** The fixture (`_fixed_state`, `:41-47`) passes `work_debt={"B": 2, "A": 1}`; under v2 the field is gone, so the fixture changes and the digest is recomputed once under v2 and re-pinned as `FIXTURE_DIGEST_V2`; the v1 value stays as a comment ("historical, never compared"). The "byte-identity with main" test (`:1-2` docstring) becomes a v2 pin; the stale-cache and certification-harness-equals-`get_hash` tests are unaffected |
| 2 | `tests/unit/kernel/golden/live_signals_v1.json` (32 `work_debt_total` keys) | Phase A's Live-bit-identical fixture | **Mechanical key removal** (`"work_debt_total": 0` from every `start` / `end` row), not a re-record; `test_live_signal_golden.py` drops the key from its comparison. A re-record is not needed because no other Live value changes |
| 3 | `tests/unit/engine/test_kernel_digest_via_scheduler.py:22, 62, 68` | uses `PROOF_DIGEST_SCHEME` the constant | no change (reads the constant) |
| 4 | the 21 tracked `data/worlds/*/world_compile_report.json` | `canonical_state_hash` (v1) | **No test moves.** `test_resolved_snapshot_freshness.py:83-85, 107-121` compares counts only and says the hashes are already stale; they stay and are described as v1 in the docs |
| 5 | `tests/regression/baseline_5k.json` | keys `version, generated_at, world_id, seed, ticks, ..., metrics` | no digest in it |
| 6 | `tests/perf/baselines/*.json`, `docs/observability/baselines/*.json` | timing baselines | no `hash` / `digest` / `fingerprint` field (scanned) |
| 7 | `tests/mutation/baselines/*.json` and other 64-hex hits under `tests/` | content hashes of source or world files | unrelated to the state digest |
| 8 | replay chunks under `data/runs/` | untracked run leftovers | not goldens; `TICK_END` carries `scheme`, so old ones read as v1 |
| 9 | `tools/perf/hash_callsite_inventory.py:52` and `docs/performance/hash_callsite_inventory.{md,json}` | the string `flat-sha256-v1` in the generated inventory | regenerate with the tool (`--update-doc`, `--format json`), `--check` must pass |
| 10 | tests that compare a fresh hash with a fresh hash (determinism, replay fidelity, certification parity, `test_world_compile_determinism`, `test_behavioral_5k`) | many | **do not move**: both sides are computed under the same scheme |

Under Option B (keep v1, constant `{}` keys) rows 1, 2 (the digest literal part) and 9 do not move; row 2's key removal still happens.

**Scan scope (added during C2):** the search for pinned values covers the **scheme strings** (`flat-sha256-v1`) as well as hash literals. C2 found a second literal of the scheme name at `tests/unit/engine/test_hash_scheduler.py:117` that the first scan (hash literals only) missed.

**Running list of moved pins for the PR body:** `FIXTURE_DIGEST_V2 = 631feb2b...` (new) and `FIXTURE_DIGEST_V1_ON_MAIN` (history, used only by the migration proof); the `test_hash_scheduler.py:117` scheme literal; the `hash_callsite_inventory` string and its generated docs; in C3 the `live_signals_v1.json` golden's `work_debt_total` keys and the certification result key list (with a schema-version note). The 21 tracked `world_compile_report.json` files keep v1 (documented in C4).

## 2. Tests that change, by reason

**Delete or replace (they exist only for removed behaviour):**
- `tests/integration/kernel/test_work_debt_stays_empty_in_production.py` -> replaced by `test_work_debt_is_gone.py`: `AuthoritativeState`, `StateUpdate`, `PressureSignals`, `RuntimeProfile` and `GovernorPolicy` have no such field; `CanonicalStateHasher.to_canonical_data` has neither key; `DeterministicScheduler.select_work` returns only entity work; `scheduler.PeriodicDefinition` and `executor`'s `DRAIN_DEBT` branch do not exist.
- `tests/unit/core/test_deferred_work_debt.py`, `tests/unit/core/test_degradation_order.py`, `tests/unit/core/test_work_classes.py` (register test-only `PeriodicDefinition`s or seed `work_debt`): delete the cases for removed behaviour; keep the entity-ordering cases that still hold (rewritten without the removed arguments).
- `tests/unit/kernel/test_scheduler_contract.py` (15 hits): rewrite to the entity-only scheduler contract (determinism, LOD, readiness, sort key); delete the periodic and non-authoritative-drop cases.
- `tests/unit/core/test_signal_truth.py` (the `opt_task` periodic definition at `:120`): keep the signal-truth checks, drop the periodic definition and `work_debt_total`.
- `tests/unit/perf/test_long_run_harness_debt.py` (PERF-D3 accounting): delete; the harness loses `work_debt` and `systems_with_debt`.
- `tests/integration/kernel/test_milestone_c_desimulation.py` (DRAIN_DEBT resolved through the executor): delete the DRAIN_DEBT cases; keep anything about entity work.
- `tests/integration/kernel/test_tied_worker_result_order.py` and `tests/unit/core/test_protocol_validator_system_results.py` (the #319 rule and the tie analysis, ID-zero system results): delete the system-result and `work_debt` cases; keep the entity-result tie ordering.
- `tests/integration/observability/test_kernel_event_recording.py` (seeds `state.work_debt` above the profile's `max_work_debt`): rewrite to drive the governor to a non-NORMAL mode some other way (the `_Pinned` governor seam used in `test_canonical_signal_contract.py`).
- `tests/integration/pipeline/test_authoritative_apply.py` (`periodic_due_ticks={"P1": 10}`, 4 hits) and `test_state_isolation.py` (`work_debt={"ENTITY_BRAIN": 0}`): remove the arguments and the assertions on them.
- Cooperation OFF path (two tests, the only ones that set the `social_cooperation_disabled` sentinel): `tests/unit/domains/cooperation/test_cooperation_phase.py` (`_state_flag_off` and the test at `:128`) and `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py:125`. The sentinel no longer exists as state; the supported OFF switch is the feature flag `ENABLE_SOCIAL_COOPERATION` (`pipeline.py:218`). Rewrite them to turn the flag off through the pipeline's flag manager, or delete if `test_feature_flags` already covers the OFF path (decide with rpg-planner; the phase file itself is not edited).

**Constructor and field clean-up (mechanical):** 24 files that pass only `work_debt={}` / `periodic_due_ticks={}` to `AuthoritativeState` (listed by the inventory scan: the `tests/perf/test_phase*_budget.py` trio and the `tests/unit/domains/{information,combat_engagement}`, `tests/unit/strategic`, `tests/integration/domains` and `tests/integration/scenarios` files), plus `max_work_debt=` arguments in 15 test files (ignored today by pydantic). Do these in C0, before the slot: valid before and after.

**Value-bearing fields in certification and observability tests:** `test_manifest_snapshot.py`, `test_recorder_refactor.py`, `test_cert_result_serialization.py` (`:248` pins the result key list, including `work_debt`), `test_allowed_failure_truth.py`, `test_artifact_budget.py`, `test_evidence_levels.py` (mock state with `periodic_due_ticks`), `tests/observability/test_metrics_export.py`, `test_live_snapshot_provider.py`, `test_observability_hardening.py` (`"work_debt_total": 0` in snapshot dicts): drop the field; update the pinned key list; add a schema-version note for the certification artifact.

**Governor and profile tests** (`test_resource_governor_contract.py`, `test_phase_budget_governor.py`, `test_anti_thrashing.py`, `test_milestone_b_closure.py`, `test_milestone_d_closure.py`, `test_minimal_kernel.py`, `test_substrate_freeze_m1.py:` `profile.max_work_debt = 1000`): remove the debt cases and the `max_work_debt` arguments; the threshold cases for tick cost, memory, utilization and replay stay untouched.

**Phase A tests that name the field:** `test_canonical_signal_contract.py` (`PressureSignals(work_debt_total=0, ...)` in `test_audit_mode_still_zeroes...`), `test_run_manifest_signal_contract.py` and `test_kernel_provenance_manifest_load.py` (`max_work_debt=` in profile builders).

## 3. New tests

1. `test_work_debt_is_gone.py` (above).
2. `test_proof_digest_contract.py`: the v2 pin; plus "the canonical data has exactly the expected key set" so a re-added key fails loudly; plus "scheme is `flat-sha256-v2`" (Option A).
3. Governor behaviour unchanged on non-combat runs (AC 3): the Live golden fixture (modes and signals, minus the removed key) and `test_milestone_b_closure` already pin modes; add one run on a non-combat scenario asserting the mode sequence equals the sequence recorded on `origin/main` before the change (recorded in C0, committed as a small fixture).

## 4. Order inside the PR, and what runs when

C0 (tests-only, before the slot): run the touched files plus `tests/unit/tools`. C1-C3: after each commit, the lanes named in `plan.md` section 6; before the PR, the whole list once more on the merged tree.

## 5. Mutation proofs

- `test_work_debt_is_gone`: re-add the `work_debt` key to `to_canonical_data`; the key-set test fails.
- `test_proof_digest_contract`: change one canonical field's rendering; the v2 pin fails.
- AC 3 mode-sequence test: lower `max_tick_budget_ms` in the recorded profile after recording; the sequence changes (non-vacuity).
