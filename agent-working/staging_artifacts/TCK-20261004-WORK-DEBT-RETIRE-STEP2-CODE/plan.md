---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE
date: 2026-10-08
tags: [performance, engine, determinism]
---

# Plan (design): TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE (Phase B)

Design only; nothing here is implemented. Evidence is in `investigation.md`. Goal: the RPG slot is spent on code only, so every decision below is made before it opens.

## 1. What the change is

Remove, in one PR and four code commits: `AuthoritativeState.work_debt` and `periodic_due_ticks`; `StateUpdate.work_debt_updates` and `periodic_updates`; the apply clamp and merge; the kernel's merge of ID-zero system results; `PeriodicDefinition` and the periodic, deferred (`DRAIN_DEBT`) and opportunistic scheduler branches; the unread policy fields (`allow_non_authoritative_periodic`, `allow_opportunistic`, `diagnostic_verbosity`, `metrics_detail`); `WorkerResult.work_debt_update` / `subsystem_id` and the validator's per-subsystem rule; `PressureSignals.work_debt_total` and the debt thresholds in both governors; `max_work_debt`; and the reporting surfaces (API, snapshot, `sim_work_debt_total`, certification model and scenario, long-run harness fields). The proof digest loses two keys, so it gets a new scheme (owner question 1).

Behaviour on shipped runs does not change: the governor never saw a non-zero debt, the scheduler never had a definition, and `pipeline.py` has no reference. What changes is the bytes of every state digest.

## 2. OWNER QUESTIONS (need an answer before the slot)

**Q1. PERF-D5: how does the digest scheme change?**
- **Option A (recommended, the ticket's stated plan): `flat-sha256-v2`.** `CanonicalStateHasher.to_canonical_data` stops writing `periodic_due_ticks` and `work_debt`; nothing else in the canonical JSON changes (same `sort_keys`, same separators). `PROOF_DIGEST_SCHEME` becomes `"flat-sha256-v2"`; `TICK_END` payloads and `ProofDigest` carry it automatically. Cost: every state digest changes once; the only literal pin in `tests/` is `FIXTURE_DIGEST_ON_MAIN` (`test_proof_digest_contract.py:31`), plus its fixture, which carries `work_debt`. Gain: the canonical form has no dead keys, and the scheme history is honest.
- **Option B: keep `flat-sha256-v1` and write the two keys as constant `{}`.** Zero digests move and nothing is re-pinned, but the canonical form carries two permanent dead keys and the removed fields live on in the hash. Cheaper by about 0.5 day; rejected unless the owner prefers zero churn.
- **Compatibility rule (both options):** a digest is comparable only with a digest of the same scheme; v1 and v2 values are never compared. No code in `src/` reads a stored digest or replay back, so no loader changes. Stored copies are labelled by use: `TICK_END` already carries `scheme`; the 21 tracked `data/worlds/*/world_compile_report.json` files keep their v1 `canonical_state_hash` (they are already stale on hashes by design, `test_resolved_snapshot_freshness.py:83-85` compares counts only) and are described as v1 in the docs; certification artifacts and the long-run `final_state_hash` get the scheme from the run's code version, and I propose recording `proof_digest_scheme` next to them (certification `models.py`, long-run harness; see Q2). v1 is not kept alive as a compute path: the engine computes v2 only; the v1 value of the pinned fixture is recorded as a historical comment.

**Q2. Files outside gate item 7's Phase B list.** Phase B's list is `state.py`, `apply.py`, `checkpoint.py`, `updates.py`, `scheduler.py`, `policy.py` and the ticket's reporting surfaces. Needing owner OK in addition:
- the Phase A files, released to the RPG lanes on 2026-10-08, reopened: `kernel.py` (4 lines: `:611, 623-624, 642`), `governor.py` (4 lines), `phase_governor.py` (2 lines), `src/core/governance.py` (1 field + a comment), `src/config/profiles.py` (`max_work_debt` x5), `runtime_status.py` (1 line), `signal_source.py` (4 lines);
- `src/engine/executor.py` (two `DRAIN_DEBT` branches), `src/engine/domain_logic.py` (`drain_debt`), `src/core/worker_protocol.py` (two fields), `src/core/protocol_validator.py` (partial lift 1 already covers it), `src/perf/profiles.py:47`, `src/engine/worker_manager.py:258` (a comment; partial lift covers it), `src/observability/understanding/rootcause/rules.py` (title and docstring text only), `tools/perf/hash_callsite_inventory.py:52` (a string);
- `src/engine/pipeline.py`: **not touched.**

**Q3. Not for the owner, for rpg-planner (no edit by us):** `src/domains/cooperation/phase.py:78-80` keeps a dead `periodic_due_ticks` sentinel guard after this change. It stays correct (`hasattr` guard), so we leave the RPG file alone and file the cleanup for them. Two cooperation OFF-path tests change (section 6).

## 3. Files, by gate class

| Class | Files |
|---|---|
| **Core (gated)** | `src/core/state.py` (fields at `:1425-1426`, freeze copy `:1613-1614`), `src/engine/apply.py` (`:314-319, 495-496`), `src/engine/kernel.py` (`:611, 623-624, 642`) |
| **Phase B list** | `src/engine/checkpoint.py` (`:15, 116-117`), `src/core/updates.py` (`:1048-1049, 1091, 1137-1138, 1202-1205, 1267-1268`), `src/engine/scheduler.py`, `src/engine/policy.py`, and the reporting surfaces `src/certification/{scenarios,models,harness}.py`, `src/observability/{prometheus_collector,live/snapshot_provider}.py`, `src/engine/observability.py`, `src/api/engine_manager.py`, `src/perf/long_run_harness.py` |
| **Outside the list (Q2)** | the Phase A files, `executor.py`, `domain_logic.py`, `worker_protocol.py`, `protocol_validator.py`, `perf/profiles.py`, `worker_manager.py`, `rootcause/rules.py`, `tools/perf/hash_callsite_inventory.py` |
| **Not touched** | `src/engine/pipeline.py`, `src/domains/cooperation/phase.py`, `src/core/work.py`, `src/core/concurrency_law.py` (see below) |

`WorkClass.PERIODIC/OPPORTUNISTIC/DEFERRED` and the `ConcurrencyLaw` priority table stay: they are small constants that existing result-ordering tests use, and removing them widens the change. They become unreachable constants, listed as a follow-up.

## 4. The counter and the two comments

`dropped_work_delta` / `dropped_work_count` stay as telemetry (API consumers read them) and report 0, with the comments fixed at `governance.py:45` and `observability.py:32`: "work the scheduler drops; nothing registers a task that can be dropped, so 0". The divergence entry says so.

## 5. Order of commits (each green on its own), and the estimate

| # | Commit | Content | Est. |
|---|---|---|---|
| C0 | **Pre-slot, tests only, no gate** (optional but recommended) | strip the no-op `work_debt={}` / `periodic_due_ticks={}` keyword arguments from the 24 mechanical test files and the leftover `max_work_debt=` arguments; valid before and after the field removal | 0.5 d, before the slot |
| C1 | Stop producing deferred work | executor `DRAIN_DEBT` branches, `drain_debt`, scheduler periodic / deferred / opportunistic branches, `PeriodicDefinition`, the four policy fields, `WorkerResult` fields, the validator rule, the kernel merge; delete or rewrite the mechanism tests that exist only for them | 1 d |
| C2 | Remove the state fields, bump the scheme | `state.py`, `updates.py`, `apply.py`, `checkpoint.py` (v2), the digest fixture and pin, remaining test constructors, long-run harness | 1 d |
| C3 | Remove the signal and thresholds | `work_debt_total`, `signal_source.py`, `runtime_status.py`, both governors, `max_work_debt`, snapshot, API, Prometheus, certification model and scenario, root-cause text; golden fixture key | 1 d |
| C4 | Docs, parity, divergence, inventories | section 7 | 0.5-1 d |
| C5 | Verify, close, PR | lanes below, closure, `pr_render` | 0.5 d |

Slot cost: **4 to 4.5 working days with C0 done before the slot, 5 days without it.** It fits in 5, with no slack when C0 is skipped.

**Risky parts, in order:**
1. **Every digest moves (Option A).** Any pin I did not find fails late. Mitigation: the inventory found one literal pin; run the full lanes (section 6) before the PR, not only the scoped ones (Phase A's CI missed `tests/unit/tools`).
2. **`state.py`, `apply.py`, `kernel.py` conflicts** with RPG lanes that hold decision-core, biology and need-profile work. Mitigation: the slot is exclusive; rebase onto `origin/main` at the start of each day and push no later than the end of day 5.
3. **64 test files**, 24 purely mechanical. Mitigation: C0; a scripted, reviewed edit for the rest.
4. **Positional construction of `AuthoritativeState` / `StateUpdate`: checked, none.** An AST scan of `src/`, `tests/` and `tools/` finds no call that passes a positional argument to either, so removing fields cannot shift an argument.
5. **Certification artifact schema**: the result dict loses `work_debt` (`models.py:84`, pinned by `test_cert_result_serialization.py:248`). A schema/version note is needed.
6. **Prometheus**: `sim_work_debt_total` disappears; an external scrape or dashboard would lose it. None in the repo.
7. **Code-health and mypy ratchets are blocking from 2026-10-18.** Removal should only improve them; unused imports and the `Kernel.__init__` ceiling need a check, as in Phase A.

## 6. Verification lanes (named, because a scoped run missed a lane in Phase A)

`tests/unit/tools` and `tests/docs` in full; `tests/unit/core`, `tests/unit/kernel`, `tests/unit/engine`, `tests/unit/resource`, `tests/unit/observability`, `tests/unit/perf`; `tests/integration/kernel`, `tests/integration/pipeline`; `tests/certification`; `tests/static`, `tests/architecture`, `tests/parity`; `tests/tools/test_perf_inventories_committed_in_sync.py`; the world-compile determinism and freshness tests; `uv run make code-health` and `uv run make typecheck-py`. Each run as its own foreground step, output read before the next commit.

## 7. Docs, parity, divergence

- **Divergence DEV-019** (class **Stabilized**): work debt and the never-wired periodic / opportunistic path are removed; the digest scheme becomes v2; the dropped-work counter stays at 0 with honest comments. Verification: the "field is gone" test, `test_proof_digest_contract.py`.
- **Parity:** update `INFRA-223` and `INFRA-420` (the tied-result rule loses its system-result half) and `WORLD-117` if its evidence changes; add `INFRA-429` for the v2 scheme and the removed fields (verified, test path = the new "field is gone" test).
- **Docs:** `deterministic_execution.md` (T04 analysis around `:144-145` rewritten: the tie rule now concerns entity results only; the proof-digest paragraph names v2), `resource_governor_degradation_matrix.md` ("designed but unused" note at `:34`, rule at `:39`), `scheduler_work_model_matrix.md`, `scheduler_test_matrix.md`, `extended_certification_test_matrix.md` (`DEGRADED_NORMAL_RECOVERY`, `WORK_DEBT_BUILDUP`), `resource_governor_contract.md`, `signal_truth_contract.md`, `task_result_update_substrate_contract.md`, `substrate_baseline_contract.md` and its test matrix, `authoritative_export_contract.md:25`, `kernel.md:203`, `performance_contract.md:113`, `prometheus_metrics.md:34`, `performance_optimization_decisions.md` (PERF-D3 closed, PERF-D5 v2), `performance_clause_inventory.md`, `known_limitations.md:115`, and the regenerated `hash_callsite_inventory.{md,json}`.
