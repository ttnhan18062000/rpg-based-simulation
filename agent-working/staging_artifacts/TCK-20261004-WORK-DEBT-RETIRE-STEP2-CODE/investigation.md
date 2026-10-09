---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE
date: 2026-10-08
tags: [performance, engine, determinism]
---

# Investigation: TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE (design only)

Tree: `origin/main` `5e0994837` (after Phase A, #448, and the flags batch, #451); **re-checked 2026-10-09 against `origin/main` `3ffa6b95b` (after #457, #462, #454 and #468): `work_debt` still has 61 hits in `src/` with the same per-file split, the periodic, DRAIN_DEBT and opportunistic counts are unchanged, and the only moved line numbers are in `apply.py` (+5) and `scheduler.py` (-29); both are updated below.** Line numbers are from the newer tree.
Method: `search_docs`, `graphify query "work_debt"`, then `grep -rn` over `src/`, `tests/`, `tools/`, `docs/`, `data/`, `config/`.

## 0. What has already gone

- The **salience debt half** went with #387: `debt_ratio` and `global_salience` appear nowhere in `src/` (`grep -rn debt_ratio\|global_salience src` is empty).
- Phase A (#448) added `PressureSignals.tick_cost` / `tick_budget` / `phase_cost` and `src/engine/signal_source.py`; it did **not** touch `work_debt_total`, which `signal_source.py` still builds at four sites (below).
- Nothing produces debt. `work_debt` is read and written only by the paths below; every producer is either test-seeded (`PressureInjector.inject_work_debt`, tests that pass `work_debt={...}`) or absent.

## 1. `work_debt` (61 hits in `src/`, grouped by role)

| Role | Site | What it does |
|---|---|---|
| State field | `src/core/state.py:1426` `work_debt: Dict[str, int]`; `:1614` in the freeze copy (`shallow_freeze(self.work_debt)`) | the only stored copy |
| Proof-digest input | `src/engine/checkpoint.py:117` `data["work_debt"] = dict(sorted(...))` | **in every state hash** (the key is present even when `{}`) |
| Update field | `src/core/updates.py:1049` `work_debt_updates`; `:1091` in `is_empty`; `:1138` copy and `:1204-1205` additive merge in `merge`; `:1268` rebuild | typed record |
| Apply clamp | `src/engine/apply.py:322-324` (`max(0, old + delta)`), `:501` written into the new state | the only writer of `state.work_debt` |
| Kernel merge | `src/engine/kernel.py:611` init, `:623-624` (`res.work_debt_update is not None and res.subsystem_id` -> last-writer-wins by subsystem, `continue`), `:642` into `StateUpdate` | produces `work_debt_updates` from ID-zero system results |
| Signal | `src/core/governance.py:32` `PressureSignals.work_debt_total`; `src/engine/signal_source.py:64, 88, 114, 169` (`sum(state.work_debt.values())`, four sources); `src/engine/runtime_status.py:64` (copied in `record_signals`); `src/engine/observability.py:25, 120, 128` (snapshot dataclass and `sum(kernel.state.work_debt.values())`) | the always-0 input |
| Governor | `src/engine/governor.py:78` (`>= max_work_debt` -> SURVIVAL), `:86` (`>= 0.5 * max_work_debt` -> DEGRADED), `:145` (`recovery_limit_debt`), `:154` (recovery check) | can only ever see 0 |
| Phase governor | `src/engine/phase_governor.py:138-139` (`max_debt`, `work_debt_total > max_debt * 0.7` in the compaction rule) | same |
| Profiles | `src/config/profiles.py:37` `max_work_debt` (default 1000), `:119, 138, 157, 176` (four production profiles); `src/perf/profiles.py:47` | the threshold |
| Scheduler | `src/engine/scheduler.py:93-105` the DEFERRED branch (`:94`, `DRAIN_DEBT` at `:100`) (`WorkItem(work_kind="DRAIN_DEBT")` per positive `work_debt` entry) | creates DRAIN_DEBT items |
| Executor | `src/engine/executor.py:202-221` (sequential) and `:347-365` (concurrent adapter): `DRAIN_DEBT` -> `SimulationDomainLogic.drain_debt` (`src/engine/domain_logic.py:58`) -> `WorkerResult(entity_id=0, work_debt_update=..., subsystem_id=...)` | the only producer of ID-zero system results |
| Worker protocol | `src/core/worker_protocol.py:107-108` `work_debt_update`, `subsystem_id` | carry the drain |
| Validator | `src/core/protocol_validator.py:47, 52, 83-85, 88-99` `_check_one_debt_update_per_subsystem` (PERF-M1-T04, the rule from #319) and "System result missing subsystem_id" | guards the merge above |
| Certification | `src/certification/scenarios.py:33-38` `PressureInjector.inject_work_debt`; `:565` `WORK_DEBT_BUILDUP` in the pressure-scenario expectations tuple; `src/certification/models.py:69, 84` (`work_debt` field and dict key); `src/certification/harness.py:153` | scenario and result model |
| Long-run harness | `src/perf/long_run_harness.py:44-45` (`systems_with_debt`, `work_debt`), `:210-211, 223-224` | PERF-D3 accounting |
| API / snapshot / Prometheus | `src/api/engine_manager.py:205`; `src/observability/live/snapshot_provider.py:136`; `src/observability/prometheus_collector.py:63-66` (`sim_work_debt_total`) | reporting surfaces |
| Comment only | `src/engine/worker_manager.py:258` (names `work_debt_total` in a comment) | |

Root-cause rule: `src/observability/understanding/rootcause/rules.py:253-285` `GovernorPressureFromObservabilityOrWorkDebt` reads **no** debt value; only its title text and docstring say "Work Debt" (`rule_id` at `:263`, registered at `:357`, tested in `tests/unit/observability/test_root_cause_engine.py:21, 175, 186`). Change the title and docstring text only; keep the `rule_id` (stored analyses key on it).

## 2. `periodic_due_ticks`, `periodic_updates`, `PeriodicDefinition`, the periodic branch

| Site | Role |
|---|---|
| `src/core/state.py:1425` field; `:1613` freeze copy | state |
| `src/engine/checkpoint.py:116` | **in every state hash** |
| `src/core/updates.py:1048` `periodic_updates`; `:1091, 1137, 1202-1203, 1267` | no producer anywhere in `src/` |
| `src/engine/apply.py:319-320, 500` | copies `periodic_due_ticks` and applies `periodic_updates` |
| `src/engine/scheduler.py:19-27` `PeriodicDefinition`; `:35-36` constructor; `:70-90` the periodic branch (reads `state.periodic_due_ticks`, `:77`) | **no `src/` path ever registers a definition** (`DeterministicScheduler()` is built with none; only tests pass them) |
| `src/engine/policy.py:16` `allow_non_authoritative_periodic` (rows `:83, 104, 125, 146`) | read only by the periodic branch (`scheduler.py:73`) |
| **`src/domains/cooperation/phase.py:78-80`** | **a reader the ticket did not list:** `if hasattr(state, "periodic_due_ticks") and "social_cooperation_disabled" in state.periodic_due_ticks: flag = False`. Nothing in `src/` writes that key; only tests set it (`tests/unit/domains/cooperation/test_cooperation_phase.py:90`, `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py:125`). The phase already has the real OFF switch, the feature flag `ENABLE_SOCIAL_COOPERATION` (`src/engine/pipeline.py:218`). The `hasattr` guard means **the phase keeps working when the field is gone**, so `phase.py` needs no edit; its guard becomes dead code (follow-up for rpg-planner). Only the two OFF-path tests must change |
| `src/core/work.py:14-16, 34` `WorkClass.PERIODIC/OPPORTUNISTIC/DEFERRED`, `WorkItem.due_tick`; `src/core/concurrency_law.py:14-16` | class priorities used by the result sort key and by tests (`test_tied_worker_result_order`, `test_protocol_validator_system_results`). Recommendation: **keep the enum members and the priority table** (smaller blast radius); they become unreachable constants, listed as a follow-up |

## 3. The opportunistic branch and the unread policy fields

- `src/engine/scheduler.py:108` `if policy.allow_opportunistic:` (empty body); `src/engine/policy.py:15` (rows `:82, 103, 124, 145`).
- `diagnostic_verbosity` (`policy.py:18`, rows `:84, 105, 126, 147`) and `metrics_detail` (`:19`, rows `:85, 106, 127, 148`): read nowhere in `src/` outside `policy.py`.

## 4. The two misleading comments

`src/core/governance.py:45` (`dropped_work_delta ... # Work shed in the current tick`) and `src/engine/observability.py:32` (`dropped_work_count ... # Autoritative work shed by governor`, also misspelled). Both counters count only what the scheduler drops (`DeterministicScheduler.select_work`'s `dropped_count`, non-authoritative periodic definitions), which is always 0 once no definition is registered. After this change the counter has no producer; decision for the plan: keep `dropped_work_delta` / `dropped_work_count` (telemetry fields API consumers read) as a constant-0 report, with accurate comments, and say so in the divergence entry.

## 5. Surfaces outside `src/`

`docs/observability/prometheus_metrics.md:34` (`sim_work_debt_total`); `docs/engine/matrices/*` (scheduler work model and test matrices, degradation matrix lines 34 and 39, extended certification matrix `DEGRADED_NORMAL_RECOVERY` "30 debt -> Drain"); `docs/engine/deterministic_execution.md` T04 analysis (around lines 144-145); `docs/engine/contracts/` (resource governor, signal truth, task-result update substrate, substrate baseline); `docs/engine/authoritative_export_contract.md:25` (a JSON sample with `work_debt_updates`); `docs/engine/kernel.md:203`; `docs/engine/performance_contract.md:113`; `docs/architecture/performance_optimization_decisions.md` (PERF-D3, PERF-D5); `docs/performance/performance_clause_inventory.md`; `docs/performance/hash_callsite_inventory.{md,json}` and `tools/perf/hash_callsite_inventory.py:52` (name the scheme string). Parity ledger entries that cite it: `INFRA-223`, `INFRA-420`, `WORLD-117`. No Grafana, Prometheus alert, dashboard or frontend file references `work_debt` (grep over the repo outside `src/`, `tests/`, `docs/`, `agent-working/` finds only `codebase/baselines/mypy_baseline.txt`).

## 6. Facts the design depends on

- Every state hash changes. `CanonicalStateHasher.to_canonical_data` writes `data["periodic_due_ticks"]` and `data["work_debt"]` unconditionally (`checkpoint.py:116-117`), so even an empty dict is part of the canonical JSON; removing the keys changes the bytes of every digest. The scheme string is one constant, `PROOF_DIGEST_SCHEME` (`checkpoint.py:15`), emitted in `TICK_END` payloads (`kernel.py`) and `ProofDigest`.
- No code in `src/` reads a stored replay or a stored digest back: there is no replay reader and no `StateUpdate` deserializer, so "old digests are never compared with new" costs no loader.
- `RuntimeProfile` ignores unknown keyword arguments (pydantic default), so test code that still passes `max_work_debt=...` keeps constructing; those arguments become silently ignored and are cleaned up for honesty, not for correctness. A YAML profile that sets `max_work_debt` is likewise ignored.
- `pipeline.py` has **no** reference to `work_debt`, `periodic_*` or `DRAIN_DEBT`: the pipeline file does not change.
