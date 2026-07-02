---
status: proposal
layer: observability
authority: P1
audience: agent
date: 2026-07-02
tags: [observability, simulation-quality, process-isolation, broker-mode, hot-path, decision-trace, epic-proposal]
---

# Observability & SimQ Process Isolation — Requirements, Current State, Gaps

Source proposal for the `obs-isolation` epic batch (`tickets/todos/obs-isolation/`). All claims below verified against code on 2026-07-02.

---

## 1. Requirements

External evaluation components (SimQ quality scoring, decision tracing, and any future intention-log machinery) must satisfy:

- **R1 — Performance isolation**: the engine main process (tick loop) must not be measurably affected by these components.
- **R2 — Loose coupling**: not tied into the engine; the kernel interacts only through injected callbacks/adapters and must run with them absent.
- **R3 — Toggleable**: can be turned fully on/off per run without code changes.
- **R4 — Process separation**: can run as a different process mode (future: separate container).

These requirements largely restate existing project law — `docs/architecture/observability_hot_path_safety_contract.md` (hot-path operation whitelist/blacklist, import isolation, backpressure modes) and `docs/engine/contracts/infrastructure_compat_contract.md` (kernel importable without external infrastructure). This proposal closes the gap between that law and the shipped implementation.

---

## 2. Current State (verified inventory)

| Component | Location | Status |
|---|---|---|
| Bounded event queue + async drain | `src/observability/queue.py` (`BoundedObservabilityQueue`, `QueueDrainWorker`) | Working; singleton guarantee + test sentinel (INFRA parity entries exist) |
| SimQ in-process consumption | `quality_fn=hub.on_envelope` injected into `QueueDrainWorker` at kernel init | Working (TCK-20260630-SIMQ-WIRE-KERNEL) |
| Backpressure / load-shedding | `EventRecorder` NORMAL→PRESSURE→DEGRADED→SURVIVAL modes (OBS-BACKPRESSURE, INFRA-199) | Working |
| On/off switches | `QUALITY_SCORING_DISABLED=1`, `QUALITY_FEED_MODE`, `ObservabilityMode.OFF` | Working (R3 satisfied) |
| **Stream producer** | `EventRecorder` → `get_event_stream_adapter().publish(event)` (`src/observability/event_recorder.py:147`) → `RedisStreamAdapter` (`src/observability/stream/adapters.py`): own bounded queue, daemon publisher thread, severity-based eviction, degraded mode without Redis | Working (TCK-20260520-SIM-OBS-M36). Env: `SIM_STREAM_BACKEND` / `SIM_REDIS_URL` / `SIM_STREAM_NAME`; `production` deployment profile defaults to `redis` |
| **Stream consumer** | `RedisStreamConsumer` (`src/observability/stream/consumer.py`): consumer-group read, reconstructs `SimulationEvent` from `payload` JSON | Working |
| **Broker feed** | `BrokerQualityFeed` (`src/simulation_quality/feed.py`): daemon consumer thread → `hub.on_envelope` | Working, graceful when Redis absent |
| **Standalone worker** | `python -m src.simulation_quality.worker` (`QualityWorker`): builds hub + broker feed, `/health` HTTP endpoint (`QUALITY_WORKER_PORT`, default 8082), SIGTERM/SIGINT shutdown, writes final report | **Exists but incomplete** (see G2) |
| Tests | `tests/simulation_quality/test_feed.py`, `test_broker_feed_integration.py`, `test_performance.py`, `test_kernel_simq_integration.py`; `tests/unit/observability/test_decision_trace.py` | Exist; no cross-mode grade-parity or engine-overhead benchmark |

**Conclusion:** R2 and R3 are met. R1 is met by contract for the queue path but violated by the decision-trace writer (G4) and unproven by measurement (G5). R4 is ~80% built; three concrete defects block it (G1–G3).

---

## 3. Gaps

### G1 — Stream-name default mismatch (broker mode silently dead out-of-box)
Producer default: `simulation:events` (`ObservabilityConfig.get_stream_name()`, env `SIM_STREAM_NAME`/`RPG_STREAM_NAME`).
Consumer defaults: `sim:events` (`BrokerQualityFeed` and `QualityWorker`, env `QUALITY_STREAM_NAME`).
With defaults, the worker consumes a stream nothing writes to. No shared constant, no startup cross-check.

### G2 — QualityWorker scores 2 of 10 pillars
`QualityWorker.__init__` constructs `scorers = [AgencyScorer(weights), CombatScorer(weights)]` only. The in-process kernel path wires all 10 pillar scorers. Broker-mode grades are silently non-comparable to in-process grades. No shared scorer-registry builder exists for both paths to use.

### G3 — Kernel feed routing in broker mode (verify + fix)
`Kernel` calls `build_feed_from_env()` (`src/engine/kernel.py:232`) and starts the feed with an in-engine hub. If `QUALITY_FEED_MODE=broker`, this appears to start a `BrokerQualityFeed` consumer thread *inside the engine process* — scoring would run in-engine anyway (defeating R4) and potentially double-consume alongside an external worker. Expected behavior: in broker mode the engine only publishes; hub + feed live in the worker process.

### G4 — DecisionTraceWriter hot-path contract violation
`DecisionTraceWriter.write_trace()` performs synchronous `file.write()` + `flush()` per entity per tick (`src/observability/cognition/decision_trace_writer.py:128-129`), called from the adventure phase (`src/domains/adventure/phase.py:20`). This is direct file IO inside a simulation phase — forbidden by hot-path contract §3. Shipped with E22, predating the contract's enforcement attention.
**Refactor constraints:** (a) `src/observability/live/entity_inspector.py:142` reads `get_latest_goal_scores()` live — the in-memory latest-scores cache must survive; (b) incremental tick-index writes provide crash recovery — completeness-on-close semantics must be preserved (`docs/observability/decision_trace_contract.md`).

### G5 — Isolation unproven; queue drops unguarded
No benchmark compares engine tick throughput with SimQ disabled / in-process / broker. In-process mode shares the GIL — "off the hot path" bounds tick latency but not CPU; broker mode is the true R1 guarantee and its benefit is unmeasured. Additionally, `BoundedObservabilityQueue` drops on overflow; a drop during a calibration run silently degrades SimQ grades — `make evaluate` / `tools/calibrate_simq.py` do not assert `dropped_count == 0`.

---

## 4. SimQ Interaction Constraints (for any future event-touching feature)

Recorded here so subsequent epics (intention-log extensions, pressure propagation, etc.) inherit them:

1. **Anchor invalidation**: SimQ grades are locked to the 25-anchor calibration corpus. Any feature that adds event types or changes entity behavior shifts pillar scores; recalibration (`tools/calibrate_simq.py`, `grade_anchors.json`) is a mandatory closing step (precedent: TCK-20260701-SIMQ-CALIBRATE-REFRESH).
2. **Behavior-feedback features need determinism design**: the intention-log *ring buffer* would let strategy read recent decisions — a decisions→trace→decisions loop. That makes it durable cognitive state under the Durable State Rule (typed model, replay-reproducible), not an observability add-on. It is, however, hot-path *compatible* (contract §2 whitelists bounded ring buffers).
3. **Shared per-tick budget**: metric recorder, cognition recorder, personality recorder, decision-trace writer, and SimQ all run per tick when observability is on; additions should be measured cumulatively (G5 benchmark is the baseline).
4. **Single stream, consistent drops**: SimQ and `simulation_events.jsonl` consume the same envelope stream via one drain worker — they can never diverge, but queue drops hit both (G5 guard).

---

## 5. Ticket Map

| Ticket | Covers | Tier |
|---|---|---|
| `TCK-20260702-OBSISO-EPIC` | Epic — tracks the batch | epic |
| `TCK-20260702-OBSISO-TRACE-ASYNC` | G4 | standard |
| `TCK-20260702-OBSISO-BROKER-CONFIG` | G1 + G3 | standard |
| `TCK-20260702-OBSISO-WORKER-PARITY` | G2 | standard |
| `TCK-20260702-OBSISO-ISOLATION-PROOF` | G5 | standard |

Out of scope for this epic: containerization artifacts (Dockerfile/compose — future once G1–G3 land), intention-log behavioral extensions (ring buffer, Chronicle surprise signal, social-memory annotation — remain ideas in `idea_intention_log_first_class.md`, constrained by §4), NATS/Kafka backends.
