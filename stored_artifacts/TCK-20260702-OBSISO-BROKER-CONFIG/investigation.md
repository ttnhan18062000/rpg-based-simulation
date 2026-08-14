---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260702-OBSISO-BROKER-CONFIG
artifact_type: investigation
tags: [observability, simulation-quality, broker-mode, redis, configuration, kernel]
---

# Investigation — TCK-20260702-OBSISO-BROKER-CONFIG

## Current Behavior

### G1 — stream-name default mismatch (CONFIRMED, live)
- Producer default: `ObservabilityConfig.get_stream_name()` — `src/observability/config.py:336-338`.
  Resolves `SIM_STREAM_NAME` or `RPG_STREAM_NAME`, else `"simulation:events"`. Ticket cited
  336-338 — **exact match, no drift.**
- Producer wiring: `get_event_stream_adapter()` (`src/observability/stream/factory.py:16-39`)
  builds `RedisStreamAdapter(redis_url=ObservabilityConfig.get_redis_url(), stream_name=ObservabilityConfig.get_stream_name(), ...)` when `ObservabilityConfig.get_stream_backend() == "redis"`.
  This is the "single source of truth" surface the ticket wants SimQ consumers to route through;
  confirmed method names: `get_stream_backend()` (config.py:317-328), `get_redis_url()`
  (config.py:330-333), `get_stream_name()` (config.py:335-338).
- Consumer default #1: `BrokerQualityFeed.__init__` — `src/simulation_quality/feed.py:58-66`,
  `stream_name: str = "sim:events"` default at **line 61** (ticket cited 61 — exact match).
  Also independently defaulted again inside `build_feed_from_env()` at
  `feed.py:133`: `stream_name=os.environ.get("QUALITY_STREAM_NAME", "sim:events")` (ticket cited
  133 — exact match).
- Consumer default #2: `QualityWorker.__init__` — `src/simulation_quality/worker.py:72-76`,
  `stream_name=os.environ.get("QUALITY_STREAM_NAME", "sim:events")` at **line 74**, not line 73
  as the ticket cites (line 73 is the `broker_url=` line immediately above). **Minor drift: off
  by one line** — not caused by the sibling ticket (worker.py was untouched by
  TCK-20260702-OBSISO-TRACE-ASYNC); likely just an off-by-one in the original scoping pass.
- Net effect confirmed exactly as scoped: with no env vars set, producer writes to
  `simulation:events`, every consumer path (`BrokerQualityFeed` directly, `build_feed_from_env()`,
  and `QualityWorker`) reads from `sim:events`. Broker mode is silently dead out-of-box. **G1 is
  real and unfixed.**
- A **third** doc-level place documents the `sim:events` default and will need the same table
  update: `docs/simulation_quality/quality_scoring_contract.md:166` (§3.4 Dual Feed Mode), not
  just `docs/guides/simulation_quality.md` (which the ticket already names).

### G3 — kernel feed routing in broker mode (CONFIRMED, live, line numbers unchanged)
Full current wiring in `src/engine/kernel.py`, `Kernel.__init__`:
- `build_feed_from_env()` import + call: **lines 232-233** — identical to the ticket's citation
  (`kernel.py:232-233`) despite the sibling `TCK-20260702-OBSISO-TRACE-ASYNC` having just touched
  this file (that ticket's changes were to the decision-trace writer path, not the SimQ block —
  no shift here).
- Lines 227-258: if `obs_mode != ObservabilityMode.OFF` and `_feed = build_feed_from_env()` is not
  `None` (i.e. `QUALITY_SCORING_DISABLED != "1"`, **regardless of `QUALITY_FEED_MODE`**), the
  kernel:
  1. builds `ScoringWeights.load(...)`,
  2. builds **all 10 pillar scorers** via `build_all_scorers(_weights)`
     (`src/simulation_quality/scorers/__init__.py:10-25` — Agency, Cognition, Combat, Economy,
     Faction, Information, Narrative, Progression, Social, WorldDynamics),
  3. constructs a `QualityHub(scorers=..., weights=..., persistence=QualityPersistence(_q_run_dir), run_id=self._run_id)` **inside the engine process**,
  4. sets `_quality_fn = _hub.on_envelope`, `self._quality_hub = _hub`, `self._quality_feed = _feed`.
- Line 260-265: `EventRecorder(..., quality_fn=_quality_fn)` — wires the hub into the in-process
  drain worker regardless of feed mode.
- **Line 267-268**: `if self._quality_feed is not None and self._quality_hub is not None:
  self._quality_feed.start(self._quality_hub)`. When `QUALITY_FEED_MODE=broker`, `_feed` is a
  `BrokerQualityFeed` instance (from `build_feed_from_env()`, `feed.py:130-135`), so this line
  calls `BrokerQualityFeed.start(hub)` — which (per `feed.py:72-108`) connects a
  `RedisStreamConsumer` and spawns a **daemon thread named `"broker-quality-feed"`**
  (`feed.py:107`) inside the engine process, consuming Redis and calling `hub.on_envelope()` on
  the in-engine hub.
- **G3 is confirmed exactly as scoped, and worse in one respect not explicit in the ticket text**:
  in broker mode the engine doesn't just build "a QualityHub" — it builds and runs **all 10
  pillar scorers** in-engine (same `build_all_scorers()` call used for in-process mode), so
  broker-mode scoring runs fully in-engine (defeating R4/isolation) even though the point of
  broker mode is to keep that CPU work in the separate `QualityWorker` process (which itself only
  runs 2 of 10 scorers per G2, out of scope here but relevant context for the double-consumption
  risk below).
- Double-consumption risk confirmed structurally: both the in-engine `BrokerQualityFeed` (started
  by the kernel) and an external `QualityWorker`'s own `BrokerQualityFeed`
  (`worker.py:72-76`) resolve the same defaults (`QUALITY_BROKER_URL`, `QUALITY_STREAM_NAME`,
  `QUALITY_CONSUMER_GROUP="quality_scoring"`) — same consumer group, so Redis Streams
  `XREADGROUP` distributes (not duplicates) individual entries between the two consumers, but
  each entry is scored once by two *different* hub instances (in-engine 10-scorer hub, worker's
  2-scorer hub) — the two are architecturally guaranteed non-comparable and split the event
  stream unpredictably between them. Confirms `INFRA-235`'s dedup-by-`event_id` guard
  (`pillar_accumulator.py::PillarAccumulator.add`) does not fully solve this: dedup only
  protects a single hub against redelivery of the same event, not against two hubs each
  independently scoring a disjoint subset of the same run.
- Expected fix target stated by ticket Scope: in broker mode the engine must not construct a
  `QualityHub` or start any consumer thread — engine only publishes (already true; `EventRecorder`
  → `get_event_stream_adapter().publish()` is independent of the quality-scoring block). Kernel
  currently has no branch on feed mode at all — `_feed`'s concrete type (`InProcessQualityFeed` vs
  `BrokerQualityFeed`) is never inspected before deciding whether to build the hub. This needs to
  change; the `_quality_hub` property (`kernel.py:324-327`, "Read-only access to the QualityHub
  instance (None if SimQ is disabled)") docstring will also need updating since it will become
  "None if SimQ is disabled **or in broker mode**".

### Naming collision to disambiguate (risk of false "already fixed" belief)
`src/simulation_quality/feed.py`'s `InProcessQualityFeed` docstring
(`feed.py:32-38`) reads: *"quality_fn=hub.on_envelope is injected into EventRecorder's
QueueDrainWorker at kernel init time (G1 fix)... it does not create a second QueueDrainWorker
(G3 fix)."* This is **not** evidence that the current ticket's G1/G3 are fixed. These G1/G3
labels come from a *different, earlier, already-closed* gap analysis
(`docs/audits/D20_simq_integration.md`, closed by `TCK-20260630-SIMQ-WIRE-KERNEL`, see also the
duplicate/no-op `TCK-20260701-SIMQ-KERNEL-WIRE`): that G1 was "`EventRecorder`'s
`QueueDrainWorker` created without `quality_fn`" and that G3 was "`InProcessQualityFeed` creates a
second competing `QueueDrainWorker`". Both are real and fixed — confirmed by
`tests/simulation_quality/test_kernel_simq_integration.py::test_no_second_drain_worker` and
`::test_event_recorder_worker_has_quality_fn`, both passing against current code. They are
unrelated to *this* ticket's G1 (stream-name mismatch) and G3 (broker-mode in-engine hub/thread),
which come from the later `docs/plans/observability_process_isolation.md` (2026-07-02) gap
numbering and remain open. Anyone reading `feed.py`'s docstring in isolation could wrongly
conclude this ticket is already done — it is not.

## Mechanics / Engine Constraints
- `docs/engine/contracts/infrastructure_compat_contract.md` §3 "Infrastructure Isolation":
  "The core engine (`src.engine.kernel`) is guaranteed to be importable without external
  infrastructure... present." Verified still true today: `RedisStreamConsumer.connect()`
  (`src/observability/stream/consumer.py:29-46`) does a **lazy** `import redis` inside `connect()`
  wrapped in a broad `try/except Exception` — a missing `redis` package raises `ModuleNotFoundError`,
  caught, logged, `connect()` returns `False`, and `BrokerQualityFeed.start()`
  (`feed.py:81-88`) sets `health_status="unavailable"` and returns without raising. This
  graceful-degradation path must survive the G3 fix — whatever change stops the kernel from
  building a hub/starting the feed in broker mode must not remove or bypass this fallback for the
  case where broker mode is requested but the feed itself still needs to construct without error
  (e.g., the fix should skip *hub construction*, not prevent `build_feed_from_env()` or any
  publish-side code from being reachable when `redis` is absent).
- Note: the contract's §3 text is written in terms of RabbitMQ/Kafka/Postgres/generic brokers —
  it does not name Redis or SimQ specifically. The graceful-degradation behavior is real and
  consistent with the contract's *intent*, but the contract text itself would benefit from an
  explicit SimQ/Redis mention; flagged under Docs Requiring Update as an optional but on-scope
  clarification since this ticket is precisely the place that hardens broker-mode isolation.
- `docs/plans/observability_process_isolation.md` §1 R2 ("Loose coupling... kernel interacts only
  through injected callbacks/adapters and must run with them absent") and R4 ("Process
  separation... future: separate container") are the requirements G3 directly serves — the fix
  must leave R1-R3 unaffected for in-process mode (test_kernel_simq_integration.py must keep
  passing unchanged per the ticket's own AC).

## Docs Requiring Update
- `docs/guides/simulation_quality.md`: "Feed modes" section (lines 282-310) and "Environment
  variables" table (lines 90-106) currently list only `QUALITY_*` vars with no mention that
  `QUALITY_STREAM_NAME`/`QUALITY_BROKER_URL` will default onto `ObservabilityConfig`'s
  `SIM_STREAM_NAME`/`SIM_REDIS_URL`/`SIM_STREAM_BACKEND` once G1 is fixed; needs the unified
  config table (all env vars, defaults, owning process) and a broker-mode quickstart per ticket
  Scope item 4.
- `docs/simulation_quality/quality_scoring_contract.md`: §3.4 "Dual Feed Mode" (lines 147-176)
  documents the same stale `QUALITY_STREAM_NAME` default (`sim:events`, line 166) and, separately,
  contains a drift unrelated to this ticket's core scope but discovered here — line ~176 states
  "`InProcessQualityFeed.start()` registers a drain callback on `BoundedObservabilityQueue`",
  which no longer matches current code (`InProcessQualityFeed.start()` in `feed.py:43-44` now
  just stores the hub reference; the actual callback wiring happens in `kernel.py:254-264` via
  `EventRecorder(quality_fn=...)`, per the already-closed G1/G3 doc-history above). Flagging this
  contract-text staleness for the Plan phase to decide whether to fix in this ticket (adjacent,
  small) or spin a follow-up — do not silently fix without a scope decision.
- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers either G1 (stream-name single
  source of truth) or G3 (broker-mode kernel hub/thread suppression) — both need **new** P1
  entries (see Parity Ledger Overlap below), per ticket Scope item 5.
- `docs/engine/contracts/infrastructure_compat_contract.md`: optional — §3 could name
  Redis/SimQ explicitly alongside RabbitMQ/Kafka/Postgres now that this ticket hardens exactly
  that isolation boundary. Not strictly required (the general language already covers it), leaving
  this as a judgment call for Plan rather than asserting it as mandatory.

## Parity Ledger Overlap
- `INFRA-233` (verified, P1): `QUALITY_SCORING_DISABLED=1` short-circuit in
  `build_feed_from_env()`. Unaffected by this ticket's fix (the short-circuit happens before any
  mode branching) — no update needed, but the G3 fix must preserve this early-return exactly as
  is (do not reorder the disabled-check below any new mode-branch logic).
- `INFRA-239` (verified, P1): "`BrokerQualityFeed.start()` creates `RedisStreamConsumer`... skips
  gracefully... when Redis unreachable." Describes `feed.py`'s own behavior in isolation, which
  is not changing — no update needed for G1/G3 as scoped (stream-name default change is a
  parameter value, not a behavior change to this entry's claim; kernel-side suppression of *when*
  `.start()` is called is new kernel behavior, not new `BrokerQualityFeed` behavior).
  `test_path: tests/simulation_quality/test_feed.py::test_broker_feed_skips_gracefully_when_redis_unavailable`
  — confirmed this test file/function exists and matches current code.
- **No existing entry** covers G1 (stream-name single source of truth across producer/consumer)
  or G3 (kernel must not build a hub / start a broker consumer thread in broker mode) — both are
  net-new. Recommend two new P1 entries in `docs/parity_ledger/infrastructure.yaml` (next available
  ID after `INFRA-316`, i.e. `INFRA-317`/`INFRA-318` or whatever is current at implementation
  time — re-check the tail of the file before assigning, since other in-flight tickets may claim
  IDs first):
  - G1 entry: text asserting `BrokerQualityFeed`/`QualityWorker`/`build_feed_from_env()` stream
    name and broker URL resolve through `ObservabilityConfig.get_stream_name()`/`get_redis_url()`
    when `QUALITY_STREAM_NAME`/`QUALITY_BROKER_URL` are unset; `status: missing` until
    implemented, then `verified` with a `test_path` exercising the new integration test (AC #1).
  - G3 entry: text asserting the engine process constructs zero `QualityHub` instances and starts
    zero Redis consumer threads when `QUALITY_FEED_MODE=broker`; `status: missing` until
    implemented; `priority: P0` is arguable given this is the isolation guarantee R4 exists for —
    Plan should decide P0 vs P1 (P0 requires a passing `test_path` per repo rule; the ticket's AC
    #2 already demands exactly this assertion, so P0 is achievable at close).
- No P0 entries currently exist for this exact area, so no pre-existing P0 test_path obligation is
  inherited — but see above, a new P0 is a reasonable candidate for the G3 entry given AC #2's
  language ("zero SimQ scorer objects and zero Redis consumer threads").

## Prior Work
- `TCK-20260630-SIMQ-WIRE-KERNEL` (stored_artifacts present) — fixed the *original* G1 (quality_fn
  injection into `EventRecorder`'s drain worker) and G3 (removed `InProcessQualityFeed`'s
  competing `QueueDrainWorker`) from `docs/audits/D20_simq_integration.md`. This is the code path
  this ticket's G1/G3 fix must not regress — `test_kernel_simq_integration.py`'s four tests
  (`test_simq_hub_wired_into_kernel`, `test_no_second_drain_worker`,
  `test_event_recorder_worker_has_quality_fn`, `test_20_tick_run_produces_nonzero_tick_count`)
  are the regression guard and the ticket's AC #3 explicitly requires them to keep passing
  unchanged.
- `TCK-20260701-SIMQ-KERNEL-WIRE` — closed as a duplicate/no-op; created against the same stale
  D20 audit text before it was updated. No implementation. Useful only as confirmation that the
  "old" G1/G2/G3 numbering is fully resolved and this ticket's G1/G3 are a distinct, later problem.
- `TCK-20260520-SIM-OBS-M36` (Production Stream Adapter) — built `RedisStreamAdapter`/
  `RedisStreamConsumer` and the `SIM_STREAM_*`/`SIM_REDIS_URL` env vars this ticket must route
  SimQ's `QUALITY_*` defaults onto. No stream-name-parity work was in that ticket's scope (it only
  built the producer side), consistent with the gap this ticket closes.
- `TCK-20260702-OBSISO-TRACE-ASYNC` (stored_artifacts present, sibling ticket, just landed) —
  touched `src/observability/cognition/decision_trace_writer.py` and made async-write changes;
  confirmed via direct read that it did **not** touch the SimQ hub-construction block in
  `kernel.py:227-269`, so no line-number drift affects this ticket's citations there.
  `docs/plans/observability_process_isolation.md` G4 is marked RESOLVED by this ticket.
- `docs/audits/D20_simq_integration.md` — the original (now largely superseded/historical) audit;
  not re-read in full here since its G1-G3 findings are confirmed already closed by the tickets
  above and are a naming collision, not prior art for this ticket's actual scope.

## Risks and Open Questions
- **Open (blocking Plan, not answered here per instruction not to assume)**: "who writes
  `quality_scores.jsonl` into the run dir the engine owns?" Facts gathered, no decision made:
  - Engine's run dir convention: `ArtifactRepository(base_dir: str = "data/runs")`
    (`src/observability/reporting/artifact_repository.py:38`); `Kernel.__init__` builds
    `run_dir_str = os.path.join(self._artifact_repo.base_dir, self._run_id)`
    (`kernel.py:222-223`) — i.e. `data/runs/{run_id}/`.
  - `QualityWorker`'s `QUALITY_RUN_DIR` default is the **fixed literal**
    `"data/runs/quality_worker"` (`worker.py:65`) — not parameterized by `run_id` at all. Two
    engine runs with different `run_id`s would both have their broker-mode worker write into the
    *same* `data/runs/quality_worker/` directory by default, unless an operator explicitly sets
    `QUALITY_RUN_DIR`/`QUALITY_RUN_ID` per run.
  - This is a real, confirmed divergence from the engine's own run-dir convention, not a
    misunderstanding — Plan must decide: point `QUALITY_RUN_DIR` default at the engine's
    `data/runs/{run_id}` pattern (requires the worker to receive/derive `run_id`, which today only
    comes from `QUALITY_RUN_ID` env, default `"broker_worker"`, entirely decoupled from the
    engine's `run_id`), or keep it deliberately separate and document why. Flagging as blocking
    because the ticket's own Assumptions/Open Questions section defers this decision explicitly
    and it affects Scope item 4 (docs) and possibly the new parity entry text.
- Risk: the G3 fix must decide *how* to detect "broker mode" inside `Kernel.__init__` — today
  nothing inspects `_feed`'s type. The cleanest signal is `isinstance(_feed, BrokerQualityFeed)`
  (or a `feed.mode` property added to `QualityFeedAdapter`) rather than re-reading
  `QUALITY_FEED_MODE` from env a second time (which `build_feed_from_env()` already read once —
  re-reading independently risks skew if the two reads disagree, e.g. under test env-var
  monkeypatching mid-call). Recommend Plan specify inspecting the adapter instance, not the env
  var, to keep a single source of truth for mode resolution.
- Risk: `self._workers_started = 2 if (obs_mode != ObservabilityMode.OFF) else 0`
  (`kernel.py:306`, comment: "EventRecorder._worker + DecisionTraceWriter._worker") does not
  currently count any SimQ-broker consumer thread — so today's lifecycle-supervisor worker count
  is already implicitly correct for the *desired* G3 end-state (zero extra workers for SimQ in
  broker mode) but is currently **wrong** for the *actual* broken state (a live
  `"broker-quality-feed"` thread exists but isn't counted). Not a scope item to fix the counter
  now (it will become correct again once G3 is fixed to not start that thread) — but the
  implementer must not accidentally "fix" the counter instead of the actual bug.
- Risk: `worker.py`'s off-by-one line citation (73 vs 74) is trivial but should be corrected in
  ticket text/Plan citations rather than propagated.

## Anti-Drift Hazards
- Do not change `InProcessQualityFeed` behavior while fixing G1/G3 — it is unrelated (already
  fixed by the older G1/G3 wiring ticket) and `test_kernel_simq_integration.py`'s
  `test_no_second_drain_worker` / `test_event_recorder_worker_has_quality_fn` will catch any
  regression, but avoid touching that code path at all to keep the diff scoped.
- Do not rename or restructure `ObservabilityConfig.get_stream_name()`/`get_redis_url()` — the
  ticket wants SimQ to *route through* these, not fork or wrap them into a new abstraction; keep
  the producer-side methods as the single source of truth exactly as they exist today.
- Do not fix G2 (`QualityWorker` scoring only 2/10 pillars) — explicitly out of scope, covered by
  sibling ticket `TCK-20260702-OBSISO-WORKER-PARITY`. It is tempting to touch `worker.py`'s scorer
  list while already editing that file for the stream-name default; resist it.
- Do not add a benchmark or performance measurement for broker vs in-process overhead — that is
  `TCK-20260702-OBSISO-ISOLATION-PROOF` (G5), explicitly out of scope here.
- Do not silently "fix" the `quality_scoring_contract.md` §3.4 stale-doc-text drift found above
  (the "`InProcessQualityFeed.start()` registers a drain callback" claim) without a Plan-phase
  scope decision — it's adjacent, not squarely in G1/G3, and fixing it changes a different doc
  section than the one this ticket's Scope item 4 names.
- Preserve `QUALITY_SCORING_DISABLED=1` as the very first check in `build_feed_from_env()`
  (`feed.py:125-126`) — both AC #4 and `INFRA-233` depend on it short-circuiting before any new
  mode-routing logic this ticket adds.
