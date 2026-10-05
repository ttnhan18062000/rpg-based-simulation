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

- **Canonical contract.** No wall-clock or host-resource reading may influence authoritative state. Pressure signals are deterministic proxies (work-unit counts, queue depth against a fixed ceiling, work debt). The mid-tick cutoff and the end-of-tick drop are driven by a work-unit budget or are off. Guarantee: the same build, configuration, seed, and initial state give the same proof digest at every tick, whatever the host load. Required for certification, determinism and replay tests, Simulation Quality calibration, and any benchmark that claims hash parity.
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

**Today's runs satisfy neither contract fully.** Two wall-clock inputs still change what is computed, in every execution mode unless `audit_mode` is on (inputs 2 and 3 below no longer do; they are report-only):

1. `ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py`) chooses `RuntimeMode` from `tick_compute_ms`, resident memory, and worker and queue utilization; the mode then sets cadence, LOD, scan policy, and phase budgets.
2. **Report-only since `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`.** `Kernel._phase_resolution()` (`src/engine/kernel.py`) still compares elapsed wall-clock time with `profile.max_tick_budget_ms` while processing results when `audit_mode` is off, but an overrun now only records `RuntimeStatus.budget_overrun_ms` / `total_budget_overruns` and raises the watchdog alert. It no longer drops results and no longer forces `DEGRADED`. Before this ticket it did both, so what a run computed depended on host speed (`frontier_living_world`, same seed: 8 vs 10 deaths at tick 500).
3. **Report-only since `TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY`.** The end-of-tick check in `Kernel._tick_once_inner` records the same overrun signal after tick 5 instead of the `9999` dropped-work sentinel; `dropped_work` now counts only work the scheduler shed. Nothing in the governor or in `AuthoritativeState` reads the overrun signal (PERF-D1 amendment A1).
4. **World-pressure salience.** The previous tick's measured `tick_compute_ms` becomes `compute_ratio` and `global_salience` in `Kernel._phase_resolution`, is applied to `AuthoritativeState.pressure_signals` (`src/engine/apply.py`), and multiplies shop buy prices (`DynamicPriceService.calculate_buy_price`, used by `ShopService.buy_item` for the gold check and cost). A slower or busier host makes items cost more, and no `RuntimeMode` change is involved. This violates rule A1; the fix removes `compute_ratio` from `global_salience` and is pending in `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING` (it edits `src/` and waits for the RPG-core entry gate). Until then, salience still includes `compute_ratio`.

`audit_mode` zeroes the timing and resource signals, so it suppresses the first and fourth inputs, and it silences the overrun report in the second and third (`flags["audit_mode"]`, `src/engine/kernel.py`). It removes the two remaining wall-clock inputs, but it is **not sufficient on its own for a deterministic run**: before `TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK`, identical `audit_mode` runs (raised budget, sequential executor, no dropped work, governor in `NORMAL`) diverged from tick 5 because `DirtySetBuilder.mark_from_update` skipped entity updates by `id()` and a recycled address silently dropped an entity from the dirty set (`TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`). That cause is removed, and no trial diverged in 144 short (8-tick) trials after the fix, where bare `main` diverged in 8 of 96; this is a measurement over short runs, not a proof of determinism, and a second `id()`-keyed cache (`get_frozen`, `src/engine/executor.py`) was probed without a stale hit but is not proven safe. `audit_mode` is still not the Canonical contract, which has no implementation yet (`PERF-M1`).

`verification_level = REDUCED` stays the label for a run that reached `DEGRADED` or `SURVIVAL` and has no verified control trace. It discloses the problem per run and does not make the run reproducible.

**Inputs the Canonical proxy set must replace.** In addition to the two above that still change outcomes, two inputs reach control decisions and are classified by the table above: the replay-buffer backlog, which is one of the governor's `DEGRADED` triggers and depends on a background flush thread (recorded as a mode transition); and `PhaseBudgetGovernor` (`src/engine/phase_governor.py`), which reads per-phase wall-clock costs and `tick_compute_ms` directly in every mode (the "phase budgets" row). The evidence for all of this is `docs/performance/wall_clock_inventory.md`; its §6 lists what the scan could not see.

`docs/engine/runtime_profiles.md` §4 (the same profile gives identical semantics on different hardware classes) holds under the Canonical contract only.

---

## The canonical hash

Approved decision: PERF-D5. Two digest families exist, with two roles.

- **Proof digest.** `CanonicalStateHasher.get_hash()` is a flat SHA-256 over compact canonical JSON of the whole state (the scheme named `flat-sha256-v1`). It is the only value that may back a determinism, replay, certification, or parity claim.
- **Stability check.** `AuthoritativeState.fingerprint()` (`StateFingerprinter.get_fingerprint`) is an MD5 over a hand-built string of selected state domains. It does not cover all state (Place data is outside it). It is a cheap in-tick diagnostic, and it is never cited as proof that two runs are equal.

The proof digest's input is a canonical sorted JSON representation:
- All dict keys sorted lexicographically
- All entity collections sorted by entity ID

This means the digest is independent of Python dict insertion order or object identity. Two `AuthoritativeState` objects that are semantically identical produce the same digest. Floating-point values are **not** rounded before hashing: an earlier version of this document said they were, and no rounding exists in `to_canonical_data` or the component `to_canonical_dict` methods. PERF-D5 removes the claim rather than implementing it, because rounding hides small divergences and can flip at rounding boundaries; portability is handled by the DET-PORT tiers above.

**When it is computed.** The kernel computes the per-tick digest in `Kernel._phase_persistence` only when replay is allowed and (`audit_mode` is on or `replay_richness == "FULL"`); otherwise the per-tick value is the string `"SKIPPED"`. The policy gives full replay richness in `NORMAL` and `CONSTRAINED`, minimal richness in `DEGRADED` (the value is `"SKIPPED"` unless `audit_mode` forces the digest), and no replay in `SURVIVAL` (`src/engine/policy.py`), where nothing is computed or emitted per tick. The final digest at shutdown is always computed. No scheduling mechanism governs this: `CanonicalHashScheduler` is called only by the certification harness, in `FULL` mode (`docs/performance/hash_callsite_inventory.md`).

**Where it goes.** The per-tick value is the payload key `"hash"` of a `TICK_END` `TraceEvent` in the replay stream. There is no warehouse field named `tick_hash`, and nothing in `src/` reads the `TICK_END` hash.

**Coverage gap.** `AuthoritativeState.pressure_signals` is outside the proof digest (`CanonicalStateHasher`'s `to_canonical_data` has no such key), so a difference in salience is invisible to the flat hash until a purchase changes gold or inventory. This is a known gap, recorded here; no fix is decided.

**Built (`TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE`, the `src/engine/checkpoint.py` half of PERF-D5):** the scheme is named by `PROOF_DIGEST_SCHEME = "flat-sha256-v1"`; `ProofDigest` is a typed record of scheme, tick, `DigestStatus` and value; `CanonicalHashScheduler.compute_digest` returns it and reports `NOT_COMPUTED_UNSANCTIONED_BOUNDARY` instead of a stale or approximate value; and `BudgetedCanonicalHasher` and `HashMode.LIGHT` are retired. The flat hash values are unchanged. Cross-run, cross-executor and compaction parity tests now compare `CanonicalStateHasher.get_hash`; the fingerprint tests that remain are labelled as stability-check coverage tests.

**Approved, not built (PERF-D5, pending `PERF-M1-T03b`, which waits for the RPG-core entry gate because it edits `kernel.py` and `src/certification/harness.py`):** the kernel's per-tick and shutdown digests do not yet go through the scheduler or carry a scheme and typed status (the per-tick value is still the string `"SKIPPED"` when not computed); the certification harness still holds a hand-written copy of the flat hash (`tests/unit/engine/test_proof_digest_contract.py` keeps it equal to `get_hash` until the copy is replaced by a call); and when the digest is computed is not yet a declared field of the runtime profile.

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

**Tied results (verified 2026-10-04, `TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION`).** The key is not unique, and the earlier statement that it is "always total" was wrong. Verified outcome: **bounded commutative merge rules**.

- *Entity results* (non-zero `entity_id`) have a unique key. `ProtocolValidator.validate_result_batch` rejects a second result for one entity, and `_phase_resolution` has its own guard (`Duplicate authoritative result for entity`). A same-entity tie is therefore a protocol violation, never an ordering question.
- *System results* (`entity_id` 0, such as `DRAIN_DEBT`) tie on the whole key (debt is seeded in these tests; in ordinary play `work_debt` stays empty, so no DRAIN_DEBT result is produced today — see TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION). They are merged into `work_debt_updates[subsystem_id]`. Results for **distinct** subsystems write distinct keys, so they commute: permuting their arrival order left the ordered-batch content, the raw `StateUpdate`, the refined update (timing fields excluded), the authoritative state and the proof digest (`CanonicalStateHasher.get_hash`) unchanged on the local, thread and process routes, over the idle, movement, resource, strategic and a twelve-entity all-ready scenario (non-combat).
- *The bound.* The merge is last-writer-wins, not a sum. Two results for the **same** subsystem with different values would be order-dependent (the proof digest diverges; `test_mutation_proof_a_noncommutative_tie_makes_the_comparison_fail`, which injects the pair below the validator). The supported protocol is at most one debt-update system result per subsystem per tick, and it is **enforced**: `ProtocolValidator.validate_result_batch` raises `ProtocolViolationError` ("Duplicate system result for subsystem ...") for a second one (`TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM`). The shipped constructors satisfy it (the scheduler emits one `DRAIN_DEBT` item per debt key). This is not a defect record: no shipped path produced the divergent case.
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

The replay stream carries the per-tick digest (or `"SKIPPED"`) in the `"hash"` payload key of each `TICK_END` `TraceEvent`. No code in `src/` reads it, so there is no built-in divergence detector. Regression tests compare digests themselves: a reference run and a second run from the same seed are compared tick by tick, and the first mismatch identifies the tick where divergence began. Such a comparison is a proof only when it compares proof digests (see "The canonical hash").

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
