---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260702-OBSISO-BROKER-CONFIG
artifact_type: plan
tags: [observability, simulation-quality, broker-mode, redis, configuration, kernel]
---

# Implementation Plan — TCK-20260702-OBSISO-BROKER-CONFIG

## Summary

Two independent, additive bugs are fixed. **G1** (stream-name/broker-url mismatch): `BrokerQualityFeed.__init__`
and `build_feed_from_env()` (`src/simulation_quality/feed.py`) and `QualityWorker.__init__`
(`src/simulation_quality/worker.py`) currently hardcode `"sim:events"` / `"redis://localhost:6379"` as their
ultimate fallback, while the producer (`ObservabilityConfig.get_stream_name()`/`get_redis_url()`,
`src/observability/config.py:331-338`) defaults to `"simulation:events"` / `redis://localhost:6379/0`. The
fix makes `BrokerQualityFeed.__init__` the single place that resolves the ultimate default (via
`Optional[str] = None` parameters that fall back to `ObservabilityConfig` when unset), and has both
`build_feed_from_env()` and `QualityWorker.__init__` simply forward `os.environ.get("QUALITY_*")` (which is
`None` when unset) instead of hardcoding a second, independently-stale literal. This keeps explicit
`QUALITY_STREAM_NAME`/`QUALITY_BROKER_URL` overrides working exactly as before, and means the default only
has to be correct in one place. **G3** (in-engine hub/thread in broker mode): `Kernel.__init__`
(`src/engine/kernel.py:227-268`) currently builds all 10 pillar scorers, a `QualityHub`, and (via the
existing `if self._quality_feed is not None and self._quality_hub is not None: self._quality_feed.start(...)`
guard at lines 267-268) starts a `"broker-quality-feed"` consumer thread inside the engine process
regardless of `QUALITY_FEED_MODE`. The fix wraps only the hub-construction block in
`if not isinstance(_feed, BrokerQualityFeed):`, checking the already-resolved feed instance (not re-reading
`QUALITY_FEED_MODE` from env a second time). `self._quality_feed = _feed` is hoisted out of that new
conditional so it is still set in broker mode (for future introspection) — but because `self._quality_hub`
now stays `None` for a `BrokerQualityFeed`, the existing unmodified line 267-268 guard already prevents
`.start()` from being called, so no new thread spawns. This is a minimal, surgical diff: one import change,
one new `if` wrapping the existing hub-construction block, no change to the `EventRecorder` construction or
the `.start()` call site itself.

Two decisions blocking Plan are resolved here (see Step 3 and Step 5) rather than deferred: the
`QUALITY_RUN_DIR` default is changed from the fixed literal `"data/runs/quality_worker"` to
`f"data/runs/{run_id}"` (worker-local fix, no cross-process run_id propagation invented — see Step 3
rationale); and the pre-existing bound-method-vs-string bug in
`test_broker_feed_integration.py::test_broker_feed_graceful_when_redis_unavailable` is fixed in-place because
the new AC #1 test must extend this exact file as its stated pattern and cannot trust a file with a
known-broken assertion sitting next to it.

## Steps

### Step 1 — G1 fix: `BrokerQualityFeed` resolves defaults through `ObservabilityConfig`
**Files:** `src/simulation_quality/feed.py`
**Change:**
- Change `BrokerQualityFeed.__init__` signature from
  `(broker_url: str = "redis://localhost:6379", stream_name: str = "sim:events", consumer_group: str = "quality_scoring")`
  to `(broker_url: Optional[str] = None, stream_name: Optional[str] = None, consumer_group: str = "quality_scoring")`.
  Inside `__init__`, add a lazy import (matching the existing lazy-import style already used inside
  `start()` at lines 73-74): `from src.observability.config import ObservabilityConfig`. Resolve:
  `self._broker_url = broker_url if broker_url is not None else ObservabilityConfig.get_redis_url()` and
  `self._stream_name = stream_name if stream_name is not None else ObservabilityConfig.get_stream_name()`.
  This is the single place the ultimate default is computed — do not duplicate `ObservabilityConfig` calls
  elsewhere.
- In `build_feed_from_env()` (currently line 130-135), change the broker branch from
  `stream_name=os.environ.get("QUALITY_STREAM_NAME", "sim:events")` /
  `broker_url=os.environ.get("QUALITY_BROKER_URL", "redis://localhost:6379")` to
  `stream_name=os.environ.get("QUALITY_STREAM_NAME")` / `broker_url=os.environ.get("QUALITY_BROKER_URL")`
  (no hardcoded fallback string — `os.environ.get(...)` returns `None` when unset, which now correctly
  triggers `__init__`'s own `ObservabilityConfig` fallback). `consumer_group` keeps its existing
  `"quality_scoring"` literal default unchanged — G1 only covers stream name and broker URL, not consumer
  group (no producer-side equivalent exists to route through).
- Update the existing default value shown in any docstring/comment in this file that still says
  `"sim:events"` (there is none beyond the two sites above per investigation.md's confirmed line numbers).
**Do NOT touch:** `InProcessQualityFeed` (any method), `QualityFeedMode` enum, `QualityFeedAdapter` ABC,
`consumer_group`'s default value, the `QUALITY_SCORING_DISABLED` short-circuit at the top of
`build_feed_from_env()` (must remain the first check, unmodified).
**Verify:**
- New unit test 1 — `test_broker_stream_name_defaults_to_observability_config` (`tests/simulation_quality/test_feed.py`):
  with no `QUALITY_STREAM_NAME`/`SIM_STREAM_NAME`/`RPG_STREAM_NAME` env vars set,
  `build_feed_from_env()` under `QUALITY_FEED_MODE=broker` yields a `BrokerQualityFeed` whose
  `_stream_name == "simulation:events"`; also assert `QUALITY_STREAM_NAME` still overrides when set.
- New unit test 2 — `test_broker_url_defaults_to_observability_config` (`tests/simulation_quality/test_feed.py`):
  same shape, for `_broker_url` vs `ObservabilityConfig.get_redis_url()`.
- Existing `tests/simulation_quality/test_feed.py::test_broker_feed_skips_gracefully_when_redis_unavailable`
  (constructs `BrokerQualityFeed(broker_url="redis://127.0.0.1:19999")` with no `stream_name` arg) must
  still pass unchanged — it does not assert on `_stream_name`, only on `health()["status"]`, so the new
  default resolution does not affect it.
- Existing `test_broker_feed_stop_is_noop` (`feed = BrokerQualityFeed()`, no args) must still construct
  without raising — confirms the `None`-triggers-`ObservabilityConfig`-lookup path doesn't blow up when
  `SIM_STREAM_NAME`/`SIM_REDIS_URL` are also unset (falls through to `ObservabilityConfig`'s own hardcoded
  final defaults).

### Step 2 — G1 fix: `QualityWorker` forwards, does not hardcode, stream/broker defaults
**Files:** `src/simulation_quality/worker.py`
**Change:** In `QualityWorker.__init__` (lines 72-76), change
```python
self._feed = BrokerQualityFeed(
    broker_url=os.environ.get("QUALITY_BROKER_URL", "redis://localhost:6379"),
    stream_name=os.environ.get("QUALITY_STREAM_NAME", "sim:events"),
    consumer_group=os.environ.get("QUALITY_CONSUMER_GROUP", "quality_scoring"),
)
```
to
```python
self._feed = BrokerQualityFeed(
    broker_url=os.environ.get("QUALITY_BROKER_URL"),
    stream_name=os.environ.get("QUALITY_STREAM_NAME"),
    consumer_group=os.environ.get("QUALITY_CONSUMER_GROUP", "quality_scoring"),
)
```
No hardcoded `"sim:events"`/`"redis://localhost:6379"` literal remains in `worker.py` — the default now
comes entirely from Step 1's `BrokerQualityFeed.__init__` fallback, so this file needs no
`ObservabilityConfig` import of its own.
**Do NOT touch:** the `scorers = [AgencyScorer(weights), CombatScorer(weights)]` line (lines 69, G2 — out of
scope, covered by `TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX`), `weights_path`/`grade_path`/`detection_path`/
`profile` resolution, the health-server/HTTP handler, signal handling, `run()`.
**Verify:** New unit test 3 — `test_quality_worker_stream_name_defaults_to_observability_config`
(new file `tests/simulation_quality/test_worker.py`): construct `QualityWorker()` with no `QUALITY_*`/
`SIM_STREAM_*` env vars set, assert `worker._feed._stream_name == "simulation:events"` and
`worker._feed._broker_url == ObservabilityConfig.get_redis_url()`'s default value; also assert
`QUALITY_STREAM_NAME`/`QUALITY_BROKER_URL` still override when explicitly set.

### Step 3 — Run-dir decision: `QUALITY_RUN_DIR` default ties to `QUALITY_RUN_ID`, not a fixed literal
**Files:** `src/simulation_quality/worker.py`
**Decision:** Option (a) from investigation.md ("point `QUALITY_RUN_DIR` at the engine's `run_id` pattern")
requires the worker process to *receive* the engine's `run_id`, which today only happens via the operator
setting `QUALITY_RUN_ID` — there is no cross-process channel that lets the worker discover the engine's
`self._run_id` automatically (the worker is a separate process/container; inventing such a channel, e.g.
embedding run_id in the stream name or a discovery side-channel, is a larger architecture change and belongs
with `TCK-20260702-OBSISO-ISOLATION-PROOF` or a future ticket, not this one). What **is** in scope and a
real, local bug: the worker's own two knobs, `QUALITY_RUN_DIR` and `QUALITY_RUN_ID`, are currently
*inconsistent with each other* — `QUALITY_RUN_DIR` defaults to the fixed literal `"data/runs/quality_worker"`
regardless of what `QUALITY_RUN_ID` is set to, so two operators who correctly set distinct `QUALITY_RUN_ID`
values (to avoid stamping score records with the same run ID) still collide on the same output directory
unless they *also* separately set `QUALITY_RUN_DIR`. Fix: default `QUALITY_RUN_DIR` from the already-resolved
`run_id`, so setting `QUALITY_RUN_ID` alone is sufficient to avoid collision — a one-line, purely local
change requiring no cross-process coordination.
**Change:** In `QualityWorker.__init__`, reorder so `run_id` is resolved before `run_dir`, then default
`run_dir` from it:
```python
run_id = os.environ.get("QUALITY_RUN_ID", "broker_worker")
run_dir = os.environ.get("QUALITY_RUN_DIR", f"data/runs/{run_id}")
```
(replaces current lines 65-66, which compute `run_dir` first with the fixed literal, then `run_id`
separately). `QUALITY_RUN_DIR` remains a full explicit override when set — this only changes the *default*.
**Operational note (add to docs, see Step 7):** broker-mode deployments still collide if two engine runs
share the same `QUALITY_RUN_ID` default (`"broker_worker"`) — operators running more than one concurrent
broker-mode worker must set distinct `QUALITY_RUN_ID` values per run; this was already true before this
fix (the collision surface is not new) and remains an operational responsibility, not a code defect, given
the worker's process-isolation design (one worker process per logical run/deployment, consistent with
`docs/plans/observability_process_isolation.md` R4).
**Do NOT touch:** `QUALITY_WEIGHTS_PATH`/`QUALITY_GRADE_PATH`/`QUALITY_DETECTION_PATH`/`QUALITY_PROFILE`
resolution (unrelated env vars, unaffected by this reorder).
**Verify:** New test (beyond test_plan.md's original 8 — added here because Step 3 is a real behavior
change per the Testing Rule, and test_plan.md could not have specified it since this decision was explicitly
left open for Plan) — `test_quality_worker_run_dir_defaults_to_run_id` (`tests/simulation_quality/test_worker.py`,
same new file as Step 2's test): with `QUALITY_RUN_ID=my-run` set and `QUALITY_RUN_DIR` unset, assert
`worker._persistence`'s run dir (or equivalent introspectable attribute — check
`QualityPersistence.__init__`'s stored attribute name before writing the assertion) resolves to
`"data/runs/my-run"`, not `"data/runs/quality_worker"`.

### Step 4 — G3 fix: kernel builds zero hub / starts zero consumer threads in broker mode
**Files:** `src/engine/kernel.py`
**Change:** In `Kernel.__init__` (current lines 227-268):
1. Change the import at line 232 from `from src.simulation_quality.feed import build_feed_from_env` to
   `from src.simulation_quality.feed import build_feed_from_env, BrokerQualityFeed`.
2. Hoist `self._quality_feed = _feed` (currently set inside the `try` block at line 256) to immediately
   after `if _feed is not None:` (currently line 234), so it is set for *both* in-process and broker feeds
   before any mode branching.
3. Wrap the existing hub-construction block (the `from src.simulation_quality.weights import ScoringWeights`
   line through the `try`/`except` that builds `_weights`, `_hub`, sets `_quality_fn`/`self._quality_hub`) in
   `if not isinstance(_feed, BrokerQualityFeed):`. Detect broker mode by inspecting the already-constructed
   `_feed` instance's concrete type — **do not** re-read `QUALITY_FEED_MODE` from `os.environ` a second time
   inside `Kernel.__init__` (per investigation.md's Risk note: `build_feed_from_env()` already read it once;
   a second independent read risks skew under test env-var monkeypatching mid-call and is not a single
   source of truth).
4. Leave lines 260-268 (the `EventRecorder(...)` construction and the
   `if self._quality_feed is not None and self._quality_hub is not None: self._quality_feed.start(self._quality_hub)`
   guard) **completely unmodified**. This guard already does the correct thing once step 3 makes
   `self._quality_hub` stay `None` for a `BrokerQualityFeed` — `.start()` is simply never called, so no
   `"broker-quality-feed"` thread spawns. Do not add a second, redundant mode-check here.
5. Update the `quality_hub` property docstring (currently line 326): `"""Read-only access to the QualityHub
   instance (None if SimQ is disabled)."""` → `"""Read-only access to the QualityHub instance (None if SimQ
   is disabled or QUALITY_FEED_MODE=broker — broker-mode scoring runs in the external QualityWorker
   process, not in-engine)."""`.
**Do NOT touch:** the `EventRecorder(...)` constructor call or its arguments, the
`self._workers_started = 2 if (obs_mode != ObservabilityMode.OFF) else 0` counter at line 306 (per
investigation.md's Risk note — it is already correct for the desired end-state and must not be "helpfully"
adjusted), `self._entity_timeline_store`, `self._metric_recorder`/`self._cognition_recorder`/
`self._decision_trace_writer`/`self._personality_recorder` construction (lines 271-298, unrelated to SimQ).
**Verify:**
- New test 5 — `test_kernel_broker_mode_builds_zero_quality_hub`
  (`tests/simulation_quality/test_kernel_simq_integration.py`): `Kernel.__init__` with
  `QUALITY_FEED_MODE=broker` → `kernel._quality_hub is None`.
- New test 6 — `test_kernel_broker_mode_starts_zero_consumer_threads` (same file): after that same
  `Kernel.__init__`, no thread named `"broker-quality-feed"` in `threading.enumerate()`.
- New test 7 — `test_kernel_inprocess_mode_unaffected_by_g3_fix` (same file): re-assert, independent of the
  4 existing unchanged tests, that `QUALITY_FEED_MODE=inprocess` still produces a non-`None`
  `kernel._quality_hub` with all 10 scorers present — guards against an implementation that branches on
  "is broker mode requested" (env-var string comparison) instead of "is `_feed` concretely a
  `BrokerQualityFeed`" (isinstance check).
- New test 8 — `test_quality_scoring_disabled_still_wins_in_both_modes` (same file): with
  `QUALITY_SCORING_DISABLED=1`, `kernel._quality_hub is None` and no `"broker-quality-feed"` thread exists,
  under **both** `QUALITY_FEED_MODE=inprocess` and `QUALITY_FEED_MODE=broker`.
- Existing `tests/simulation_quality/test_kernel_simq_integration.py`'s 4 tests
  (`test_simq_hub_wired_into_kernel`, `test_no_second_drain_worker`, `test_event_recorder_worker_has_quality_fn`,
  `test_20_tick_run_produces_nonzero_tick_count`), run under their existing `QUALITY_FEED_MODE=inprocess`
  fixture default, must pass **unchanged** — hard stop if any fail, not a test to "update" (per ticket AC #3).

### Step 5 — Fix pre-existing bug in `test_broker_feed_integration.py` (in-scope, justified)
**Files:** `tests/simulation_quality/test_broker_feed_integration.py`
**Decision:** Fix, not work around. `test_broker_feed_graceful_when_redis_unavailable` (line 33) currently
asserts `feed.health == "unavailable"` — comparing `BrokerQualityFeed.health` (a bound method object) to a
string, which is always `False` and has never actually executed because the module is
`@pytest.mark.skipif(not REDIS_AVAILABLE, ...)`-gated by default. Step 6 must extend this exact file (per
ticket AC #1's explicit instruction to follow "the existing pattern in
`tests/simulation_quality/test_broker_feed_integration.py`"), so this file must actually be a working
pattern, not a silently-broken one sitting one test above the new addition. The fix is a one-line, obviously
correct change with zero G1/G3 behavioral coupling.
**Change:** Line 33: `assert feed.health == "unavailable"` → `assert feed.health()["status"] == "unavailable"`.
**Do NOT touch:** `test_broker_feed_dedup_same_event_id` (the other test in this file — unrelated, already
correct), the module-level `REDIS_AVAILABLE`/`pytestmark` skip gate, `@pytest.mark.slow` markers.
**Verify:** `test_broker_feed_graceful_when_redis_unavailable` passes when run with `REDIS_AVAILABLE=1` (this
test mocks `RedisStreamConsumer` and does not require a live Redis instance despite the gate — confirm it
runs in the environment used for verification; if genuinely unavailable, document the skip explicitly per
test_plan.md's instruction rather than silently passing over it).

### Step 6 — New AC #1 integration test: producer/consumer share stream name with zero env vars
**Files:** `tests/simulation_quality/test_broker_feed_integration.py` (extended, not a new file — the ticket's
AC #1 explicitly names this file's pattern, and a second broker-integration file would fragment the same
`REDIS_AVAILABLE`/`@pytest.mark.slow` gating surface for no benefit)
**Change:** Add `test_no_env_vars_set_broker_mode_producer_consumer_share_stream_name`: with no
`QUALITY_*`/`SIM_STREAM_*` env vars set (`monkeypatch.delenv` each), `QUALITY_FEED_MODE=broker`,
`SIM_STREAM_BACKEND=redis`, publish one event via `get_event_stream_adapter().publish(event)`
(`src/observability/stream/factory.py`) and confirm a `BrokerQualityFeed`/`QualityWorker`-side consumer
receives it without any manual stream-name alignment — i.e. the producer and consumer resolve to the same
stream key (`"simulation:events"`) purely from Step 1/2's fix. Follow the same `REDIS_AVAILABLE`-gated,
`@pytest.mark.slow` pattern as the two existing tests in this file (now that Step 5 has fixed the pattern).
**Do NOT touch:** anything in `src/` in this step — this step is test-only, depends on Steps 1, 2, and 5
already being complete.
**Verify:** The new test itself, run with `REDIS_AVAILABLE=1`. This is the direct test for ticket AC #1.

### Step 7 — Docs: `docs/guides/simulation_quality.md`
**Files:** `docs/guides/simulation_quality.md`
**Change:**
- "Environment variables" table (currently lines 90-106): update `QUALITY_BROKER_URL`'s Default column from
  `redis://localhost:6379` to `ObservabilityConfig.get_redis_url()` (`SIM_REDIS_URL`/`RPG_REDIS_URL`, else
  `redis://localhost:6379/0`) and `QUALITY_STREAM_NAME`'s Default column from `sim:events` to
  `ObservabilityConfig.get_stream_name()` (`SIM_STREAM_NAME`/`RPG_STREAM_NAME`, else `simulation:events`).
  Update `QUALITY_RUN_DIR`'s Default column from `data/runs/quality_worker` to `data/runs/{QUALITY_RUN_ID}`
  per Step 3. Add a new **Owning Process** column to the whole table (per ticket AC #5, "Config docs list
  every env var with its default and owning process") — populate from source: `QUALITY_SCORING_DISABLED`/
  `QUALITY_FEED_MODE` → Engine only (`build_feed_from_env()` is called only from `kernel.py`);
  `QUALITY_BROKER_URL`/`QUALITY_STREAM_NAME`/`QUALITY_CONSUMER_GROUP` → Engine + Worker (both construct a
  `BrokerQualityFeed`); `QUALITY_WEIGHTS_PATH`/`QUALITY_GRADE_PATH`/`QUALITY_DETECTION_PATH`/
  `QUALITY_PROFILE` → Engine + Worker (both resolve independently); `QUALITY_RUN_DIR`/`QUALITY_RUN_ID` →
  Worker only; `QUALITY_WORKER_PORT` → Worker only. Also add the three `ObservabilityConfig`-owned vars that
  now matter for broker-mode stream/URL resolution: `SIM_STREAM_NAME`/`RPG_STREAM_NAME` and
  `SIM_REDIS_URL`/`RPG_REDIS_URL` and `SIM_STREAM_BACKEND`/`RPG_STREAM_BACKEND` → Engine (producer,
  `src/observability/config.py`).
- "Feed modes" → "Broker" subsection (currently lines 296-308): update the example command block's
  `QUALITY_STREAM_NAME=sim:events` line to either omit it (showing the zero-env-var-needed default now
  works) or change it to `QUALITY_STREAM_NAME=simulation:events` with a note that this line is now optional
  since it matches the producer default automatically. Add the operational note from Step 3 about
  `QUALITY_RUN_ID` needing to be distinct per concurrent worker to avoid `QUALITY_RUN_DIR` collision.
**Do NOT touch:** "Grade scale" section, endpoint documentation above the env var table, anything about
scorer pillar counts (G2 territory).
**Verify:** No automated test covers doc-table completeness in this repo; verify by manual cross-check
against Steps 1-3's actual `os.environ.get(...)` call sites (grep `QUALITY_` and `SIM_`/`RPG_` prefixed env
var reads across `feed.py`, `worker.py`, `config.py` and confirm every one appears in the table).

### Step 8 — Docs: `docs/simulation_quality/quality_scoring_contract.md` §3.4
**Files:** `docs/simulation_quality/quality_scoring_contract.md`
**Change:**
- Line 166 table: update `QUALITY_STREAM_NAME`'s Default from `sim:events` to `ObservabilityConfig.get_stream_name()`
  (`simulation:events` when no override), and `QUALITY_BROKER_URL`'s Default similarly, matching Step 7.
- Line ~176 (`InProcessQualityFeed.start() registers a drain callback on BoundedObservabilityQueue`):
  **decision** — fix this in the same step, not a follow-up ticket. Rationale: this is the exact section
  already being edited for the G1 default-value correction (same doc, same §3.4, few lines away), the
  statement is factually false against current code (`InProcessQualityFeed.start()` at `feed.py:43-44` only
  stores the hub reference; the actual `EventRecorder(quality_fn=...)` wiring happens in `kernel.py`), and
  leaving a directly false sentence sitting inside a section this ticket's own diff already touches is worse
  than the small cost of correcting it. This is a doc-text-only correction with zero code-behavior coupling
  (distinct from G2/G5, which are out-of-scope *code* changes). Replace with: "`InProcessQualityFeed.start()`
  stores the `QualityHub` reference for health/stop reporting; the actual envelope delivery is wired by the
  kernel injecting `quality_fn=hub.on_envelope` into `EventRecorder`'s `QueueDrainWorker` at kernel init
  time (`kernel.py`)."
**Do NOT touch:** any other section of `quality_scoring_contract.md` (§3.1-3.3, §3.5+), the
`QualityFeedAdapter` interface code block (unchanged, still accurate).
**Verify:** Manual review — no automated doc test exists for this file's prose accuracy.

### Step 9 — Parity ledger: two new entries
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Current max ID in the file is `INFRA-316` (confirmed by direct scan of the file tail at
Plan-writing time — re-confirm this is still the max immediately before implementation, since other
in-flight tickets may claim IDs first). Add two new entries, appended after the current last entry:

```yaml
- id: INFRA-317
  text: >
    TCK-20260702-OBSISO-BROKER-CONFIG (G1) -- BrokerQualityFeed.__init__, build_feed_from_env(), and
    QualityWorker.__init__ resolve stream_name and broker_url through
    ObservabilityConfig.get_stream_name()/get_redis_url() (src/observability/config.py) when
    QUALITY_STREAM_NAME/QUALITY_BROKER_URL are unset, instead of an independently-hardcoded
    "sim:events"/"redis://localhost:6379" default that diverged from the producer's
    "simulation:events" default and left broker mode silently dead out-of-box. Explicit
    QUALITY_STREAM_NAME/QUALITY_BROKER_URL overrides continue to take precedence.
  status: missing
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    (fill in at implementation close) src/simulation_quality/feed.py (BrokerQualityFeed.__init__,
    build_feed_from_env()), src/simulation_quality/worker.py (QualityWorker.__init__).
  proof_type: regression
  test_path: tests/simulation_quality/test_feed.py::test_broker_stream_name_defaults_to_observability_config,tests/simulation_quality/test_feed.py::test_broker_url_defaults_to_observability_config,tests/simulation_quality/test_worker.py::test_quality_worker_stream_name_defaults_to_observability_config,tests/simulation_quality/test_broker_feed_integration.py::test_no_env_vars_set_broker_mode_producer_consumer_share_stream_name
  divergence_note: null
  support_boundary: >
    Config default-value resolution only -- no change to RedisStreamAdapter/RedisStreamConsumer
    wire behavior, no new stream backend, no change to consumer_group defaulting.

- id: INFRA-318
  text: >
    TCK-20260702-OBSISO-BROKER-CONFIG (G3) -- when QUALITY_FEED_MODE=broker, the engine process
    (src/engine/kernel.py, Kernel.__init__) constructs zero QualityHub instances and starts zero
    Redis consumer threads. Kernel detects broker mode by inspecting the resolved feed instance
    (isinstance(_feed, BrokerQualityFeed)), not by re-reading QUALITY_FEED_MODE from env a second
    time. In-process mode (QUALITY_FEED_MODE=inprocess, the default) is unaffected -- the kernel
    still builds all 10 pillar scorers and a QualityHub exactly as before. This closes the isolation
    gap where broker-mode scoring ran fully in-engine (defeating the purpose of broker mode) and
    could double-consume the same Redis consumer group alongside an external QualityWorker.
  status: missing
  priority: P0
  legacy_evidence: null
  v2_evidence: >
    (fill in at implementation close) src/engine/kernel.py (Kernel.__init__, ~lines 227-268 and the
    quality_hub property docstring).
  proof_type: regression
  test_path: tests/simulation_quality/test_kernel_simq_integration.py::test_kernel_broker_mode_builds_zero_quality_hub,tests/simulation_quality/test_kernel_simq_integration.py::test_kernel_broker_mode_starts_zero_consumer_threads,tests/simulation_quality/test_kernel_simq_integration.py::test_kernel_inprocess_mode_unaffected_by_g3_fix,tests/simulation_quality/test_kernel_simq_integration.py::test_quality_scoring_disabled_still_wins_in_both_modes
  divergence_note: null
  support_boundary: >
    Kernel-side mode-routing only -- QualityWorker's own scorer completeness (G2) and any
    broker-vs-inprocess performance comparison (G5) are explicitly out of scope and not claimed by
    this entry.
```

P0 for INFRA-318 is justified because this is the process-isolation guarantee R4 exists for
(`docs/plans/observability_process_isolation.md`), the ticket's own AC #2 already demands exactly this
assertion, and Steps 4's tests 5/6 make a passing `test_path` achievable at close (satisfying the repo rule
that P0 entries require one). P1 for INFRA-317 matches the ticket's own overall P1 priority — a config
default-value bug, not an isolation-guarantee violation.
**Do NOT touch:** `INFRA-233`, `INFRA-239` (both confirmed unaffected by investigation.md — no status/text
change needed).
**Verify:** `parity-updater` agent (or manual check) confirms both entries' `status` flips to `verified` and
`v2_evidence` is filled in once Steps 1-6 land and their test_paths pass.

## Scope Guards

Must NOT be touched by this ticket's implementation, per ticket Out of Scope and investigation.md's
Anti-Drift Hazards:
- `InProcessQualityFeed`'s behavior (any method) — already correct, unrelated to G1/G3.
- `ObservabilityConfig.get_stream_name()`/`get_redis_url()`/`get_stream_backend()` themselves — SimQ routes
  *through* these, does not rename, wrap, or restructure them.
- `QualityWorker`'s scorer list (`scorers = [AgencyScorer(weights), CombatScorer(weights)]`,
  `worker.py:69`) — G2, covered by `TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX`.
- Any benchmark/performance measurement comparing broker vs in-process overhead — G5, covered by
  `TCK-20260702-OBSISO-ISOLATION-PROOF`.
- `self._workers_started` counter logic (`kernel.py:306`) — already correct for the desired end-state; do
  not "fix" it as part of the G3 change.
- `docs/engine/contracts/infrastructure_compat_contract.md` — investigation.md flagged this as an optional
  judgment call. **Decision: skip.** The contract's §3 general language ("core engine... importable without
  external infrastructure... present") already covers the intent, and it does not currently name any
  specific broker (RabbitMQ/Kafka/Postgres are mentioned generically, not individually) — singling out
  Redis/SimQ for this ticket would be an inconsistent one-off addition to a contract doc that isn't otherwise
  itemized per-subsystem. No change to this file in this ticket.
- The `QUALITY_SCORING_DISABLED=1` short-circuit (`feed.py`, top of `build_feed_from_env()`) — must remain
  the first check, unmodified in position, in all of Steps 1 and 4's edits.
- `EventRecorder`'s constructor call and arguments (`kernel.py:260-265`) — untouched by Step 4.
- `test_kernel_simq_integration.py`'s existing 4 tests — must pass unchanged, never edited to "make them
  pass."

## Dependency Map

- Steps 1, 2, 3, 4, 5, 7, 8 are independent of each other and can be implemented/verified in any order.
- Step 6 depends on Steps 1, 2, and 5 (needs the fixed defaults to have something correct to assert, and
  needs the pre-existing bug fixed to trust the file's pattern).
- Step 9 depends on Steps 1-6 having landed (parity entries cite those tests' paths; entries should only
  flip to `verified` once the cited tests actually pass).
- Steps 7 and 8 (docs) should be done after Steps 1-3 are finalized, since they document the exact resolved
  defaults and table shape those steps produce — but nothing blocks writing them in parallel and
  reconciling before close.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — no `QUALITY_*`/`SIM_STREAM_*` env vars, broker mode: events published are consumed by `QualityWorker` | Steps 1, 2, 5, 6 | `tests/simulation_quality/test_broker_feed_integration.py::test_no_env_vars_set_broker_mode_producer_consumer_share_stream_name` |
| AC #2 — broker mode: engine starts zero SimQ scorer objects and zero Redis consumer threads | Step 4 | `test_kernel_simq_integration.py::test_kernel_broker_mode_builds_zero_quality_hub`, `::test_kernel_broker_mode_starts_zero_consumer_threads` |
| AC #3 — in-process mode: `test_kernel_simq_integration.py` and `test_feed.py` pass unchanged | Steps 1, 2, 4 (must not regress either file) | Existing `test_kernel_simq_integration.py`'s 4 tests + existing `test_feed.py`'s 12 tests, plus new `::test_kernel_inprocess_mode_unaffected_by_g3_fix` as an explicit re-assertion |
| AC #4 — `QUALITY_SCORING_DISABLED=1` still disables everything in both modes | Steps 1, 4 (must preserve short-circuit ordering) | Existing `test_build_feed_returns_none_when_disabled` (INFRA-233) + new `::test_quality_scoring_disabled_still_wins_in_both_modes` |
| AC #5 — config docs list every env var with default and owning process | Steps 7, 8 | Manual completeness review (no automated doc-table test exists in this repo) |

## Anti-Drift Notes

- The G3 fix must key off `isinstance(_feed, BrokerQualityFeed)`, not a second `os.environ.get("QUALITY_FEED_MODE")`
  read — `build_feed_from_env()` already read that env var once; a second independent read is a
  single-source-of-truth violation and risks skew under test monkeypatching mid-call (investigation.md
  Risk).
- Do not conflate this ticket's G1/G3 with the *older*, already-closed G1/G3 numbering from
  `docs/audits/D20_simq_integration.md` (fixed by `TCK-20260630-SIMQ-WIRE-KERNEL`). The
  `InProcessQualityFeed` docstring's "G1 fix"/"G3 fix" references are about that older, unrelated pair of
  gaps — do not treat their being-already-fixed as evidence this ticket is already done, and do not edit
  that docstring as part of this ticket (it is accurate for what it describes).
- Any diff touching the `EventRecorder` construction or `.start()` guard site (`kernel.py:260-268`) is a
  strong signal an implementer has gone beyond G3's scope — the whole point of the fix is that those lines
  need zero changes.
- `worker.py`'s stream-name/broker-url line citation in ticket text is off-by-one (line 74, not 73, per
  investigation.md) — use `worker.py:72-76` (the full `BrokerQualityFeed(...)` call) as the anchor rather
  than a single line number.
- Step 3's run-dir fix is deliberately narrow (worker-local default consistency) and explicitly does not
  attempt to link the worker's run_id to the engine's `self._run_id` — that would require new cross-process
  coordination infrastructure and is out of this ticket's scope. Do not expand Step 3 into building such a
  channel.

## Deviations

All 9 steps were implemented exactly as specified; the items below are implementation-detail fill-ins the
plan left open rather than substantive departures.

- **Step 4, test 7** (`test_kernel_inprocess_mode_unaffected_by_g3_fix`): the plan's Verify text says to
  assert "all 10 pillar scorers present." `QualityHub` has no stored `scorers` list attribute — it only
  exposes `SCORER_REGISTRY: dict[str, list[PillarScorer]]` keyed by event type. The test asserts
  `len({id(s) for lst in hub.SCORER_REGISTRY.values() for s in lst}) == 10` instead of an attribute the
  class doesn't have.
- **Step 2/3 tests** (`tests/simulation_quality/test_worker.py`, new file): `QualityWorker.__init__` resolves
  `QUALITY_WEIGHTS_PATH`/`QUALITY_GRADE_PATH`/`QUALITY_DETECTION_PATH` and `QUALITY_RUN_DIR`/`QUALITY_STREAM_NAME`
  defaults as paths relative to the process cwd (via `ScoringWeights.load()` and `QualityPersistence(run_dir)`
  opening files directly, no repo-root search path). The run-dir default test needs cwd changed to `tmp_path`
  to avoid writing into the real repo's `data/runs/`, so it sets `QUALITY_WEIGHTS_PATH`/`QUALITY_GRADE_PATH`/
  `QUALITY_DETECTION_PATH` to absolute paths (computed via `os.path.abspath(...)` before the `chdir`) and uses
  `monkeypatch.chdir(tmp_path)`. The plan did not specify this mechanic since it predates the actual test
  authoring; not a scope or behavior deviation, just the concrete way "isolated, no repo pollution" (Testing
  Rule) was achieved.
- **Step 6 / Step 9, corrected during Architecture-Verify**: the plan's Step 5 Verify text already anticipated
  that live Redis might be unavailable ("if genuinely unavailable, document the skip explicitly"). No
  `redis-server` was reachable in the initial implementation sandbox, so
  `test_no_env_vars_set_broker_mode_producer_consumer_share_stream_name` was not executed to a passing state
  at Implement time, and `INFRA-317`'s `v2_evidence` initially disclosed this (3 of 4 cited tests ran). This
  disclosure turned out to be **incomplete, not just honest-but-partial**: Architecture-Verify independently
  forced `REDIS_AVAILABLE=1` against a real Docker Redis and found the test failed immediately on
  `event_category="action"` not being a valid `EventCategory` literal — a real defect unrelated to Redis
  availability that a "code review" pass had not caught. Fixing it (plus two further, independent latent
  bugs found the same way in the file's other pre-existing test — a wrong mock patch target and a
  mock behavior mismatched against the real API) let all 3 tests in the file pass against real Redis.
  `INFRA-317`'s `v2_evidence` was rewritten to describe this accurately. `INFRA-318` (G3, P0) has all 4 of
  its cited tests passing — none require live Redis, since the kernel's `.start()` guard is never reached in
  broker mode after the G3 fix.
- **Ticket Scope item 3, "Startup diagnosability," found missing at Verify (DOD_BLOCKED, not a routine
  deviation)**: neither investigation.md, this plan, nor the original Implementation Notes ever mentioned
  this scope bullet — it was silently dropped during Investigate/Plan and never implemented. `done-checker`
  caught this as a real gap, not a false positive (the ticket's own Scope section explicitly requires it).
  Fixed post-Verify, directly, without a full re-Investigate/re-Plan/re-Review cycle for this small, additive
  slice (consistent with how the two Architecture-Verify fix rounds above were already handled in this same
  ticket): `BrokerQualityFeed` gained an `events_consumed_count` counter (incremented in its consume
  callback); `QualityWorker.__init__` now logs the resolved `(broker_url, stream_name, consumer_group)`
  triple at INFO; `QualityWorker.run()` starts a one-shot `threading.Timer` (default 30s, configurable via
  `QUALITY_STALE_WARNING_SECONDS`) that logs a WARNING naming `SIM_STREAM_NAME`/`RPG_STREAM_NAME`/
  `SIM_REDIS_URL`/`RPG_REDIS_URL` if zero events were consumed by the time it fires, cancelled cleanly on
  shutdown. This does not implement the ticket's literal "stream does not exist" distinction (no such
  primitive exists in `RedisStreamConsumer` today) — the implemented signal is "zero events consumed after N
  seconds," which covers the same operator-visible symptom (a misconfigured/dead stream looks identical
  either way) using only existing primitives, and is stated as such in the code's own log message rather than
  overclaiming a check that wasn't built. 3 new tests added to `tests/simulation_quality/test_worker.py`.
