---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-10-03
---

# Deterministic Execution Contract

**Source:** `src/engine/kernel.py`, `src/engine/checkpoint.py` (CanonicalStateHasher), `src/platform/rng.py` (DeterministicRNG), `src/engine/pipeline.py`
**Related docs:** [kernel.md](kernel.md) (6-phase loop), [candidate_selection.md](candidate_selection.md) (ordering guarantees), [dirty_state_and_dependency.md](../core/dirty_state_and_dependency.md) (audit_dirty_set)

---

## Purpose

The determinism guarantee is: **same world seed + same initial `AuthoritativeState` → same `CanonicalStateHasher.get_hash()` after every tick.**

This guarantee is the foundation for replay fidelity, regression testing, and parity verification. Any code that violates it is a critical bug.

---

## Scope of the guarantee

Approved decision: PERF-D2 (`docs/architecture/performance_optimization_decisions.md`). The guarantee is stated in tiers, and only what a passing test matrix proves is claimed.

| Tier | Scope | Claim |
|---|---|---|
| DET-PORT-0 | Same build, same interpreter minor version, same OS and CPU architecture, sequential executor, Canonical contract | Guaranteed. This is the certification reference. |
| DET-PORT-1 | The DET-PORT-0 environment with a different executor backend (thread, process) or worker count, and any `PYTHONHASHSEED` | Guaranteed only for backends and worker counts in a passing parity matrix; otherwise unclaimed. |
| DET-PORT-2 | A different OS, CPU architecture, interpreter minor version, or native-extension build | Not guaranteed. A combination is promoted to a claim only after it passes the same matrix. |

The reference runtime is the one CI runs: CPython 3.13 on Linux x86-64. Every benchmark result, baseline, and hash proof records its tier and its runtime identity (interpreter version and build flavor, OS, architecture, and the versions of any native kernels). A proof is comparable only within its tier.

**Current state.** The tiers are the approved contract. Recording a tier on results is pending (`PERF-M2-T02` defines the benchmark identity schema), and which executor backends and worker counts pass parity today has not been measured. The only claim that stands on evidence is the one this document made before: sequential execution on one machine, subject to the wall-clock inputs listed under "What runs today". Concurrent execution mode is outside DET-PORT-0. `docs/engine/known_limitations.md` records that bit-identical parity is ratified for sequential mode only. DET-PORT-1 replaces that statement only for the backend and worker-count combinations that pass the matrix (the matrix is not yet run; implementation is pending, tracked under `PERF-M1`).

---

## The two contracts: Canonical and Live bounded

Approved decision: PERF-D1, with amendment A1. Two contracts exist for two uses; a run states which one it ran under.

- **Canonical contract.** No wall-clock or host-resource reading may influence authoritative state. Pressure signals are deterministic proxies (work-unit counts and queue depth against a fixed ceiling). The mid-tick cutoff and the end-of-tick drop are driven by a work-unit budget or are off. Guarantee: the same build, configuration, seed, and initial state give the same proof digest at every tick, whatever the host load. Required for certification, determinism and replay tests, Simulation Quality calibration, and any benchmark that claims hash parity.
- **Live bounded contract.** Real wall-clock and resource signals are allowed. Every decision that changes what is computed is either written to a versioned, bounded control trace or is derivable from one that is. Guarantee: a Live run is reproducible **given its trace**: a Canonical-mode replay that consumes the trace reaches the same hashes. The trace is not predictable in advance, and that is accepted.
- **Rule A1, part of both contracts.** A game-facing signal (any value that systems read from `AuthoritativeState` to change gameplay: prices, salience, and anything derived from them) is computed from deterministic inputs only. Host timing and resources may choose how much work the engine does (mode, budgets, cadence). They never change what the world's rules produce.

### Control-input classification

| Decision | Treatment |
|---|---|
| `RuntimeMode` transition (tick, from, to) | Recorded |
| Mid-tick cutoff: how many sorted results were applied before the drop | Recorded (the mode alone does not say which results were lost) |
| End-of-tick dropped-work marker | Recorded |
| Phase budgets emitted from measured sub-phase cost | Recorded as emitted values; the costs that produced them are not |
| Scan policy, cadence, LOD, sweep interval | Derived from the recorded mode and budgets; a test proves the derivation |
| Worker completion order | Not recorded; results are canonically sorted before resolution |
| Frame pacing, GC timing | Not recorded; no effect on authoritative state |

### What runs today

**Today's runs satisfy neither contract fully.** One wall-clock input still changes what is computed, in every execution mode unless `audit_mode` is on (inputs 2 and 3 below no longer do; they are report-only):

1. `ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py`) chooses `RuntimeMode` from `tick_compute_ms`, resident memory, and worker and queue utilization; the mode then sets cadence, LOD, scan policy, and phase budgets.
2. **Report-only since `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`.** `Kernel._phase_resolution()` (`src/engine/kernel.py`) still compares elapsed wall-clock time with `profile.max_tick_budget_ms` while processing results when `audit_mode` is off, but an overrun now only records `RuntimeStatus.budget_overrun_ms` / `total_budget_overruns` and raises the watchdog alert. It no longer drops results and no longer forces `DEGRADED`. Before this ticket it did both, so what a run computed depended on host speed (`frontier_living_world`, same seed: 8 vs 10 deaths at tick 500).
3. **Report-only since `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`.** The end-of-tick check in `Kernel._tick_once_inner` records the same overrun signal after tick 5 instead of the `9999` dropped-work sentinel; `dropped_work` now counts only work the scheduler shed. Nothing in the governor or in `AuthoritativeState` reads the overrun signal (PERF-D1 amendment A1).
4. **Closed by `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` (was: world-pressure salience).** The previous tick's measured `tick_compute_ms` used to become `compute_ratio` and `global_salience` in `Kernel._phase_resolution`, was applied to `AuthoritativeState.pressure_signals`, and multiplied shop buy prices, so a slower or busier host made items cost more (a violation of rule A1). The kernel no longer computes or writes any of it, and `DynamicPriceService.calculate_buy_price(base_value)` returns `max(1, int(base_value))` and reads no state (`docs/guidelines/intentional_divergences.md` §2.75). `tick_compute_ms` remains a governor control signal and a report value, never a gameplay input.

`audit_mode` zeroes the timing and resource signals, so it suppresses the first input, and it silences the overrun report in the second and third (`flags["audit_mode"]`, `src/engine/kernel.py`). It removes the one remaining wall-clock input that changes what is computed, but it is **not sufficient on its own for a deterministic run**: before `TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK`, identical `audit_mode` runs (raised budget, sequential executor, no dropped work, governor in `NORMAL`) diverged from tick 5 because `DirtySetBuilder.mark_from_update` skipped entity updates by `id()` and a recycled address silently dropped an entity from the dirty set (`TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`). That cause is removed, and no trial diverged in 144 short (8-tick) trials after the fix, where bare `main` diverged in 8 of 96; this is a measurement over short runs, not a proof of determinism, and a second `id()`-keyed cache (`get_frozen`, `src/engine/executor.py`) was probed without a stale hit but is not proven safe. `audit_mode` is still not the Canonical contract, which has no implementation yet (`PERF-M1`).

**The Canonical signal contract (opt-in, `TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY`).** A profile with `signal_contract=CANONICAL` replaces the first input's measured cost with a modelled one. `CanonicalSignalSource` (`src/engine/signal_source.py`) computes `tick_cost` in reference-milliseconds from `WORK_MODEL_V1` (`src/engine/work_units.py`: 0.68 per active entity plus 7.42 per lead, PROVISIONAL, counted from `AuthoritativeState` before the mode acts), so the mode cannot feed back into its own input. It reads no clock and no host module, and a static test keeps it that way. Memory and replay backlog are not inputs under Canonical; queue and worker pressure are demand proxies; `PhaseBudgetGovernor`'s two per-phase rules (locomotion, final_integrity) have no pre-policy counter and do not fire (DEV-018); the thresholds keep their millisecond meaning, as reference-host milliseconds. The same seed then gives the same mode, phase budgets and state hash on any host (`tests/integration/kernel/test_canonical_signal_contract.py`, INFRA-426). The default contract is `LIVE`, today's behaviour, unchanged and pinned by a golden fixture (INFRA-427); `audit_mode` still wins and zeroes the signals. Which contract a run used is recorded in its run manifest (`signal_contract`). Canonical models overload; it does not measure it, and the model is a rough estimator (its weights exclude the `combat_engagement` cost until that defect is fixed).

`verification_level = REDUCED` stays the label for a run that reached `DEGRADED` or `SURVIVAL` and has no verified control trace. It discloses the problem per run and does not make the run reproducible.

**Inputs the Canonical proxy set must replace.** In addition to the two above that still change outcomes, two inputs reach control decisions and are classified by the table above: the replay-buffer backlog, which is one of the governor's `DEGRADED` triggers and depends on a background flush thread (recorded as a mode transition); and `PhaseBudgetGovernor` (`src/engine/phase_governor.py`), which reads per-phase wall-clock costs and `tick_compute_ms` directly in every mode (the "phase budgets" row). The evidence for all of this is `docs/performance/wall_clock_inventory.md`; its §6 lists what the scan could not see.

`docs/engine/runtime_profiles.md` §4 (the same profile gives identical semantics on different hardware classes) holds under the Canonical contract only.

---

## The canonical hash

Approved decision: PERF-D5. Two digest families exist, with two roles.

- **Proof digest.** `CanonicalStateHasher.get_hash()` is a flat SHA-256 over compact canonical JSON of the whole state (the scheme named `flat-sha256-v2`; v2 is v1 without the two state keys `periodic_due_ticks` and `work_debt`, which were removed with work debt in `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`, and a v2 digest is never compared with a v1 digest). It is the only value that may back a determinism, replay, certification, or parity claim.
- **Stability check.** `AuthoritativeState.fingerprint()` (`StateFingerprinter.get_fingerprint`) is an MD5 over a hand-built string of selected state domains. It does not cover all state (Place data is outside it). It is a cheap in-tick diagnostic, and it is never cited as proof that two runs are equal.

The proof digest's input is a canonical sorted JSON representation:
- All dict keys sorted lexicographically
- All entity collections sorted by entity ID

This means the digest is independent of Python dict insertion order or object identity. Two `AuthoritativeState` objects that are semantically identical produce the same digest. Floating-point values are **not** rounded before hashing: an earlier version of this document said they were, and no rounding exists in `to_canonical_data` or the component `to_canonical_dict` methods. PERF-D5 removes the claim rather than implementing it, because rounding hides small divergences and can flip at rounding boundaries; portability is handled by the DET-PORT tiers above.

**When it is computed.** The kernel takes the per-tick digest in `Kernel._phase_persistence` through `CanonicalHashScheduler.compute_digest(..., reason="replay")`, only when replay is allowed and (`audit_mode` is on or `replay_richness == "FULL"`); otherwise the digest is a `ProofDigest` with status `NOT_COMPUTED_LIVE_POLICY` and no value. The policy gives full replay richness in `NORMAL` and `CONSTRAINED`, minimal richness in `DEGRADED` (not computed unless `audit_mode` forces it), and no replay in `SURVIVAL` (`src/engine/policy.py`), where nothing is computed or emitted per tick. When Live runs hash is unchanged by `TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER` (PERF-D5 point 4: it stays as is until Gate A). The final digest at shutdown goes through the same scheduler at the run-end boundary and is always computed. The certification harness takes its digests through the scheduler too, with `reason="certification"` (`docs/performance/hash_callsite_inventory.md`).

**Where it goes.** The per-tick digest is the payload of a `TICK_END` `TraceEvent` in the replay stream. There is no warehouse field named `tick_hash`, and nothing in `src/` reads the `TICK_END` hash.

**`TICK_END` payload shape (schema note, `TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER`).** Before: `{"hash": "<sha256 hex>"}`, or `{"hash": "SKIPPED"}` when not computed. Now: `{"hash": "<sha256 hex>" | null, "scheme": "flat-sha256-v2", "digest_status": "computed" | "not_computed_live_policy" | "not_computed_unsanctioned_boundary"}`. `hash` is `null` exactly when `digest_status` is not `computed`. Replays recorded before this change carry the string `"SKIPPED"` and no `scheme` or `digest_status`. A reader that compares or verifies hashes must treat the old `"SKIPPED"` and the new `null` as "not computed", must never count a missing or `null` hash as equal evidence, and must not compare digests whose `scheme` differs (a missing `scheme` means `flat-sha256-v1`, the only scheme that existed).

**Coverage gap (PERF-D5 finding, left open).** `AuthoritativeState.pressure_signals` is outside the proof digest (`CanonicalStateHasher`'s `to_canonical_data` has no such key). While the kernel wrote salience into it, a difference in salience was invisible to the flat hash until a purchase changed gold or inventory. The kernel no longer writes it (`TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`), so in production it stays the initial `{}`; the field is still outside the digest, and anything that writes it in future would be uncovered. Recorded here; no fix is decided.

**Built (`TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE`, the `src/engine/checkpoint.py` half of PERF-D5):** the scheme is named by `PROOF_DIGEST_SCHEME` (`flat-sha256-v1` when this was built, `flat-sha256-v2` since `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`); `ProofDigest` is a typed record of scheme, tick, `DigestStatus` and value; `CanonicalHashScheduler.compute_digest` returns it and reports `NOT_COMPUTED_UNSANCTIONED_BOUNDARY` instead of a stale or approximate value; and `BudgetedCanonicalHasher` and `HashMode.LIGHT` are retired. The flat hash values were unchanged by that ticket. The tracked `data/worlds/*/world_compile_report.json` files carry a `canonical_state_hash` computed under `flat-sha256-v1`; it is not compared with any v2 digest (the freshness test checks counts only), and the files are described as v1 until a world is recompiled. Cross-run, cross-executor and compaction parity tests now compare `CanonicalStateHasher.get_hash`; the fingerprint tests that remain are labelled as stability-check coverage tests.

**Built (`TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER`, PERF-M1-T03b):** the kernel's per-tick and shutdown digests go through `CanonicalHashScheduler.compute_digest` and carry a scheme and a typed status (`NOT_COMPUTED_LIVE_POLICY` has its first producer); the certification harness calls the scheduler instead of holding a hand-written copy; `HashMode` and the `mode` parameter are removed; `DEFAULT_HASHING_BUDGET`, the `"hashing"` budget entry and its `max_full_hashes_per_100_ticks` field are removed. Hash values are unchanged.

**Not built (PERF-D5):** when the digest is computed is not yet a declared field of the runtime profile.

---

## The four enforcement rules

### Rule 1: Stateless random numbers — `DeterministicRNG`

**Location:** `src/platform/rng.py`

```
DeterministicRNG.get_float(domain, tick, entity_id, sub_id) -> float
DeterministicRNG.get_int(domain, tick, entity_id, sub_id) -> int
```

Each call computes a composite seed: `base_seed ^ domain ^ tick ^ entity_id ^ sub_id`, then creates a **fresh** `random.Random(composite_seed)` and draws one value. This is **order-independent** — any domain can call `get_float()` in any order and always gets the same value for the same arguments.

**Forbidden:** `DeterministicRNG.next_float()` and `next_int()` — these are stateful sequential draws. They are deprecated and forbidden in concurrent contexts. Using them in a pipeline phase that may run out-of-order causes divergence.

Other forbidden operations in tick-path code:
- `random.random()` (global mutable state)
- `time.time()` or any wall-clock read
- `os.getpid()` or process/thread ID reads
- Reading external files or network during tick resolution

### Rule 2: Deterministic worker result ordering

**Location:** `Kernel._phase_resolution` in `src/engine/kernel.py`

After all workers complete, their results are sorted before resolution:

```python
sorted(results, key=lambda r: (r.class_priority, -r.local_priority, r.entity_id))
```

**Tied results (verified 2026-10-04, `TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION`; updated by `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`).** Until the work-debt retirement the key was not unique: ID-zero system results (`DRAIN_DEBT`) tied on the whole key and were merged last-writer-wins per subsystem, bounded by a validator rule. Those results no longer exist, so **the key is unique by construction** and arrival order cannot matter.

- *Entity results* (non-zero `entity_id`) have a unique key. `ProtocolValidator.validate_result_batch` rejects a second result for one entity, and `_phase_resolution` has its own guard (`Duplicate authoritative result for entity`). A same-entity tie is therefore a protocol violation, never an ordering question.
- *No system results.* Nothing produces an `entity_id` 0 result, and the validator rejects one outright ("System results (entity id 0) are not supported"). `WorkerResult` no longer carries `work_debt_update` or `subsystem_id`, and the kernel no longer merges system results. The earlier analysis (distinct subsystems commuted; two same-subsystem results with different values would have diverged the proof digest) described a path that no shipped run exercised and that is removed. `tests/integration/kernel/test_tied_worker_result_order.py` now asserts that no two results share the full key, that permuting the arrival order leaves the ordered batch, the raw and refined updates, the state and the proof digest unchanged on the local, thread and process routes, and (non-vacuity) that the permutations really reorder a many-result scenario; `tests/unit/core/test_protocol_validator_system_results.py` pins the rejection.
- *Not covered:* combat scenarios (open ticket `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`), `audit_mode=False` (the mid-tick throttle that dropped the tail of the sorted list is report-only since `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`, but the governor's `tick_compute_ms` input still differs by host), and runs longer than five ticks.

### Rule 3: Read-only worker state

Workers receive `AuthoritativeState.readonly_view()` — a frozen snapshot. Any attempt to mutate durable state from a worker (outside the authoritative apply path) is a protocol violation caught by audit mode.

### Rule 4: Deterministic candidate sets

All entity selection operations produce `tuple(sorted(...))` results. See [candidate_selection.md](candidate_selection.md) for the three-tier selection system.

---

## Divergence detection tools

### `audit_mode`

When `kernel.audit_mode = True`, the engine fires `ProtocolViolationError` if `CanonicalStateHasher.get_hash()` changes during a non-mutating phase. This catches accidental mutations in read-only phases (e.g. a domain service writing directly to entity state rather than producing an intent).

### `audit_dirty_set=True`

Enables `DirtySetLeakError` — raised when a phase marks a dirty flag that it should not have access to. See [dirty_state_and_dependency.md](../core/dirty_state_and_dependency.md) for the 9-entity / 8-world-object flag taxonomy and which flags each phase may set.

### Per-tick digest comparison

The replay stream carries the per-tick digest in the `"hash"` payload key of each `TICK_END` `TraceEvent` (`null` with a `digest_status` when not computed; replays recorded before `TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER` carry the string `"SKIPPED"`). No code in `src/` reads it, so there is no built-in divergence detector. Regression tests compare digests themselves: a reference run and a second run from the same seed are compared tick by tick, and the first mismatch identifies the tick where divergence began. Such a comparison is a proof only when it compares proof digests (see "The canonical hash").

### Checkpoint files

`checkpoint.py` supports writing and loading `AuthoritativeState` snapshots. A checkpoint captures the full state at a given tick — loading it and continuing the simulation must produce the same downstream tick_hash sequence as an uninterrupted run.

---

## Known non-determinism sources (pre-existing, out of scope to fix)

1. **Concurrent execution mode** — OS thread scheduling is non-deterministic. Only sequential mode is guaranteed; concurrent combinations are claimed only when they pass the DET-PORT-1 matrix (not yet run).
2. **External I/O during live simulation** — if a campaign reads from a live file or socket during tick resolution, the read is non-deterministic (pre-existing: campaigns are analysis-only and run in isolation).
3. **Python float precision edge cases** — `CanonicalStateHasher` does not round floats (see "The canonical hash"). Float behavior across interpreter minor versions, operating systems, and CPU architectures is a known risk, handled by the DET-PORT tiers: a combination is unclaimed until it passes the matrix.
4. **Wall-clock and host-resource inputs** — the four inputs listed under "What runs today". `audit_mode` suppresses all four (and, because it also zeroes the replay backlog and the per-phase costs in the signals, `src/engine/kernel.py`, it neutralizes the replay-backlog trigger and `PhaseBudgetGovernor` as well); the Canonical contract replaces them with deterministic proxies (pending `PERF-M1`).

---

## Regression tests

- `tests/integration/kernel/test_determinism_suite.py` — same seed → same per-tick digest for N ticks
- `tests/integration/kernel/test_replay_fidelity.py` — checkpoint load → resume → same hash sequence
- `tests/certification/test_world_compile_determinism.py` — P0 hard gate; must pass for release

**Stability checks, not proofs.** These tests compare the fingerprint (MD5 over selected domains), not the proof digest, so they show equality only for the domains the fingerprint covers. They are valid stability checks and must not be cited as determinism proofs (PERF-D5):

- `tests/integration/kernel/test_executor_determinism.py`
- `tests/integration/kernel/test_seed_stability.py`
- `tests/perf/test_concurrency_parity.py`
- `tests/perf/test_dirty_parity.py`

PERF-D5 relabels them as stability checks or moves them to the proof digest (implementation pending `PERF-M1-T03`).

---

## Extension rules

1. Any new tick-path code that needs a random value MUST use `DeterministicRNG.get_float()/get_int()` with all four parameters. Never use stateful draws.
2. Any new pipeline phase MUST produce a candidate set via `tuple(sorted(...))`.
3. Any new worker that might mutate state must go through the authoritative apply path — never mutate `AuthoritativeState` directly in a worker.
4. If a new source of non-determinism is intentionally introduced (e.g., a live-data feature), it must be documented in known_limitations.md with its scope and rationale.
5. `audit_mode` should be enabled in all CI runs that verify the determinism guarantee.
