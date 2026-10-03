---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance, architecture, determinism]
---

# State-Hash and Fingerprint Call-Site Inventory

Evidence for PERF-D5 (hash policy), call-site half of PA-03A, from
`TCK-20261003-PERF-HASH-CALLSITE-INVENTORY`. It was written on 2026-10-03 against the tree at the
commit named in the generated block. It measures nothing (no kernel run, no timing), proposes no
policy, and edits none of the documents it compares; those findings are in §6. The cost half of
PA-03A waits for the RPG-core stability entry gate in `performance_optimization_roadmap.md`.

How to read it: §1 is the answer in short. §2 is the scanner's generated tables. §3 to §5 are
hand-written from reading the code. §6 lists where three documents disagree with the code. §7 lists
what the scan and the reading could not establish.

## 1. Summary

- **Three scheduling mechanisms exist and almost nothing runs through them.**
  `CanonicalStateHasher.get_hash` is the flat SHA-256 hash. `BudgetedCanonicalHasher` (a rate-limited
  wrapper) has no production caller. `CanonicalHashScheduler` (a boundary check plus a LIGHT MD5 mode)
  is called from exactly two places, both in `src/certification/harness.py`, and always in `FULL`
  mode with `reason="certification"`, so its `HashScheduleViolation` cannot be raised by any
  production path and `HashMode.LIGHT` is never requested.
- **No hash-schedule mechanism governs the live persistence path.** The kernel hashes directly:
  once per tick when replay is allowed and (audit mode or `replay_richness == "FULL"`), and once at
  shutdown unconditionally (§4).
- **A second digest family exists beside the flat hash**: the fingerprint, an MD5 over a hand-built
  string of selected state domains (`StateFingerprinter.get_fingerprint`, reached through
  `AuthoritativeState.fingerprint()`). The kernel computes it up to four times per tick in audit mode
  and once per tick otherwise when replay is allowed. It is governed by no scheduling mechanism.
- **One hand-rolled copy of the flat hash exists**: `CertificationHarness._write_full_evidence`
  re-implements SHA-256 over compact canonical JSON instead of calling `get_hash`.
- **Two schemes are compared with themselves, never with each other** (§5).
- **Three documents contradict the code in seven places** (§6).

## 2. Generated tables

<!-- BEGIN GENERATED: tools/perf/hash_callsite_inventory.py -->

Generated from commit `58d6836c9b74713354b7526cd9b15b8bd9771f78` by `tools/perf/hash_callsite_inventory.py`. Regenerate this block with:

```
python3 tools/perf/hash_callsite_inventory.py --update-doc docs/performance/hash_callsite_inventory.md
python3 tools/perf/hash_callsite_inventory.py --format json > docs/performance/hash_callsite_inventory.json
python3 tools/perf/hash_callsite_inventory.py --check docs/performance/hash_callsite_inventory.json
```

### G1. Call sites in `src/` (static scan; guards are the conditions inside the enclosing function, as written)

| # | File | Line | Enclosing function | Mechanism | Kind | Guards in the function |
|---|---|---|---|---|---|---|
| 1 | `src/certification/harness.py` | 186 | `CertificationHarness.run_scenario` | CanonicalHashScheduler.compute_hash | caller | try; if expectations.reproducibility_required |
| 2 | `src/certification/harness.py` | 257 | `CertificationHarness._write_full_evidence` | hashlib digest of canonical state data | caller | try |
| 3 | `src/certification/harness.py` | 311 | `CertificationHarness._get_baseline_hash` | CanonicalHashScheduler.compute_hash | caller | try |
| 4 | `src/core/state.py` | 1641 | `AuthoritativeState.fingerprint` | StateFingerprinter.get_fingerprint | delegation inside a mechanism | none in this function |
| 5 | `src/engine/checkpoint.py` | 188 | `BudgetedCanonicalHasher.get_hash` | CanonicalStateHasher.get_hash | delegation inside a mechanism | unless: self._last_known_hash; if max_h is not None and self._call_count >= max_h |
| 6 | `src/engine/checkpoint.py` | 191 | `BudgetedCanonicalHasher.get_hash` | CanonicalStateHasher.get_hash | delegation inside a mechanism | none in this function |
| 7 | `src/engine/checkpoint.py` | 280 | `CanonicalHashScheduler.compute_hash` | CanonicalStateHasher.get_hash | delegation inside a mechanism | if mode is HashMode.FULL |
| 8 | `src/engine/kernel.py` | 397 | `Kernel._tick_once_inner` | AuthoritativeState.fingerprint | caller | if self._audit_mode |
| 9 | `src/engine/kernel.py` | 710 | `Kernel._phase_resolution` | AuthoritativeState.fingerprint | caller | if self._current_policy.replay_allowed |
| 10 | `src/engine/kernel.py` | 1151 | `Kernel._guard_stability` | AuthoritativeState.fingerprint | caller | none in this function |
| 11 | `src/engine/kernel.py` | 1186 | `Kernel._phase_persistence` | CanonicalStateHasher.get_hash | caller | if self._current_policy.replay_allowed and (self._audit_mode or self._current_policy.replay_richness == 'FULL') |
| 12 | `src/engine/kernel.py` | 1255 | `Kernel.shutdown` | CanonicalStateHasher.get_hash | caller | none in this function |
| 13 | `src/worldbuilding/compiler.py` | 792 | `WorldCompiler.compile` | StateFingerprinter.get_fingerprint | caller | none in this function |
| 14 | `src/worldbuilding/compiler.py` | 803 | `WorldCompiler.compile` | CanonicalStateHasher.get_hash | caller | none in this function |

### G2. Functions that produce a digest or delegate to a mechanism

| File | Line | Function | hashlib algorithms | Delegates to |
|---|---|---|---|---|
| `src/core/state.py` | 1635 | `AuthoritativeState.fingerprint` | - | StateFingerprinter.get_fingerprint |
| `src/engine/checkpoint.py` | 45 | `CanonicalStateHasher.get_hash` | sha256 | - |
| `src/engine/checkpoint.py` | 165 | `BudgetedCanonicalHasher.get_hash` | - | CanonicalStateHasher.get_hash |
| `src/engine/checkpoint.py` | 259 | `CanonicalHashScheduler.compute_hash` | md5 | CanonicalStateHasher.get_hash |
| `src/replay/fingerprint.py` | 33 | `StateFingerprinter.get_fingerprint` | md5 | - |

### G3. Schemes

| Mechanism | What it produces |
|---|---|
| CanonicalStateHasher.get_hash | flat SHA-256 over compact canonical JSON of the whole state |
| BudgetedCanonicalHasher.get_hash | same flat SHA-256, rate limited; returns a stale value when over budget |
| CanonicalHashScheduler.compute_hash | FULL: same flat SHA-256 at a sanctioned boundary; LIGHT: MD5 of tick/seed/entity and region counts |
| StateFingerprinter.get_fingerprint | dict whose 'state_hash' is an MD5 over a hand-built string of selected state domains |
| AuthoritativeState.fingerprint | delegates to StateFingerprinter.get_fingerprint (same dict, MD5 state_hash) |
| hashlib digest of canonical state data | hashlib digest computed by the caller itself, not through CanonicalStateHasher.get_hash |

### G4. Calls whose receiver the scanner could not resolve by name

None.

### G5. References from `tests/` (consumers; lines listed per file and mechanism)

| File | Mechanism | Lines |
|---|---|---|
| `tests/certification/test_event_observability_parity.py` | CanonicalStateHasher.get_hash | 55 |
| `tests/certification/test_evidence_levels.py` | CanonicalStateHasher.get_hash | 397 |
| `tests/helpers/replay_diff.py` | CanonicalStateHasher.get_hash | 85 |
| `tests/helpers/scenario.py` | CanonicalStateHasher.get_hash | 81 |
| `tests/integration/campaigns/test_phase9_campaign_runner.py` | AuthoritativeState.fingerprint | 81, 81 |
| `tests/integration/kernel/test_checkpoint_reproducibility.py` | CanonicalStateHasher.get_hash | 20, 21, 42, 53, 53, 94, 94, 100, 107, 123, 130, 141 |
| `tests/integration/kernel/test_checkpoint_reproducibility.py` | hashlib digest of canonical state data | 41 |
| `tests/integration/kernel/test_determinism_suite.py` | CanonicalStateHasher.get_hash | 46, 60, 61, 82, 83, 120, 129 |
| `tests/integration/kernel/test_executor_determinism.py` | AuthoritativeState.fingerprint | 60, 71, 89, 99 |
| `tests/integration/kernel/test_kernel_boundaries.py` | CanonicalStateHasher.get_hash | 85, 92 |
| `tests/integration/kernel/test_long_run_determinism.py` | CanonicalStateHasher.get_hash | 51, 61 |
| `tests/integration/kernel/test_p1_replay_fidelity.py` | StateFingerprinter.get_fingerprint | 503, 504 |
| `tests/integration/kernel/test_replay_fidelity.py` | AuthoritativeState.fingerprint | 16, 24, 37, 45, 101, 101, 108, 116 |
| `tests/integration/kernel/test_replay_fidelity.py` | CanonicalStateHasher.get_hash | 133, 134, 140 |
| `tests/integration/kernel/test_seed_stability.py` | AuthoritativeState.fingerprint | 67, 78, 96, 104 |
| `tests/integration/kernel/test_snapshot_integrity.py` | CanonicalStateHasher.get_hash | 19, 20 |
| `tests/integration/observability/test_cognition_snapshot_artifact.py` | CanonicalStateHasher.get_hash | 172, 178 |
| `tests/integration/pipeline/test_governance_isolation.py` | CanonicalStateHasher.get_hash | 13, 23 |
| `tests/integration/pipeline/test_no_hidden_mutation.py` | CanonicalStateHasher.get_hash | 81, 82 |
| `tests/integration/scenarios/test_scenario_runtime_service.py` | CanonicalStateHasher.get_hash | 354, 369 |
| `tests/integration/world/test_long_run_stability.py` | CanonicalStateHasher.get_hash | 90 |
| `tests/integrity/test_logic_guards.py` | AuthoritativeState.fingerprint | 137, 138, 139, 247 |
| `tests/perf/test_apply_compaction_perf.py` | AuthoritativeState.fingerprint | 76, 76 |
| `tests/perf/test_concurrency_parity.py` | StateFingerprinter.get_fingerprint | 32, 49 |
| `tests/perf/test_dirty_parity.py` | StateFingerprinter.get_fingerprint | 77, 84 |
| `tests/unit/core/test_engine_integrity.py` | AuthoritativeState.fingerprint | 159 |
| `tests/unit/core/test_engine_integrity.py` | CanonicalStateHasher.get_hash | 86, 87 |
| `tests/unit/core/test_entity_integrity.py` | CanonicalStateHasher.get_hash | 93, 93, 153, 154, 189, 189, 337, 337, 387, 387, 460, 460 |
| `tests/unit/core/test_entity_integrity.py` | StateFingerprinter.get_fingerprint | 359, 360 |
| `tests/unit/core/test_operational_flags.py` | CanonicalStateHasher.get_hash | 78, 81 |
| `tests/unit/core/test_place_state.py` | CanonicalStateHasher.get_hash | 91, 92, 146, 147 |
| `tests/unit/domains/optimization/test_semantic_entity_index.py` | CanonicalStateHasher.get_hash | 224, 228 |
| `tests/unit/domains/optimization/test_state_update_compactor.py` | AuthoritativeState.fingerprint | 89, 89 |
| `tests/unit/domains/progression/test_progression_decision_canonical_hash.py` | CanonicalStateHasher.get_hash | 64 |
| `tests/unit/economy/test_economy_health_monitor.py` | AuthoritativeState.fingerprint | 188, 190 |
| `tests/unit/engine/test_campaign_bridge_fields_state_hash_coverage.py` | CanonicalStateHasher.get_hash | 33, 34, 39, 40, 47, 48, 58, 59, 69, 70, 103, 103, 107, 108, 125, 126 |
| `tests/unit/engine/test_hash_scheduler.py` | CanonicalHashScheduler.compute_hash | 44, 54, 64, 74, 84, 94, 103, 113, 121, 132, 143, 144, 157 |
| `tests/unit/kernel/test_worker_equivalence.py` | CanonicalStateHasher.get_hash | 60, 61, 85, 85 |
| `tests/unit/progression/test_species_base_stats_preserved.py` | CanonicalStateHasher.get_hash | 261, 262 |
| `tests/unit/replay/test_fingerprint_identity_coverage.py` | StateFingerprinter.get_fingerprint | 39, 40, 53, 54 |
| `tests/unit/worldbuilding/test_place_wiring.py` | CanonicalStateHasher.get_hash | 118, 119, 322, 323 |
| `tests/unit/worldbuilding/test_world_compiler.py` | CanonicalStateHasher.get_hash | 166, 1151, 1152 |

<!-- END GENERATED -->

## 3. Per call site (hand-written)

Mechanism labels: **flat** = `CanonicalStateHasher.get_hash` (SHA-256, compact canonical JSON of the
whole state); **fingerprint** = the MD5 fingerprint dict. "State tick" is the tick of the state the
digest describes; "computed at" is when in the tick the call runs. Line numbers are at the audited
commit; the generated tables above are the source for them after later merges.

### 3.1 `src/engine/kernel.py`

**K1 `Kernel._tick_once_inner`, fingerprint (audit mode only).**
- Runs: once per tick, only when `self._audit_mode` (`kernel.py:396-397`); audit mode is requested by
  the certification harness (`flags={"audit_mode": True}`, `harness.py:89, 174, 300`) and by tests, not by
  a normal run. Independent of `RuntimeMode`.
- State tick: tick T, the state at the start of the tick. Computed at: after `_phase_init`, before
  scheduling.
- Consumer: held in the local `start_fingerprint`; compared in `_guard_stability` after Scheduling
  and after Collection (`kernel.py:410-411, 419-420`) by `state_hash` equality
  (`kernel.py:1152`); a difference raises `ProtocolViolationError`. Not stored or emitted.
- Scheme: fingerprint (MD5), compared only with another fingerprint.
- Stale: no. Recomputed every tick; the local is dropped at the end of the tick.

**K2 `Kernel._guard_stability`, fingerprint (audit mode only, by caller).**
- Runs: twice per audit-mode tick (Scheduling and Collection guards). The function has no guard of
  its own; its callers are guarded by `self._audit_mode and start_fingerprint`
  (`kernel.py:410, 419`). That caller guard is read by hand, not found by the scanner.
- State tick: tick T, `self._state` at the time of the call (before Resolution; the generation is
  replaced only in `_phase_advancement`). Computed at: just after Scheduling and just after
  Collection.
- Consumer: the equality check in the same function (`kernel.py:1152`); the value is used in the
  error message. Not stored.
- Scheme: fingerprint (MD5), compared with K1's value.
- Stale: no.

**K3 `Kernel._phase_resolution`, fingerprint (every tick when replay is allowed).**
- Runs: every tick where `self._current_policy.replay_allowed` (`kernel.py:700`), that is `NORMAL`,
  `CONSTRAINED` and `DEGRADED`; not `SURVIVAL` (`policy.py:150` sets `replay_allowed` false) and not
  when the kernel forced replay off (`kernel.py:223, 583`). Independent of audit mode.
- State tick: tick T, the pre-advancement state, emitted next to the refined update that has not yet
  been applied. Computed at: end of Resolution, before Cleanup and Advancement.
- Consumer: stored as `payload["fingerprint"]` of a `REFINED_UPDATE` `TraceEvent`
  (`kernel.py:700-712`), handed to `ReplayManager.emit` (`replay_manager.py:85`), which buffers it
  (`replay_manager.py:104`); `MINIMAL` richness still passes `KERNEL` events
  (`replay_manager.py:94-97`). Readers: none found in `src/` (§7); tests read it, for example
  `tests/integration/kernel/test_authoritative_outcome_truth.py:188`.
- Scheme: fingerprint (MD5).
- Stale: no.

**K4 `Kernel._phase_persistence`, flat hash (per tick, conditional).**
- Runs: when `replay_allowed` and (`self._audit_mode` or `replay_richness == "FULL"`)
  (`kernel.py:1184`). `NORMAL` and `CONSTRAINED` use richness `FULL` (`policy.py:88, 109`), so it
  runs every tick there; `DEGRADED` (`MINIMAL`, `policy.py:130`) skips it unless audit mode is on;
  `SURVIVAL` never emits. Otherwise the payload hash is the string `"SKIPPED"` (`kernel.py:1183`).
- State tick: T+1. `_phase_advancement` has already replaced the state with the next generation
  (`kernel.py:835-843`), and persistence runs after it (`kernel.py:452-453`). The event is stamped
  `tick=self._state.tick`, so the stamp and the state agree. Computed at: end of tick.
- Consumer: payload `"hash"` of a `TICK_END` event (`kernel.py:1188-1194`) into the replay buffer
  (`replay_manager.py:104`). No reader in `src/` (§7). Tests: `tests/unit/engine/test_hash_scheduler.py`
  (patches `get_hash` and asserts `TICK_END` content, around lines 43-260),
  `tests/unit/kernel/test_verification_level.py` (reads the `TICK_END` trail).
- Scheme: flat. A `"SKIPPED"` sentinel sits in the same field, so a consumer sees two kinds of value.
- Stale: no cache of the hash. The per-component canonical dicts it serialises are cached (§4.3).

**K5 `Kernel.shutdown`, flat hash (always).**
- Runs: once per kernel, at shutdown, with no guard (`kernel.py:1254-1255`). Not gated on mode,
  richness or audit.
- State tick: the final tick; computed at: shutdown, after workers and observability are stopped.
- Consumers: `logger.info` (`kernel.py:1256`); `ShutdownResult.final_hash` (`kernel.py:1314`,
  field `core/lifecycle.py:21`) and the run manifest `state_hash` (`kernel.py:1307`). Downstream of
  `final_hash`: `certification/harness.py:166` (feeds `ConformanceEvaluator.evaluate`,
  `conformance.py:71-79`, and `recorder.py:173-174`), `perf/long_run_harness.py:234, 324, 331`
  (determinism check compares two runs), `cli/entry.py:266` (printed), `observability/reporting/
  run_report.py:103-110, 435` (report). Downstream of the manifest `state_hash`:
  `observability/reporting/artifact_repository.py:35`, `observability/warehouse/adapters.py:166, 388`,
  `warehouse/clickhouse.py:373, 404`, `observability/mining/auditor.py:182`.
- Scheme: flat.
- Stale: no.

### 3.2 `src/certification/harness.py`

**H1 `CertificationHarness.run_scenario`, `CanonicalHashScheduler.compute_hash`.**
- Runs: only when `expectations.reproducibility_required` (`harness.py:170-186`), inside `try`.
  `mode=FULL`, `reason="certification"`, so `allow_full_hash_at` is always true.
- State tick: `kernel2.state.tick`, the tick the second run reached; computed at: right after its
  last `tick_once()`, before its `shutdown`. Passing `tick=kernel2.state.tick` makes the scheduler's
  tick argument the state's own tick.
- Consumer: `secondary_hash` into `ConformanceEvaluator.evaluate` (`harness.py:195-197`), compared
  with `final_hash` (`conformance.py:77-79`).
- Scheme: flat, compared with K5's flat value, so same scheme on both sides.
- Stale: no.

**H2 `CertificationHarness._get_baseline_hash`, `CanonicalHashScheduler.compute_hash`.**
- Runs: when called to produce the baseline (a forced-sequential run, `harness.py:296-312`), inside
  `try`; same `FULL` / `"certification"` arguments.
- State tick: the baseline kernel's final tick; computed at: after its last tick, before `shutdown`.
- Consumer: `baseline_hash` into the conformance check (`conformance.py:71-73`) and the recorded
  status `MATCHED` / `DRIFT_DETECTED` (`recorder.py:174`).
- Scheme: flat, compared with K5's flat value.
- Stale: no.

**H3 `CertificationHarness._write_full_evidence`, hand-rolled digest.**
- Runs: only at `EvidenceLevel.FULL` (`harness.py:272-275`), inside `try`; a failure is logged and
  returns `None`.
- State tick: `result.final_state`, the final state; computed at: result persistence, after the run.
- Consumer: returned as `artifact_hash` to `self._recorder.record(...)` (`harness.py:273-278`) and
  stored as `final_state_hash` in the certification artifact (`certification/models.py:212-275`,
  `recorder.py:39-69`).
- Scheme: flat by construction: SHA-256 over the same compact JSON that `get_hash` hashes (the code
  comment says "matching get_hash()", `harness.py:254`). It is a second implementation, not a call.
  Nothing in `src/` keeps the two in step.
- Stale: no.

### 3.3 `src/worldbuilding/compiler.py`

**W1 `WorldCompiler.compile`, fingerprint** and **W2 `WorldCompiler.compile`, flat hash.**
- Runs: once per world compile, unguarded (`compiler.py:792, 803`).
- State tick: the freshly compiled state (tick 0); computed at: end of compilation.
- Consumers: both go into the compile report as `state_hash` (fingerprint) and `canonical_state_hash`
  (flat) (`compiler.py:823-824`). `state_hash` is printed by `cli/entry.py:229` and
  `worldbuilding/cli.py:285`. The report is written to JSON when `output_report_path` is set
  (`compiler.py:828-829`). Tests: `tests/unit/worldbuilding/test_world_compiler.py`,
  `tests/certification/test_world_compile_determinism.py`.
- Scheme: both. The report carries both side by side under different keys; the comment at
  `compiler.py:795-803` says the fingerprint does not cover Place data, which is why the flat hash is
  there too.
- Stale: no.

### 3.4 Delegations inside the mechanisms (not callers)

`AuthoritativeState.fingerprint` (`state.py:1635-1641`) delegates to `StateFingerprinter.get_fingerprint`.
`BudgetedCanonicalHasher.get_hash` (`checkpoint.py:165-191`) and
`CanonicalHashScheduler.compute_hash` (`checkpoint.py:259-280`) delegate to
`CanonicalStateHasher.get_hash`. None of the three has a production caller other than those listed
above (the budgeted wrapper has none).

## 4. Which mechanism governs which call site

### 4.1 Governed

| Mechanism | Governs | Evidence |
|---|---|---|
| `CanonicalHashScheduler.compute_hash` | H1, H2 only | the only two references outside `checkpoint.py` (generated table G1) |
| `BudgetedCanonicalHasher.get_hash` | nothing in production | no call outside `checkpoint.py`; only `tests/unit/engine/test_resource_budget_gate.py` constructs it |
| `CanonicalStateHasher.get_hash` | is the hash itself; called directly by K4, K5, W2 | G1 |

### 4.2 Ungoverned by any hash-schedule mechanism

K4 (per-tick flat hash), K5 (shutdown flat hash), W2 (compile flat hash), H3 (hand-rolled SHA-256),
and all fingerprint sites K1, K2, K3, W1. K4's only control is the inline condition at
`kernel.py:1184`, which tests richness and audit mode, not a budget or a boundary. The
`CanonicalHashScheduler` boundary rule (tick 0, run end, or a sanctioned reason) is not applied to
K4 or K5.

### 4.3 Caching that sits under the flat hash

22 dataclasses in `src/core/state.py`, `EntityState` among them, cache their `to_canonical_dict()`
result in a `_canonical_cache` field set once (`state.py:70-83` is the pattern;
`EntityState.to_canonical_dict` at `state.py:930-934`). The classes are `frozen=True`, so the cache
is valid while a component is never mutated in place. The cache is never cleared; the returned dict
is shared, so a caller that mutated it would corrupt later hashes. This is the one place a stale
value can reach the flat hash. It does not exist for the fingerprint, which rebuilds its string each
call.

## 5. Schemes and cross-scheme comparison

| Value | Scheme | Compared with |
|---|---|---|
| K1 vs K2 | fingerprint `state_hash` (MD5) | each other (`kernel.py:1152`) |
| H1 vs K5, H2 vs K5 | flat SHA-256 | each other (`conformance.py:71-79`) |
| K4 | flat SHA-256 or `"SKIPPED"` | nothing in `src/` |
| K5 `final_hash` across two runs | flat SHA-256 | each other (`perf/long_run_harness.py:333`) |
| W1, W2 | MD5 fingerprint and flat SHA-256 | reported side by side, never compared |

No path in `src/` compares a flat hash with a fingerprint, or a `LIGHT` value with anything: `LIGHT`
is never requested. The one place where two flat values come from two code paths is H3 against
`get_hash`; nothing compares them.

## 6. Where the documents disagree with the code

Documents are not edited. "Code" cites the evidence.

| # | Document and line | Statement | Code and line | Difference |
|---|---|---|---|---|
| 1 | `docs/engine/deterministic_execution.md:34` | `get_hash()` "produces a SHA-256 of the world state after each tick" | `kernel.py:1184-1186`, `policy.py:130, 150` | Computed per tick only when replay is allowed and (audit mode or FULL richness); `DEGRADED` writes `"SKIPPED"`, `SURVIVAL` emits nothing |
| 2 | `docs/engine/deterministic_execution.md:37` | "All floating-point values rounded to a fixed precision" | `checkpoint.py:64` (`to_canonical_data`), `state.py:72-83` | No rounding found in `to_canonical_data` or the component `to_canonical_dict` methods read; values go to `json.dumps` as stored (`grep round(` over `src/core` and `checkpoint.py` finds none in canonical code) |
| 3 | `docs/engine/deterministic_execution.md:41` | the hash "is emitted in the `TICK_END` event in the warehouse (field: `tick_hash`)" | `kernel.py:1188-1194` | The payload key is `"hash"` in a replay `TraceEvent`; `tick_hash` is a local variable, not a field, and no warehouse field of that name exists in `src/` |
| 4 | `docs/engine/deterministic_execution.md:41` | "Replay divergence is detected by comparing `tick_hash` sequences" | grep `TICK_END` in `src/`: only `kernel.py:1192` | No code in `src/` reads the `TICK_END` hash; the claimed comparison has no implementation here |
| 5 | `docs/engine/known_limitations.md:93` | `_guard_stability()` "fingerprints the full `AuthoritativeState` (SHA-256 over all fields)" | `kernel.py:1151`, `state.py:1641`, `fingerprint.py:119` | It is the MD5 fingerprint over selected domains. The same file says MD5 at `known_limitations.md:149`, so the file disagrees with itself |
| 6 | `docs/engine/known_limitations.md:115-121` | table: `DEGRADED` gives `"SKIPPED"` | `kernel.py:1184` | Audit mode forces the hash in `DEGRADED` too; the table omits the audit-mode condition |
| 7 | `docs/plans/design_enhancement/performance_milestones_epic.md:61-62` | full hash calls are "rate already limited by `BudgetedCanonicalHasher`" | `checkpoint.py:141`; `kernel.py:1186, 1255` | The wrapper has no production caller; the kernel calls `CanonicalStateHasher.get_hash` directly |

Statements checked and consistent with the code: `known_limitations.md:125` (hash runs every tick in
`NORMAL` and `CONSTRAINED`), `:129` (the sentinel), `:135` (final hash always computed),
`:140` (`REFINED_UPDATE` carries a fingerprint in every mode that allows replay), `:149-151`
(MD5; the fingerprint is the per-tick signal in `DEGRADED`).

## 7. Limits of this inventory

- The scanner resolves receivers by name (imports, aliases, `x = Class()` assignments). It lists calls
  it cannot resolve in G4 (none at the audited commit). A hash reached through a callable passed as
  an argument, `getattr`, or a string-built name would not be found.
- Guards are the conditions inside the enclosing function. A guard in a caller (K2) was read by hand.
- Consumers outside `src/` and `tests/` (documents, tools, the dashboards) were not scanned beyond the
  `tests/` table G5; `tools/balance_measure.py` references the mechanisms and was not traced.
- Replay consumers: nothing in `src/` reads `REFINED_UPDATE` or `TICK_END` payloads. They are written
  to the replay buffer (`replay_manager.py:104`) and the chunks that buffer produces; what reads
  those files was **not traced**. Last known hand-off point: `ReplayManager._buffer.record`.
- Cost of any call site is deliberately absent. `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`
  records one observed fingerprint cost; it is a one-off observation, not a baseline, and is referenced
  here only.
- Whether the 22 component caches are ever invalidated by in-place mutation was not tested.
