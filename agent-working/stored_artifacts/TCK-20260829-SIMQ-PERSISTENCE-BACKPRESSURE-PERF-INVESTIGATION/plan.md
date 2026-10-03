---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION
artifact_type: plan
tags: [performance, observability, simulation-quality]
---

# Implementation Plan — TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION

## Summary

This plan fixes both root causes the investigation isolated under the "persistence" umbrella,
makes the explicit no-fix call on `CanonicalStateHasher`, and resolves the resource-budget
question with a concrete mechanism — closing all 4 of the ticket's Acceptance Criteria without
re-opening anything Investigate already decided.

**Root cause #1** (`ReplayManager._rotate_chunk()`'s redundant synchronous JSON serialization,
`src/engine/replay_manager.py:184-207`) is fixed by *deleting* the synchronous pre-check
serialization entirely and moving the budget-check log to reuse a byte-size figure the
background thread already computes for an unrelated purpose (`_execute_persistence()`'s rolling
chunk-size average, `replay_manager.py:279-291`) — zero new serialization work added, one full
redundant `json.dumps` walk removed per chunk rotation, and the main tick thread no longer does
any JSON work during `_rotate_chunk()` at all.

**Root cause #2** (unconditional per-record `.flush()` in `QualityPersistence.write()` and
`EventRecorder._write_envelope_to_file()`) is fixed with a batch-of-50 counter-based flush
(deliberately *not* wall-clock/interval-based — this codebase already has one documented,
already-deferred nondeterminism hazard from wall-clock-measured budgets in `kernel.py`'s
mid-resolution throttle, so a deterministic write-count trigger is the architecturally consistent
choice here), with an unconditional flush preserved at `shutdown()` in both classes so no data is
lost at run end. Both files verified to have exactly one writer (the single background
`QueueDrainWorker` thread, confirmed by tracing `quality_hub.py:174`'s `on_envelope` — injected as
`quality_fn` — and `event_recorder.py`'s `file_write_fn`, both called from
`src/observability/queue.py:126-154`'s single `_run()` loop), so a plain unlocked instance counter
is safe and consistent with the existing no-lock code in both classes.

**`CanonicalStateHasher` cadence is explicitly NOT touched** — documented as a deliberate no-fix
decision with rationale (Step 4), satisfying AC2's "or a documented decision not to fix" branch.

**Resource-budget: Option A is selected** (a new `resource_budget_large` pytest marker, read by
`tests/conftest.py`'s existing `pytest_runtest_setup` hook) — confirmed on reading the hook
(`tests/conftest.py:70-102`) that inserting a marker check between the existing `budget == "off"`
early-return and the `small`/`large`/`medium` branching is a 2-line, low-risk change, not the
"materially harder than assumed" case that would justify falling back to Option B.

No `docs/` changes are required: `INFRA-193`, `INFRA-223`, `INFRA-194`, `INFRA-198`, `INFRA-199`,
`INFRA-320` were all read in full from `docs/parity_ledger/infrastructure.yaml` and none of their
`text` fields describe the per-write flush cadence or the pre-check's exact synchronous-serialization
mechanism as contractual — only `ArtifactBudgetRegistry.check()`'s size/action/logging behavior
(`INFRA-193`, P1, untouched — the code block Step 1 relocates is literally tagged with an inline
`# INFRA-193:` comment at `replay_manager.py:182`; its ledger `text` requires only that `.check()`
correctly compute size/action and log per INFRA-060, not that the caller compute the size
synchronously-before-dispatch on the main thread — confirmed by reading `tests/certification/
test_artifact_budget.py` in full, which has no assertion on call-site timing, only
`async_write=False` used deliberately in one test to avoid thread races, not to assert production
timing), hash cadence (`INFRA-223`, untouched), inflight-count/backpressure logic (`INFRA-198`,
untouched — this plan only relocates the budget *log*, not the inflight/dispatch code),
mode-threshold math (`INFRA-194`/`INFRA-199`, untouched), and the drop/survival guard itself
(`INFRA-320` — status `verified`, **priority P0** (corrected from an earlier draft's incorrect
"none of these are P0" characterization — `docs/parity_ledger/infrastructure.yaml:7939`), **with a
populated, passing `test_path`**: `tests/simulation_quality/test_calibrate_simq.py::
TestQueueOverflowGuard::test_calibrate_simq_fails_on_forced_queue_overflow`, `::
test_calibrate_simq_succeeds_normally_with_zero_drops`, `::TestSurvivalModeGuard::
test_survival_mode_flags_run_instead_of_silently_grading`, and `tests/simulation_quality/
test_evaluate_harness.py::TestQueueOverflowGuardIntegration::test_evaluate_simq_flags_queue_overflow_run`
— both files are already listed as Step 2's regression suite below, so the P0 test_path requirement
is already satisfied by this plan's existing test scope; untouched — this plan reduces the
*frequency* of the condition INFRA-320's guard detects, it does not change the guard's own logic).

## Steps

### Step 1 — Remove `_rotate_chunk()`'s synchronous budget pre-check serialization
**Files:** `src/engine/replay_manager.py`

**Change:** Delete the entire `try/except` block at `replay_manager.py:184-207` inside
`_rotate_chunk()` (the local `_to_dict` closure, `estimated_bytes = len(json.dumps(...))`, and the
`get_default_registry().check("replay_chunk", estimated_bytes)` + `logger.warning(...)` call). This
is the block the investigation identified (`investigation.md` "Root cause #1") as fully
re-serializing the entire chunk buffer synchronously on the main tick thread purely to estimate a
byte size for a warning log, confirmed by direct read of `replay_manager.py:176-246`.

Move the budget check into `_execute_persistence()` (`replay_manager.py:253-296`), immediately
after the existing `chunk_bytes = len(json.dumps([_to_dict(e) for e in events], default=str).encode())`
computation at `replay_manager.py:287` (verified by reading this block: it already computes a full
serialized byte count of the same `events` list, for the unrelated purpose of updating
`self._avg_chunk_size_bytes`, an exponential moving average used by `replay_metrics()`). Reuse that
already-computed `chunk_bytes` value for the budget check instead of re-serializing:

```python
_bcheck = get_default_registry().check("replay_chunk", chunk_bytes)
if _bcheck.action in ("warn", "reject"):
    logger.warning(
        "ReplayManager: budget %s for replay_chunk — size=%.2f MB reason=%s",
        _bcheck.action, chunk_bytes / 1048576, _bcheck.reason,
    )
```
placed inside the same `try/except Exception: pass` block that already wraps the `chunk_bytes`
computation (`replay_manager.py:278-293`), preserving the existing "budget check must never stall
the pipeline" (M6 Law / INFRA-060) swallow-on-error behavior that the original code had via its own
separate `try/except Exception as _budget_err: logger.debug(...)`.

`get_default_registry` is already imported at module level (`replay_manager.py:9`) and already used
inside `_rotate_chunk` today, so no new import is needed — just relocation of the call site.

Net effect: the main tick thread's `_rotate_chunk()` call now does only `self._buffer.extract_chunk()`,
inflight-lock bookkeeping, and `self._executor.submit(...)` dispatch — no JSON work at all. The
`async_write=False` finalize/shutdown path (`replay_manager.py:147`, `_rotate_chunk(..., async_write=False)`)
still calls `_execute_persistence()` directly and therefore still runs the budget check
synchronously in that one legitimately-synchronous shutdown case — unchanged behavior there, as
intended ("this one can be synchronous as the kernel is shutting down", `replay_manager.py:146`).

**Other writers to this resource:** `_execute_persistence()`'s `chunk_bytes`/`_avg_chunk_size_bytes`
computation (`replay_manager.py:277-293`) is the only other code that serializes `events` for a
size estimate, and this step makes it the *sole* one, eliminating the duplicate. No other code path
calls `get_default_registry().check("replay_chunk", ...)` (confirmed: it is the only call site in
`replay_manager.py`, and `get_default_registry()` itself is a single-instance registry shared
read-only by `.check()` calls from potentially other subsystems, but none write to it — `.check()`
is pure/read-only per `src/certification/artifact_budget.py:87` signature `check(self, artifact_type, estimated_size_bytes) -> BudgetCheckResult`, no mutation).

**Do NOT touch:** the `_inflight_count`/`_inflight_lock`/`_max_pending_flushes` backpressure logic
(`replay_manager.py:212-226`, INFRA-198) — this step only relocates the budget-check *log line*, not
the dispatch/backpressure bookkeeping around it. Do NOT touch `_execute_persistence()`'s actual
`self._sink.persist_chunk(...)` write call (`replay_manager.py:262`) or `replay_sink.py`'s
`_clean_for_json`/`persist_chunk` — those are the real, necessary write path, not redundant.

**Verify:** New/extended test `test_rotate_chunk_does_not_serialize_synchronously_on_main_thread` in
`tests/unit/kernel/test_replay_chunk_rotation.py` — patch/spy `json.dumps` (or the budget-registry
`.check()` call) and assert it is not invoked before `_rotate_chunk()`'s `executor.submit()` call
returns control to the caller, only after the submitted future actually runs. Regression:
`tests/unit/kernel/test_replay_chunk_rotation.py`, `test_replay_contract.py`, `test_replay_overflow.py`,
`test_replay_pressure.py`, `test_replay_shutdown_budget.py`, `tests/unit/engine/test_replay_backpressure.py`,
`test_resource_budget_gate.py`, `tests/certification/test_artifact_budget.py` (none of these assert
flush count or the exact synchronous timing of the old pre-check, confirmed by grep — no `flush`
references and no assertions on `json.dumps`/`_to_dict` call-site timing found in
`test_replay_chunk_rotation.py` or `test_replay_backpressure.py`).

---

### Step 2 — Batch `QualityPersistence.write()`'s flush cadence
**Files:** `src/simulation_quality/persistence.py`

**Change:** In `QualityPersistence.__init__()` (`persistence.py:17-25`), add
`self._pending_writes: int = 0` and a class constant `_FLUSH_INTERVAL: int = 50`. In `write()`
(`persistence.py:27-45`), replace the unconditional `self._file_handle.flush()` at line 43 with:
```python
self._pending_writes += 1
if self._pending_writes >= self._FLUSH_INTERVAL:
    self._file_handle.flush()
    self._pending_writes = 0
```
Rationale for N=50: the investigation's cProfile run recorded 4237 `QualityPersistence.write()`
calls over 500 ticks (`investigation.md` cProfile excerpt, `persistence.py:27 (write)` row, 4237
calls). N=50 cuts flush syscalls by ~98% (4237 → ~85) while bounding worst-case unflushed data at
shutdown-crash to 49 records of a non-authoritative diagnostic file — acceptable because
`quality_scores.jsonl` is explicitly non-authoritative telemetry (`docs/engine/kernel.md`'s
`PERSISTENCE (non-authoritative)` phase row governs the *tick-phase*, but this file's own role —
scored diagnostic records for `evaluate_simq.py`, not replay/determinism-critical state — carries
no durability contract in the Mechanics Bible or engine contracts; confirmed no parity ledger entry
asserts per-record flush timing for `quality_scores.jsonl`). A counter-based trigger (not a
wall-clock interval) is used deliberately: this same investigation documents an already-deferred
nondeterminism hazard from wall-clock-measured budgets elsewhere in `kernel.py` (the mid-resolution
throttle) — introducing a *second* wall-clock-driven behavior difference in a related subsystem
during the same ticket would compound exactly the class of issue the ticket's own "Kernel
Wall-Clock Throttle Relationship" section was careful to keep separate. A deterministic per-N-writes
trigger has no such dependency.

`shutdown()` (`persistence.py:76-84`) already calls `self._file_handle.flush()` unconditionally
before `close()` — leave this as-is; it already satisfies "must still flush on close/finalize" for
any records buffered below the N=50 threshold at shutdown time. No change needed there.

**Other writers to this resource:** `self._file_handle` in `QualityPersistence` has exactly one
write call site (`write()`, `persistence.py:42`) and one close call site (`shutdown()`,
`persistence.py:80`). `write()` is called from exactly one place in the codebase:
`src/simulation_quality/quality_hub.py:174` (`self._persistence.write(record)`, inside
`QualityHub.on_envelope()`). `on_envelope` is itself injected as the `quality_fn` callback into
`EventRecorder`'s `QueueDrainWorker` (confirmed via `src/simulation_quality/feed.py:35`'s comment
and `event_recorder.py:100-105`'s `QueueDrainWorker(..., quality_fn=quality_fn)` construction), and
`QueueDrainWorker._run()` (`src/observability/queue.py:126-154`) calls `quality_fn` synchronously,
sequentially, from its own single daemon thread — no other thread ever calls `write()`. This means
the new `self._pending_writes` counter needs no lock, consistent with the class's existing
lock-free design. **Pre-existing, out-of-scope hazard found while verifying this** (not introduced
or worsened by this step): `Kernel.shutdown()` (`src/engine/kernel.py:1174-1200`) calls
`_persistence.shutdown()` (closing/nulling the file handle, line 1188-1196) *before*
`self._event_recorder.shutdown()` (line 1198-1199) stops the drain-worker thread — so any envelope
still in flight through the drain worker between those two calls will find `write()`'s
`self._file_handle is None` guard (`persistence.py:28-29`) and silently no-op. This ordering issue
exists identically with or without this step's flush-batching change (it is about handle-closing
order, not flush cadence) — flagging it as a candidate for a future ticket, not fixing it here (out
of this ticket's scope per "never plan more work than ticket scope").

**Do NOT touch:** `write_report()`/`write_run_health()` (`persistence.py:47-74`) — these write to
different files (`quality_report.json`, `.run_health.json`) via their own `with open(...)` blocks,
already correctly flush-on-close via the `with` statement, and are out of this step's scope (no
per-record flush issue exists there — each is a single whole-file overwrite via temp+rename, not a
per-record append).

**Verify:** New/extended test `test_quality_persistence_write_does_not_flush_every_record` in
`tests/simulation_quality/test_persistence.py` — spy `self._file_handle.flush` (or the handle object)
and assert flush call count is less than write call count for N>1 writes, and assert a `shutdown()`
call always flushes any remainder. Regression: `tests/simulation_quality/test_persistence.py`,
`test_evaluate_harness.py`, `test_quality_hub_integration.py`, `test_calibrate_simq.py`,
`test_broker_feed_integration.py`, `test_performance.py`, `tests/perf/test_simq_isolation_overhead.py`
(grep confirmed no `flush` references in `test_persistence.py` today, so no existing assertion
depends on every-write-flushes-immediately timing).

---

### Step 3 — Batch `EventRecorder._write_envelope_to_file()`'s flush cadence
**Files:** `src/observability/event_recorder.py`

**Change:** In `EventRecorder.__init__()` (`event_recorder.py:58-107`), add
`self._pending_envelope_writes: int = 0` and reuse the same `_FLUSH_INTERVAL = 50` convention as
Step 2 (same rationale: 5432 `EventRecorder._write_envelope_to_file()` calls measured over 500
ticks in the investigation's cProfile run, `event_recorder.py:151 (record)` — note the cProfile
listing's `record` row count (5432) corresponds 1:1 with envelope writes since every accepted
`record()` call pushes exactly one envelope that the drain worker later writes; N=50 cuts flush
syscalls by ~98% here too, same non-authoritative/deterministic-trigger rationale as Step 2). In
`_write_envelope_to_file()` (`event_recorder.py:109-127`), replace the unconditional
`self._file_handle.flush()` at line 127 with the same batch-of-50 pattern:
```python
self._pending_envelope_writes += 1
if self._pending_envelope_writes >= self._FLUSH_INTERVAL:
    self._file_handle.flush()
    self._pending_envelope_writes = 0
```

Additionally, in `shutdown()` (`event_recorder.py:301-322`), add an explicit
`self._file_handle.flush()` immediately before the existing `self._file_handle.close()` call
(currently `event_recorder.py:317-321` only calls `close()`, relying on Python's implicit
close-flushes-first behavior for `TextIOWrapper`). This is a belt-and-suspenders addition — not
strictly required since `close()` already flushes internally — added for explicitness and to
mirror `QualityPersistence.shutdown()`'s already-explicit flush-then-close convention
(`persistence.py:79-80`), so both non-authoritative writer classes in this ticket read the same way.

**Other writers to this resource:** `self._file_handle` in `EventRecorder` has exactly one write
call site, `_write_envelope_to_file()`, invoked from two places: (a) as `file_write_fn` inside
`QueueDrainWorker._run()`'s loop (`queue.py:131-136`, the single background daemon thread — the
steady-state caller), and (b) directly from `EventRecorder.shutdown()`'s own final drain loop
(`event_recorder.py:307-312`, `for env in remaining: self._write_envelope_to_file(env)`), which runs
on the shutdown-caller's thread. These two call sites never overlap: `shutdown()` calls
`self._worker.stop()` first (`event_recorder.py:304-305`), which sets `running = False` and joins
the drain thread (`queue.py:120-124`, `self._thread.join(timeout=1.0)`) before `shutdown()`
proceeds to its own manual drain loop — so the two writers are sequential, not concurrent, and a
plain unlocked counter remains safe. (Note: `join(timeout=1.0)` is not an unconditional wait — if
the drain thread somehow didn't finish within 1s this ordering guarantee would weaken, but the
drain loop's own 10ms `interval_sec` sleep makes that scenario a pre-existing, unrelated
timing edge case, not something this step's flush-batching change introduces or worsens.)

**Do NOT touch:** `_publish_envelope_to_stream()` (`event_recorder.py:129-149`) — a separate
sink (in-process event stream adapter, no file I/O, no flush semantics) — out of scope. Do NOT
touch `record()`'s mode-transition logic (`event_recorder.py:151-223`, `INFRA-199`) or
`pressure_report()` (`INFRA-194`) — this step only changes `_write_envelope_to_file()`'s internal
flush cadence, not queue admission or mode evaluation.

**Verify:** New/extended test `test_event_recorder_write_envelope_does_not_flush_every_record` in
`tests/unit/observability/test_event_recorder.py` — same spy-on-flush-count pattern as Step 2, plus
an explicit assertion that `shutdown()` flushes any remaining buffered writes. Regression:
`tests/unit/observability/test_event_recorder.py`, `test_event_recorder_quality_fn.py`,
`test_obs_backpressure.py`, `tests/unit/observability/stream/test_phase21_bounded_observability_queue.py`,
`tests/unit/test_queue_worker_singleton.py`, `tests/unit/engine/test_lifecycle_supervisor.py` (grep
confirmed no `flush` references in `test_event_recorder.py` today).

---

### Step 4 — Document the explicit decision NOT to change `CanonicalStateHasher` cadence
**Files:** `tickets/inprogress/TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION.md`
(Implementation Notes section — no `src/` or `docs/` file changes)

**Change:** This is a documentation-only step with no code change. Add to the ticket's
`## Implementation Notes` section an explicit statement: "`CanonicalStateHasher.get_hash()`'s
every-tick cadence in NORMAL/CONSTRAINED mode (`src/engine/checkpoint.py:38-107`,
`Kernel._phase_persistence()` at `src/engine/kernel.py:1158-1172`) is deliberately NOT changed by
this ticket. Rationale: it is a `verified`, P2 parity-ledger contract (`INFRA-223`,
`docs/parity_ledger/infrastructure.yaml:2737-2752`), documented identically in
`docs/engine/known_limitations.md` §2.4 and `docs/engine/kernel.md`, that exists specifically to
give replay/determinism verification a fresh canonical hash every tick in the common case. Routing
it through the already-present but currently-bypassed `BudgetedCanonicalHasher`
(`checkpoint.py:110-155`) would reduce persistence cost but would also measurably reduce per-tick
determinism-verification coverage — a real product/architecture trade-off, not a pure efficiency
win like Steps 1-3. This ticket's own scope explicitly allows closing AC2 via 'a concrete fix (or a
documented decision not to fix, with rationale)' — this is that documented decision. Changing this
cadence remains available as a future ticket, gated on a fresh, explicit
`docs/guidelines/intentional_divergences.md` entry and user sign-off, not a default assumed here."

**Do NOT touch:** `src/engine/checkpoint.py` (no code change at all — `CanonicalStateHasher`,
`BudgetedCanonicalHasher`, `to_canonical_json`, `to_canonical_data` all remain byte-for-byte
unmodified), `Kernel._phase_persistence()`'s hash-gating conditional (`kernel.py:1158-1172`),
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-223` entry (no `v2_evidence` re-verification is
needed because nothing it describes changed), `docs/engine/known_limitations.md` §2.4,
`docs/engine/kernel.md`'s hash-cadence table.

**Verify:** No new test. Confirm `tests/integration/kernel/test_determinism_suite.py`
(`INFRA-223`'s own `test_path`) still passes unmodified as a "nothing changed here" regression
check, alongside the rest of the determinism/checkpoint suite listed in `test_plan.md`'s
"canonical hash / determinism" block — run only if Steps 1-3's diff is later found to touch
anything in `kernel.py`'s persistence phase (it should not; Steps 1-3 only touch
`replay_manager.py`, `persistence.py`, `event_recorder.py`).

---

### Step 5 — Add the `resource_budget_large` pytest marker mechanism
**Files:** `tests/conftest.py`, `pyproject.toml`

**Change:** In `tests/conftest.py`'s `pytest_runtest_setup(item)` (`conftest.py:70-102`), insert a
marker check between the existing early return for `budget == "off"` (line 76-77) and the
`small`/`large`/`medium` branching (line 80 onward):
```python
def pytest_runtest_setup(item):
    budget = item.config.getoption("--resource-budget")
    if budget == "off":
        return

    if item.get_closest_marker("resource_budget_large") is not None:
        budget = "large"

    if budget == "small":
        ...
```
Precedence decided explicitly: `--resource-budget off` (the profiler-use-case escape hatch,
per the existing comment at `conftest.py:74`) always wins over the marker — a marked test run with
`--resource-budget off` still gets no enforcement at all, consistent with off's existing meaning.
Any other CLI value (`small`, `medium`, the `large` default) is overridden to `large` when the
marker is present, including the case where a caller explicitly passed `small` — the marker exists
specifically because these tests cannot complete under any budget shorter than `large` regardless
of what the CLI default says, per the ticket's own Scope text ("marking them to always run with
`--resource-budget large`").

Register the new marker in `pyproject.toml`'s `[tool.pytest.ini_options]` `markers` list
(`pyproject.toml:63-89`), matching the existing convention (every other marker in that list is
registered there, e.g. `"slow: marks tests as slow ..."`):
```
"resource_budget_large: forces --resource-budget large (600s/8GB) regardless of the CLI default; for tests inherently >60s (TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION)",
```

This mechanism was confirmed on reading `tests/conftest.py` in full to be a small, low-risk,
additive change — not the "materially harder than assumed" case the ticket flagged as a possible
reason to fall back to Option B. Option A is selected as planned.

**Other writers to this resource:** `item.config.getoption("--resource-budget")` is read-only
config, set once per pytest invocation from the CLI/default (`pytest_addoption`, `conftest.py:58-65`)
— no other hook or fixture mutates it. `pytest_runtest_teardown` (`conftest.py:104-111`) only calls
`signal.alarm(0)` to disable the timer, unrelated to budget resolution. No collision.

**Do NOT touch:** `pytest_collection_modifyitems` (`conftest.py:113-130`, the `TAXONOMY_MARKERS`
enforcement for `tests/parity/`) — unrelated marker-enforcement logic for a different test
directory, not touched by this step. Do NOT change the `small`/`medium`/`large` memory/time limit
values themselves (`conftest.py:80-88`) — only which bucket a marked test resolves into.

**Verify:** New test `test_resource_budget_marker_applies_large_to_named_grade_stability_tests` in
new file `tests/tools/test_conftest_resource_budget.py` — verify the marker overrides `budget` to
`"large"` inside `pytest_runtest_setup` for a synthetic marked test item (e.g. construct/mock a
minimal `item` with `get_closest_marker` returning a marker, call the hook function directly, and
assert the effective time/mem limits chosen equal the `large` branch's values), and that
`--resource-budget off` still short-circuits regardless of the marker.

---

### Step 6 — Apply the `resource_budget_large` marker to the 6 named tests
**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`

**Change:** Add `@pytest.mark.resource_budget_large` alongside the existing `@pytest.mark.slow`
decorator (confirmed present today via direct read, e.g. `test_corpus_diversity.py:742-743`,
`:842-843`, `:942-943`, `:1044-1045`, `:1129-1130`, `:1247-1248`) on exactly these 6 test functions:
`test_simq_routing_test_seed42_1000t_cognition_grade_stability`,
`test_hero_guild_routing_seed42_1000t_cognition_grade_stability`,
`test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability`,
`test_urban_political_seed42_1000t_social_grade_stability`,
`test_urban_political_seed123_1000t_social_economy_grade_stability`,
`test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability`. Do not add the
marker to any of the file's other tests.

**Do NOT touch:** Any floor/tolerance constant, assertion value, or scenario/seed parameter inside
these 6 test bodies, or any of the file's other ~141 tests — marker addition only. This is the
explicit scope guard both the ticket's Out of Scope section and `test_plan.md`'s Anti-Drift Test
Guards call out by name.

**Verify:** `test_resource_budget_marker_applies_large_to_named_grade_stability_tests` (Step 5) plus
manually confirming (via `pytest --collect-only -m resource_budget_large tests/unit/worldassembly/test_corpus_diversity.py`)
that exactly these 6 tests collect under the new marker, no more, no fewer.

---

### Step 7 — Before/after profiling verification and perf-regression guard
**Files:** `tests/perf/test_persistence_phase_cost.py` (new)

**Change:** After Steps 1-3 land, reproduce the investigation's own clean (no-cProfile) 500-tick
`urban_political`/`seed=42` `_run_engine` run (same harness, same `no_frame_pacing=True`) and
compare `persistence`-phase share of total tick cost against the investigation's documented
pre-fix baseline (mean=8.891ms, sum=4445.7ms, 29.3% share of total tick cost across 500 ticks,
with three >150ms spikes at the ~100-tick chunk-rotation boundaries — `investigation.md`'s "Clean
(no-profiler) run" section). Record the actual post-fix numbers in the ticket's Implementation
Notes (do not invent a threshold before measuring). Then add a soft-monitor perf-regression guard
test, `test_persistence_phase_cost_regression_guard_1000t` in new file
`tests/perf/test_persistence_phase_cost.py` (per `test_plan.md`'s AC2 test spec), that runs a
~1000-tick real `_run_engine` scenario and emits a `PerformanceThresholdWarning`
(`tests/tools/perf_assertions.py`'s existing pattern, per `docs/testing/regression_policy.md` §3) —
not a hard failure — if `persistence`-phase share of total tick cost sum exceeds a ceiling set from
the measured post-fix number plus headroom (e.g. post-fix% + 10 percentage points, to avoid CI
hardware-variance false positives), and does not assert on the eliminated ~100-tick spikes
specifically (those should simply be gone after Step 1, verified qualitatively in the
before/after report, not asserted as a hard per-tick ceiling that could be CI-flaky).

**Do NOT touch:** `tools/calibrate_simq.py::_run_engine`'s own logic — this step only calls it as a
test harness, exactly as the existing 6 grade-stability tests and the investigation's own profiling
scripts already do. Do NOT add a hard-fail assertion — `test_corpus_diversity.py` and this new perf
guard both stay soft-monitor per `docs/testing/regression_policy.md` §3, matching the existing
`tests/perf/test_simq_isolation_overhead.py` convention.

**Verify:** The new `test_persistence_phase_cost_regression_guard_1000t` test itself (soft-monitor,
warns not fails), plus the manually-recorded before/after numbers written into the ticket.

**Depends on:** Steps 1, 2, 3 (needs the actual fix in place to measure a real "after" number).

---

### Step 8 — Re-run the 6 named tests and report outcome (AC4)
**Files:** None (verification/reporting step only — no source changes)

**Change:** Run:
```
.venv/bin/python3 -m pytest \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_1000t_cognition_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_hero_guild_routing_seed42_1000t_cognition_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed42_1000t_social_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_1000t_social_economy_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability" \
  -q
```
(no `--resource-budget large` CLI flag needed now — the marker from Step 6 forces it). Record the
outcome for each of the 6 tests in the ticket's Test Summary / Completion Summary: pass, or a
`CalibrationIntegrityError`/floor-tolerance failure — and if the latter, explicitly state that
re-baselining those tests is out of scope for this ticket and needs its own follow-up ticket, per
the ticket's own Out of Scope section and the parent `TCK-20260828` ticket's precedent.

**Do NOT touch:** the 6 tests' assertions/floors, even if some still fail after the fix — report
only, per AC4's "or a now-clean floor/tolerance drift needing its own re-baseline ticket" wording.

**Verify:** The 6 tests' actual pass/fail results, reported verbatim.

**Depends on:** Steps 1, 2, 3 (perf fix), Step 6 (marker applied).

---

### Step 9 — Confirm no `docs/` or parity-ledger updates are required
**Files:** None (confirmation-only step)

**Change:** Re-confirm, after Steps 1-3's actual diff is final, that `INFRA-193`, `INFRA-223`,
`INFRA-194`, `INFRA-198`, `INFRA-199`, and `INFRA-320` in `docs/parity_ledger/infrastructure.yaml`
still accurately describe current behavior (they should, since none of Steps 1-3 change
`ArtifactBudgetRegistry.check()`'s own size/action/logging semantics — `INFRA-193`, P1, added to
this list per architecture-review finding: the exact code block Step 1 relocates is tagged with an
inline `# INFRA-193:` comment at `replay_manager.py:182`; its ledger `text` requires only that
`.check()` correctly compute size/action and log, not that the caller compute the size
synchronously-before-dispatch on the main thread — confirmed by reading `tests/certification/
test_artifact_budget.py` in full, no timing assertion exists there — or hash cadence,
inflight-count/backpressure logic, mode-threshold math, or the drop/survival guard's own logic —
only the placement of a budget-check log line and the flush cadence of two writers). `INFRA-320` is
`status: verified`, **priority P0** (corrected here from an earlier draft of this plan, which
incorrectly stated "none of these are P0" — `docs/parity_ledger/infrastructure.yaml:7939`), with a
populated `test_path` covering `tests/simulation_quality/test_calibrate_simq.py::
TestQueueOverflowGuard::test_calibrate_simq_fails_on_forced_queue_overflow`, `::
test_calibrate_simq_succeeds_normally_with_zero_drops`, `::TestSurvivalModeGuard::
test_survival_mode_flags_run_instead_of_silently_grading`, and `tests/simulation_quality/
test_evaluate_harness.py::TestQueueOverflowGuardIntegration::test_evaluate_simq_flags_queue_overflow_run`
— all four already fall within Step 2's regression-test scope below, so this P0 entry's "passing
test_path" requirement is satisfied by this plan's existing test coverage with no additional test
work; this step just requires confirming they actually pass post-fix. Record this confirmation in
the ticket's Implementation Notes. No parity ledger YAML edits, no
`docs/guidelines/intentional_divergences.md` entry (no intentional behavioral divergence from any
Mechanics Bible or engine-contract-described law was made — Steps 1-3 are pure I/O-efficiency
changes with no documented contract asserting the old, slower shape as required).

**Do NOT touch:** Any file under `docs/parity_ledger/`, `docs/engine/`, or
`docs/guidelines/intentional_divergences.md`.

**Verify:** N/A (documentation confirmation only). If Steps 1-3's actual implementation diverges
from this plan in a way that touches hash cadence, backpressure thresholds, or guard logic, this
step must be re-done before ticket close.

---

### Step 10 — Ticket closeout
**Files:** `tickets/inprogress/TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION.md`

**Change:** Fill in `## Implementation Notes` (Steps 4 and 9's write-ups, plus the concrete N=50
flush-interval numbers and their rationale), `## Test Summary` (all new/extended tests from Steps
1-3, 5, 7, plus the 6-test outcome from Step 8), `## Files Changed` (the file list from Steps 1, 2,
3, 5, 6, 7), and `## Completion Summary`. Move ticket to `tickets/done/`, move staging artifacts to
`stored_artifacts/`, append `tickets/working_log.csv`, per the standard Workflow Rule After-Work
checklist.

**Do NOT touch:** Anything outside this ticket's own files during closeout.

**Verify:** `done-checker` agent's Definition-of-Done checklist, including `frontmatter_valid`.

## Scope Guards

- `src/engine/checkpoint.py` (`CanonicalStateHasher`, `BudgetedCanonicalHasher`) — no code change,
  per Step 4's explicit no-fix decision.
- `src/engine/kernel.py`'s mid-resolution wall-clock throttle block (~lines 594-610 in this
  checkout) — already-deferred, separately-tracked nondeterminism finding; not this ticket's scope,
  per the ticket's own Out of Scope section and `investigation.md`'s "Kernel Wall-Clock Throttle
  Relationship" verdict that the two mechanisms are architecturally adjacent but not the same code
  path.
- `tests/unit/worldassembly/test_corpus_diversity.py`'s floor/tolerance constants and any of its
  other ~141 tests beyond the marker addition in Step 6.
- `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s navigation logic (already complete, unrelated).
- `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`'s fix area (already complete,
  unrelated).
- `BoundedObservabilityQueue.max_size`/`EventRecorder.max_events` — do not raise these as a
  workaround for `CalibrationIntegrityError`; per `investigation.md`'s Anti-Drift Hazards, that
  would mask the drain-worker throughput ceiling rather than fix it.
- `ReplayManager`'s `_inflight_count`/`_max_pending_flushes` backpressure/dispatch logic
  (`INFRA-198`) and `EventRecorder`'s `ObservabilityController`/mode-transition logic (`INFRA-199`)
  — Steps 1-3 touch only budget-check placement and flush cadence, not these.
- `src/engine/replay_sink.py`'s `_clean_for_json`/`persist_chunk` — the real, necessary write path;
  not redundant, not touched.
- The pre-existing `Kernel.shutdown()` ordering hazard found while verifying Step 2 (SimQ
  persistence shutdown before EventRecorder/drain-worker shutdown) — documented as a future-ticket
  candidate, not fixed here.

## Dependency Map

- Steps 1, 2, 3 are independent of each other (different files, different root causes) — any order,
  or parallel.
- Step 4 (no-fix documentation) is independent of all other steps — can run anytime.
- Step 5 (marker mechanism) is independent of Steps 1-4.
- Step 6 (apply marker) depends on Step 5 (marker must exist first).
- Step 7 (before/after profiling + perf guard) depends on Steps 1, 2, 3 (needs the real fix to
  measure a real "after").
- Step 8 (re-run 6 tests) depends on Steps 1, 2, 3 (perf fix) and Step 6 (marker applied).
- Step 9 (docs confirmation) logically follows Steps 1-3's final diff, but has no code dependency.
- Step 10 (closeout) depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — Real profiling data identifies the specific bottleneck | Already satisfied by `investigation.md` (cProfile + clean-baseline runs); Step 7 re-confirms with a before/after comparison | `investigation.md`'s documented profiling runs; Step 7's before/after numbers recorded in the ticket |
| AC2 — A concrete fix (or documented decision not to fix) is implemented and verified to reduce persistence phase cost meaningfully for a representative 1000-tick run | Steps 1, 2, 3 (concrete fixes for Root causes #1 and #2); Step 4 (documented no-fix decision for `CanonicalStateHasher`) | Step 1: `test_rotate_chunk_does_not_serialize_synchronously_on_main_thread`; Step 2: `test_quality_persistence_write_does_not_flush_every_record`; Step 3: `test_event_recorder_write_envelope_does_not_flush_every_record`; Step 7: `test_persistence_phase_cost_regression_guard_1000t` + before/after numbers |
| AC3 — `--resource-budget` question is explicitly decided | Step 5 (Option A: `resource_budget_large` marker mechanism, decided and implemented, not left ambiguous) | `test_resource_budget_marker_applies_large_to_named_grade_stability_tests` |
| AC4 — The 6 named tests are re-run under the fix and outcome reported | Step 6 (marker applied to the 6 tests) + Step 8 (re-run and report) | Step 8's direct re-run of the 6 tests; outcome recorded in ticket Completion Summary |

## Anti-Drift Notes

- Do not conflate the `persistence` **tick-phase** (canonical hash + replay chunk rotation, Step 1
  + Step 4) with the `QualityPersistence`/`EventRecorder` **telemetry-write pipeline** (Steps 2-3) —
  they remain different code paths with different fixes, per `investigation.md`'s central finding.
  Both must be addressed (or explicitly not) for AC2 to be satisfiable; do not consider Step 1 alone
  sufficient to close AC2.
- The N=50 flush-interval numbers (Steps 2, 3) are a deliberate, justified choice, not a stand-in
  for "batch by some amount" — do not let Implement pick a different number without updating this
  plan's rationale (measured call counts, ~98% syscall reduction, bounded 49-record worst-case
  crash-loss window on non-authoritative telemetry).
- Do not let the `resource_budget_large` marker (Step 5) silently affect any test outside the 6
  named in Step 6 — the marker mechanism itself is directory/file-agnostic (a pytest marker, not a
  path-based override), so scope is enforced entirely by which tests get the decorator, not by the
  conftest.py change itself.
- `test_corpus_diversity.py` remains a Soft Monitor (`docs/testing/regression_policy.md` §3) — Step
  6's marker addition does not change that classification.
- The `Kernel.shutdown()` ordering hazard noted in Step 2 (SimQ persistence shutdown races ahead of
  EventRecorder/drain-worker shutdown) is real but out of scope — do not fix it inside this ticket;
  flag it for a follow-up ticket at closeout if not already filed.
- Root cause #1's fix changes *when* the budget-check warning log fires (now after async dispatch,
  from the background thread, instead of before dispatch on the main thread) — this is intentional
  and non-blocking either way; do not treat a shifted log-line timestamp as a regression.

## Unresolved Questions

None. All decisions the investigation deliberately left open (Root cause #1/#2 fix shape,
`CanonicalStateHasher` no-fix call, resource-budget Option A vs B) are resolved above with concrete,
evidence-backed choices. No genuine new architectural conflict or ambiguity surfaced while reading
the actual code beyond the pre-existing, out-of-scope `Kernel.shutdown()` ordering hazard noted in
Step 2 and the Scope Guards / Anti-Drift Notes above, which does not change this plan's approach.

## Deviations

Recorded during Implement — none change the plan's substance, all are execution-detail
corrections discovered by actually running the tests, per CLAUDE.md's "never silently deviate" rule.

1. **Step 1 test design changed from timing-based to thread-identity-based.** The plan's literal
   text ("assert it is not invoked before `_rotate_chunk()`'s `executor.submit()` call returns
   control to the caller") is inherently racy in practice: `ThreadPoolExecutor`'s background thread
   can (and did, in a real run) complete the submitted `_execute_persistence()` call before the main
   thread's very next assertion line executes, since the work is trivially fast for a 1-2-event test
   chunk. The implemented test (`test_rotate_chunk_does_not_serialize_synchronously_on_main_thread`,
   `tests/unit/kernel/test_replay_chunk_rotation.py`) instead asserts on **which thread** ever called
   the budget-check registry's `.check()` — polling until at least one call is observed, then
   asserting none of the observed calls came from `threading.main_thread()`. This proves the same
   fact the plan wanted (no budget-check work runs on the main tick thread inside `_rotate_chunk()`)
   without a race-prone "assert nothing happened yet" step.

2. **Two pre-existing tests in `tests/simulation_quality/test_persistence.py` needed updating,
   contradicting the plan's "no existing assertion depends on every-write-flushes-immediately
   timing" claim.** `test_write_appends_jsonl_line` and `test_write_multiple_appends_multiple_lines`
   both read `quality_scores.jsonl` from disk immediately after `write()`, before `shutdown()` —
   a grep for the literal string `flush` (what the plan checked) does not catch this, since the
   dependency is behavioral (immediate on-disk visibility), not a literal flush assertion. With
   Step 2's N=50 batching in place these two tests failed (0 lines / empty file) because nothing had
   crossed the flush threshold yet. Fixed by moving the file-read assertions to after
   `persistence.shutdown()` (which still unconditionally flushes any remainder) instead of before it
   — the same fix pattern the plan already specified for the new Step 2 test. No assertion values
   changed, only read-timing relative to shutdown.

3. **`test_quality_persistence_shutdown_flushes_remaining_records`'s own exact-flush-count
   assertion needed loosening from `== 1` to `>= 1`.** Discovered while writing the Step 2 test:
   `io.TextIOWrapper.close()` internally calls the object's own (possibly monkeypatched) `.flush()`
   a second time in addition to `QualityPersistence.shutdown()`'s own explicit `.flush()` call before
   `.close()` — both go through the same Python-level attribute when a test spies on `.flush()` by
   instance-attribute override. This is pre-existing `shutdown()` behavior (unchanged by this
   ticket), not a new double-flush introduced by Step 2 — the test now asserts "at least one flush
   happened," which is the actual invariant Step 2's Verify text asked for ("a `shutdown()` call
   always flushes any remainder").

4. **Step 7's regression-guard test drives the real `Kernel` directly (same approach as the
   investigation's own `clean_baseline.py` script) rather than calling `tools.calibrate_simq._run_engine()`
   directly**, because `_run_engine()` does not expose per-tick `Kernel._phase_costs` to its caller
   (it only returns `(run_dir, elapsed, run_id)`) — the persistence-phase-share measurement needs the
   phase breakdown that only reading `kernel._phase_costs` after each `tick_once()` provides. This
   matches the plan's own text ("same harness, same `no_frame_pacing=True`") in spirit (same world,
   same seed, same flags, same Kernel construction path `_run_engine()` itself uses) while actually
   being able to compute the persistence share the test needs.

5. **Step 7's measured post-fix numbers** (500-tick clean run, same methodology as
   `investigation.md`'s baseline): mean=8.817ms, median=7.417ms, p90=11.916ms, **max=83.507ms**
   (down from the pre-fix baseline's max=243.150ms — confirms Root cause #1's spike elimination),
   sum=4408.6ms, persistence share=30.3% (pre-fix: 29.3%). A separate 1000-tick clean run (the
   representative length AC2 asks for) measured persistence share=23.3%, feeding the regression
   guard's locked ceiling of 33.3% (23.3% + 10pp headroom, per plan). The `persistence`-phase's
   mean/sum barely moves because that phase's steady-state cost is dominated by
   `CanonicalStateHasher.get_hash()` (deliberately untouched, Step 4) — Root cause #1's fix
   eliminates the ~100-tick-periodic *spikes* specifically (the dominant driver of `max`), and Root
   cause #2's fix (flush batching) targets the separate `QualityPersistence`/`EventRecorder`
   telemetry pipeline's per-record syscall overhead, which is not part of `_phase_costs["persistence"]`
   at all — exactly the two-different-root-causes distinction `investigation.md`'s central finding
   already called out. Root cause #2's real effect is visible in Step 8's outcome instead: all 6
   named tests now complete (no `CalibrationIntegrityError`, no `TimeoutError`) where they previously
   did not.

6. **Step 8 outcome**: 5 of 6 named tests pass. `test_urban_political_seed42_1000t_social_grade_stability`
   fails, but with a genuine floor/tolerance drift (`SOCIAL: mean_score=36.8373` vs.
   `anchor_score=15.45`, tolerance `abs_floor=6.5052`, per-trial values `[32.3, 34.424, 43.788]`) —
   not a `CalibrationIntegrityError` and not a `TimeoutError`. This is exactly the "now-clean
   floor/tolerance drift needing its own re-baseline ticket" outcome AC4 anticipated; per the plan's
   explicit "Do NOT touch" instruction for this step, the assertion/floor was left unmodified and is
   reported here for a follow-up re-baseline ticket, not fixed in this one.
