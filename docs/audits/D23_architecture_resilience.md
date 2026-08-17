---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, engine, observability, testing]
---

# D23 — Architecture & Resilience Audit

## Audit Profile

| Axis | Value |
|---|---|
| **Subject** | rpg-based-simulation ("Deterministic Concurrent RPG Engine") |
| **Scope** | Correctness under failure, resource governance, workload prioritization, graceful degradation, durable recovery, distributed-system operability |
| **Method** | Direct source/doc inspection + three independent parallel investigations, cross-verified against implementation |
| **Posture** | Independent third-party review — no vendor process, no ticket workflow, findings stated as-is |
| **Audit date** | 2026-08-17 |
| **State** | `done` (audit complete; remediation tracked separately) |

**What this audit answers:** Does this multi-container system (FastAPI + Redis + RabbitMQ + Kafka +
anomaly worker + Prometheus/Grafana/Loki) stay correct and recoverable when a piece of it
degrades — not just "does the simulation compute the right numbers."

**Related dimensions:** D17 (Documentation Currency) — the phase-count contradiction this audit
independently re-discovered was already tracked under `TCK-20260817-FIX-PHASE-COUNT-CONTRADICTION`
before this audit ran; this audit adds two new pieces of evidence (`CLAUDE.md`'s "32-phase" claim,
`docs/guides/simulation.md`'s citation of a nonexistent `src/engine/authoritative_pipeline.py`).
D24 (Codebase Health & Architecture Observatory) — the companion audit run in the same session,
covering codebase-scale/churn/dependency-graph health rather than resilience/failure-mode analysis.

**Remediation tracking:** `docs/plans/architecture_resilience_remediation_roadmap.md`,
`TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`.

---

## A. Executive Summary

This is a genuine small distributed system, not a single-process simulation with a thin API wrapper. `docker-compose.yml` provisions eleven services: a FastAPI backend, Redis, RabbitMQ, Kafka+Zookeeper, an anomaly-detection worker, a frontend, Prometheus, Grafana, Loki+Promtail, and a watchdog. That framing matters because it changes what "correct" means here — the question isn't just "does the simulation compute the right numbers," it's "does this multi-container system stay correct and recoverable when a piece of it degrades."

**Overall quality: better than the surface complexity suggests, let down by unfinished edges.** The authoritative core — the deterministic tick engine — is architecturally sound: single-writer commit semantics enforced by immutable state objects, AST-checked architecture tests that make the read/write boundary a build-time guarantee rather than a convention, and a real tick-budget overload governor. The problems are concentrated at the *edges*: the observability/messaging layer, the API surface, and the documentation describing all of it.

**Major strengths:**
- Authoritative state mutation is structurally impossible outside the single apply path — `frozen=True` dataclasses plus AST-based architecture tests (`tests/architecture/test_phase_domain_permissions.py`, `test_api_read_model_guard.py`), not a code-review convention.
- The observability hot path is genuinely decoupled from the simulation hot path: bounded in-memory queue, non-blocking publish, severity-aware backpressure, graceful degrade-to-nothing if Redis disappears entirely.
- A real tick-budget overload governor exists (Emergency Throttling → DEGRADED) — this is the one place the system has a designed answer to "what happens under sustained overload."

**Major risks:**
- RabbitMQ and Kafka are fully provisioned, health-checked, and — for the anomaly worker — a hard startup dependency, while zero lines of application code use either. This is deployed operational surface with no functional purpose, and it can take down a real subsystem for no reason.
- `/health` is a hardcoded `{"status": "ok"}` with no relationship to whether the engine is actually alive, and the one system designed to notice that is documented as `Status: Proposed` (not built) in one place while being referenced elsewhere as if operative.
- The Redis Stream consumer has no working failure differentiation: malformed payloads, transient errors, and permanent errors are all ACK'd and discarded identically, with no DLQ — silent, invisible data loss on the observability path.
- Three different documents (a guide, an engine contract, and the root process file) describe the authoritative pipeline's phase count differently (6, 7, and 32), and one cites a source file that does not exist.

**Top 5 priorities**, in order: (1) decide the fate of the unused RabbitMQ/Kafka infrastructure — remove it or stop letting it block startup; (2) make `/health` reflect actual engine liveness; (3) fix the stream consumer's failure handling (differentiate + add a DLQ); (4) reconcile the conflicting pipeline-phase documentation; (5) add HTTP-layer admission control before any exposure beyond a trusted network.

None of this requires a rewrite. Every fix below is additive or subtractive to a single component, not a structural change.

---

## B. Current Architecture

**System map** (from `docker-compose.yml`, confirmed against code):

```
frontend  --HTTP/WS-->  backend (FastAPI, src/api/server.py)
                              |
                        V2EngineManager (src/api/engine_manager.py)
                              |  dedicated background thread "v2-engine-loop"
                        Kernel.tick_once()  [src/engine/phases.py, pipeline.py, pipeline_phases/]
                              |
                        AuthoritativeState (frozen dataclasses, single writer: RESOLUTION phase)

backend --publish(async, non-blocking)--> RedisStreamAdapter --XADD--> Redis Stream "simulation:events"
                                                                              |
                                                                    ai_worker consumes via
                                                                    RedisStreamConsumer (consumer group)
                                                                    --> anomaly rules, alerts

prometheus --scrape--> backend:/metrics
grafana --query--> prometheus
promtail --tail--> container stdout --> loki
watchdog --poll HTTP--> backend:/health, backend:/metrics; --query HTTP--> loki

rabbitmq, kafka+zookeeper: provisioned, health-checked, wired into env vars —
   NOT imported or called by any application code (confirmed repo-wide grep for
   `import pika` / `confluent_kafka`: zero matches)
```

**Confirmed** — entry points: `src/cli/entry.py` for batch/offline runs, `src/api/server.py` → `V2EngineManager` for live/API-driven runs. `V2EngineManager._run_loop` (`src/api/engine_manager.py:259-287`) calls `self._kernel.tick_once()` serially inside one dedicated `threading.Thread(name="v2-engine-loop", daemon=True)` (`engine_manager.py:229`). The manager's public surface otherwise is read-only projection (`get_state`, `get_full_snapshot`, `get_entities_paged`, `get_entity`, `get_entity_timeline_events` — `engine_manager.py:176-217`) plus lifecycle control (start/stop/pause/resume/step).

**Confirmed** — the API is a read/control-plane, not a mutation surface. No route grants external callers a path to inject or mutate world state, and this is *structurally* enforced: `tests/architecture/test_api_read_model_guard.py` forbids `src/api/routes`, `src/api/ws`, and `server.py` from importing `AuthoritativeState`/`EntityState` outside `TYPE_CHECKING`.

**Confirmed doc/code divergence (flagging per the review's evidence-verification mandate — do not assume documentation is correct):**
- `src/engine/phases.py:13-21` defines a **7-phase** `TickPhase` enum: INIT, SCHEDULING, COLLECTION, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE. `docs/engine/kernel.md` matches this.
- `docs/guides/simulation.md:19-26` describes a *different* **6-phase** loop (Init → Governance → Scheduling → Packetization → Resolution → Persistence) and cites `src/engine/authoritative_pipeline.py` as "the 17-phase mutation sequence" — **that file does not exist.** The real implementation is `src/engine/pipeline.py` + `src/engine/pipeline_phases/` (16 phase modules, not 17).
- The root `CLAUDE.md` separately describes a "32-phase refinement sequence" for the same subsystem.

Three sources, three different numbers, one citing a nonexistent file. `docs/guides/simulation.md` is stale relative to both the code and `kernel.md`.

---

## C. System Invariants

| Invariant | Enforcement | Strength |
|---|---|---|
| Authoritative mutation occurs only within `ApplyPath.apply_generation` | `AuthoritativeState` and components are `frozen=True` dataclasses (`docs/core/state.md:12`) — direct mutation raises `FrozenInstanceError` at the language level | **Structural** — Confirmed |
| Only RESOLUTION phase may write `entity`/`world` domains | `src/engine/phase_domain_permissions.py` declares per-phase read/write/emit permissions; enforced by `tests/architecture/test_phase_domain_permissions.py` (executable guard) | **Structural** — Confirmed |
| No field-level mutation of an existing entity during a read-only phase | Tier 2 SHA-256 fingerprint check | **Mode-dependent — Confirmed weakness.** Tier 1 (always-on) only checks entity count and tick number. The fingerprint check that would actually catch a subtle off-path field mutation is gated behind `audit_mode=True` (`kernel.md:36-44`). In a default production run this class of bug is invisible. |
| Determinism (bit-identical replay via canonical hash) | Canonical SHA-256 hash comparison | **Mode-dependent — Confirmed weakness.** Skipped entirely in `DEGRADED` mode, absent in `SURVIVAL` mode (`kernel.md:100-109`). The strongest correctness proof is unavailable exactly when the system is under the load most likely to produce a subtle bug — this is precisely the "invariant depends on a timing/mode assumption rather than an explicit guarantee" pattern the review framework asks to flag. |
| Per-tick atomicity — a tick's domain updates apply together or not at all | "All updates within a domain are applied together or not at all" (`docs/engine/authoritative_apply_contract.md:27`) | **Confirmed**, structurally consistent with the frozen-state/single-apply-path design. |

**No literal analog exists** in this repo for the framework's payment/inventory-as-real-money examples. The closest Tier-0 "must never double-apply" invariant is **double-mutation of `AuthoritativeState` outside the single `apply_generation` call site** — and unlike a typical distributed system, it's enforced by language-level immutability plus AST-checked tests, not by a database unique constraint or an idempotency key (there is no external database of record for authoritative state; persistence is periodic checkpoint/replay of in-process typed state). In-game economy (gold/items) is governed separately by the Mechanics Bible's atomic-conservation rules — a gameplay-correctness concern, not examined further in this audit; whether negative-gold is structurally prevented vs. only test-covered is **unable to verify** from this pass and worth a follow-up look if that matters to you.

---

## D. Failure Model

**Confirmed** — a real exception taxonomy exists: 40+ custom exception classes (`KernelContractError` — `src/core/contracts.py:26`; `HardLawViolationError` — `src/observability/hard_law_monitor.py:27`; `HashScheduleViolation` — `src/engine/checkpoint.py:29`; `DirtySetLeakError` — `src/core/dirty.py:10`; `ProtocolViolationError` — `src/core/protocol_validator.py:5`; etc.).

**Confirmed, and a real tension** — broad `except Exception:` / bare `except:` occurs **481 times** across `src/` (e.g. `src/world/environment.py:88`, a bare `except: pass`). A taxonomy this granular existing alongside catch-all density this high suggests the taxonomy is under-exploited by callers — most failures are absorbed generically rather than matched to a specific type, category, or retry decision. This is a maintainability/observability erosion risk, not an acute one; it does not warrant a blanket "add better error handling" pass (that would cut against this repo's own stated preference for minimal, targeted change) — it warrants a targeted look at the highest-consequence sites (state mutation, persistence, replay).

**The one real retry/backoff implementation in the entire codebase:** `WebhookAlertSink` (`src/observability/alerts/sinks.py:39-92`). Bounded (`max_retries=3`), isolated in a dedicated 2-thread executor so it can't block the sim loop — a real bulkhead. But the backoff is linear (`time.sleep(0.5 * attempt)`) despite an in-code comment claiming "exponential backoff" (line 87) — a small but real doc/code mismatch. No jitter. No circuit breaker — a permanently-dead webhook endpoint receives the full retry sequence on every single alert, forever. `grep -r "circuit_breaker\|CircuitBreaker" src/` returns nothing anywhere in the codebase.

**Observability failure containment is a genuine strength.** `src/observability/anomaly/worker.py` implements an explicit degraded-state model (`WorkerStatus.status`: `PENDING|RUNNING|COMPLETED|FAILED|DEGRADED|STOPPED`, line 39) with heartbeats and stream-lag tracking. The main loop (`_run_loop`, lines 244-289) catches per-iteration exceptions, logs once, and routes an alert — itself wrapped in its own try/except (line 279-280: `except Exception: pass  # Never let alert routing break the worker loop`) so a broken alert path can never cascade into a broken worker. Rule evaluation is isolated per-rule too. `kernel.py` mirrors this pattern internally: dozens of `except Exception: logger.exception(...)` wrappers around metrics extraction, alert routing, and listener notification inside `tick_once` (e.g. `kernel.py:452-462, 481-484, 610-611`) mean a peripheral/observability failure structurally cannot abort a tick. Nineteen files reference `PARTIAL_SUCCESS`/`DEGRADED`/`PENDING`-style states — degradation is modeled as durable state in multiple places, not just a log line.

**Confirmed, no differentiation, no DLQ.** `src/observability/stream/consumer.py:79-102` (verified directly):

```python
except Exception as ex:
    logger.error(f"Error processing stream event {msg_id}: {ex}")
    # Acknowledge malformed/bad records to prevent head-of-line blocking on poison pills
    try:
        self.client.xack(self.stream_name, self.group_name, msg_id)
    except Exception:
        pass
```

A malformed payload and a transient handler failure (e.g. a downstream call timing out) are handled identically — ACK'd and discarded. There is no dead-letter stream, no retry budget, no distinction between "this will never parse" and "this failed once and might succeed on retry." This is the *inverse* of the classic "poison message retries forever" smell: here, anything that fails even once vanishes permanently after exactly one attempt. Separately, if the handler succeeds but the process dies before the `xack()` call (between the two lines), the message sits in the consumer group's PEL (pending-entries list) and is never reclaimed — no `XCLAIM`/`XPENDING` logic exists — so it's also never redelivered. Net effect: **no delivery guarantee in either direction.** Blast radius is bounded — this stream is downstream of, not part of, the authoritative gameplay pipeline (Tier 3, observability/anomaly-detection only) — but it is real, silent, and currently invisible (a single `logger.error` line is the only trace).

**Confirmed — a designed-but-unbuilt watchdog, referenced elsewhere as if operative.** `docs/architecture/simulation_watchdog.md` header states `## Status: Proposed`, and describes an implementation path (`src/utils/watchdog.py`) that does not match reality. The actual, running artifact is `src/observability/watchdog.py` (`SimulationWatchdog`) — poll-based (`POLL_INTERVAL=10s`), checking `/health` (see below) and `/metrics`' `sim_current_tick` for stalls, with "3 consecutive stalled/failed cycles → `logger.critical(...)`" (`watchdog.py:106-108`) as its only escalation. No PagerDuty/Discord dispatch is implemented despite the doc describing it as able to "trigger external alerts" — it only logs. **Confirmed, verified directly:** `/health` (`src/api/server.py:126-128`) is:

```python
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    return {"status": "ok", "version": "v2", "timestamp": time.time()}
```

This never checks whether `V2EngineManager`'s background thread is alive, ticking, or has crashed — it is a liveness stub, not a readiness check. If the engine thread dies while the FastAPI process stays up, `/health` continues reporting `ok`. The only real signal is the `/metrics` tick-stall detector, which — after three ~10s cycles — writes one log line. There is no automatic restart or remediation anywhere in this path (`docker-compose.yml:175-189` uses a plain `restart: unless-stopped`, which restarts the *container*, not anything engine-aware).

---

## E. Resource Model

**Confirmed — the tick loop is single-threaded and this does not conflict with the concurrency actually present elsewhere.** Determinism is scoped to one dedicated thread's serialized ticks, not the whole process:

- FastAPI request handling (async, its own event loop) reads engine state behind `threading.Lock`/`RLock` guards (`_state_lock` — `engine_manager.py:39`; `read_model_cache.py:40`) — a reader/writer split, not shared mutation.
- `WorkerManager` (`src/engine/worker_manager.py:50`) uses `ThreadPoolExecutor`/`ProcessPoolExecutor`, but only inside the kernel's COLLECTION phase, operating over immutable snapshots and feeding into a single serialized RESOLUTION commit ("deterministic order... bit-identical resolution regardless of worker execution order" — `docs/engine/kernel.md`). This is intra-tick parallelism, not inter-tick — no tension with the determinism claim.
- `RedisStreamAdapter` runs its own daemon publisher thread (`adapters.py:152-163`); `WebhookAlertSink` runs a dedicated 2-thread executor. Both are side-channel I/O, isolated from the mutation path.

**Confirmed — real admission control exists, but only for the intra-tick worker pool.** `WorkerManager.__init__(max_workers, max_queue_depth=100, use_processes)` (`worker_manager.py:56`) implements a bounded pool, a `threading.Semaphore(effective_cap)` throttle (line 106), and an explicit fallback: once `_inflight_count >= max_queue_depth`, work executes synchronously on the caller's thread instead of queueing further (lines 118-124). This is a real bulkhead with graceful degradation, not aspirational.

**Confirmed — no equivalent exists at the HTTP layer.** `src/api/server.py` registers only `CORSMiddleware` (`allow_origins=["*"]`, `allow_credentials=True` — this specific combination is spec-invalid per the CORS specification and signals unreviewed middleware config even though browsers will reject the actual credentialed-wildcard case) and `GZipMiddleware` (`server.py:73-80`). No rate limiting, no authentication, no per-client admission control on any REST endpoint.

**Confirmed — the observability hot path is deliberately, correctly isolated, and matches its own written contract.** `docs/architecture/observability_hot_path_safety_contract.md` explicitly forbids synchronous downstream writes (§3: "Direct relational/NoSQL database inserts (e.g., SQL, ClickHouse, Redis)... in the hot path") and mandates graceful queue-drop over blocking (§4.2). The code matches: `RedisStreamAdapter.publish()` (`adapters.py:190`) only appends to an in-memory `collections.deque` under lock and returns immediately; a separate daemon thread drains it via `XADD ... maxlen=max_queue_size, approximate=True`. Backpressure is severity-aware: when full, DEBUG/INFO events are dropped first; WARNING+ events evict an existing DEBUG/INFO entry rather than being dropped themselves. `dropped_count`/`backpressure_active`/`last_error` are tracked and exposed via `.health()`. Redis connection failures are caught and logged as degraded mode, never raised (`adapters.py:143-149`) — **confirmed directly, not inferred: the engine can run fully with Redis unavailable.**

**Inferred, not fully verified — hardware-class budgets.** `docs/engine/performance_contract.md` §3.1 documents Class A/B/C benchmarking tiers; code references exist (`src/config/profiles.py`, `src/config/optimization_profiles.py`, `src/perf/profiles.py`, `src/certification/models.py`) suggesting these feed a real `RuntimeProfile`. Whether class selection enforces a hard runtime ceiling, versus being an operator-supplied config value with no enforcement, was **not fully traced** in this pass. The tick-level enforcement that *is* confirmed is budget-based rather than class-based: "Emergency Throttling" — tick duration exceeds 2x average or a hard cap → Governor transitions to DEGRADED, drops remaining work, logs a warning (`kernel.md`, consistent with `PhaseBudgetGovernor` in `performance_contract.md` §7). This is a real, wired overload response, not documentation-only.

**Confirmed — declared-but-dead distributed infrastructure, and it's on a real critical path.** `pyproject.toml:18-19` lists `pika>=1.3.2` and `confluent-kafka>=2.6.0` as core (non-optional, non-dev) dependencies. `docker-compose.yml` provisions `rabbitmq` (with a `rabbitmq-diagnostics ping` healthcheck) and `kafka`+`zookeeper` as full services; `backend` and `ai_worker` both receive `RABBITMQ_URL`/`KAFKA_URL` environment variables. A repo-wide grep (not scoped to `src/` — the whole tree) for `import pika` or `confluent_kafka` returns **zero results**. The actual event pipeline is Redis Streams only. Worse than simple dead weight: `ai_worker` declares `depends_on: rabbitmq: condition: service_healthy` (`docker-compose.yml:70-71`) — **the anomaly-detection worker's container will refuse to start if RabbitMQ fails its healthcheck, despite never sending it a single byte.** This is two extra failure domains, two extra credential surfaces, two extra healthchecks, and one real hard startup dependency, coupled into the system for zero functional return.

---

## F. Distributed Workflow Analysis

There are two genuinely distinct multi-step workflows in this repository, and they should not be conflated:

**(1) The simulation engine's own tick pipeline (the real, production-facing workflow).** Per-domain, per-tick atomicity is confirmed structurally (`authoritative_apply_contract.md:27`, backed by the frozen-state design). Crash handling is implemented, not aspirational: `src/cli/entry.py`'s `finally` block flushes the `EventRecorder`, drains the `ReplayManager`, and marks the run manifest `FAILED`. Net effect of a mid-tick crash: only the in-flight tick's proposals are lost; the last **committed** tick (post-Advancement phase) remains durable and uncorrupted. Recovery is "start a new run from the last good checkpoint," not true mid-tick resume — a reasonable, explicit design choice given the atomicity guarantee, not a gap.

**(2) The repository's own AI-agent development workflow** (the implement-ticket pipeline: Scope → Investigate → Plan → Implement → Test → Parity → Verify → Finalize, tracked in `agent-monitoring/runs.jsonl`/`events.jsonl`). This is meta/dev-tooling, not the simulated domain, but it is itself a multi-step workflow with partial-failure semantics worth noting on its own terms: sampled `runs.jsonl` entries carry only a **terminal** `final_status` plus start/end timestamps — no in-progress row exists at any point. **This means a run that crashes mid-pipeline may leave no `runs.jsonl` entry at all** — the log by itself cannot distinguish "never started" from "started and died." The actual detector for a stuck workflow is a separate, lighter mechanism: `make agent-monitoring-epic-staleness`, which checks ticket-file idle time rather than run-record state — and it is, as it happens, actively firing during this very session for `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`. It is a real, working detector, just an indirect one (file-mtime-based) rather than a durable state machine with an explicit PENDING/RUNNING state.

---

## G. Overload Analysis

- **Retry amplification:** Contained. The only real retry chain in the system (`WebhookAlertSink`, 3 bounded attempts) is isolated in its own 2-thread executor and cannot cascade into or block the tick loop. No evidence of A→B→C retry chains anywhere else — there simply aren't enough network hops in the confirmed call graph for that shape to exist yet.
- **Queue buildup:** Bounded by design at the two points that matter — `WorkerManager`'s `max_queue_depth` (falls back to synchronous execution) and `RedisStreamAdapter`'s deque (drops/evicts by severity). Redis Streams' own `maxlen`-based trimming acts as a crude, silent DLQ-equivalent (old events age out, not explicitly dead-lettered).
- **Cascading failure:** The design goal — observability/telemetry failure cannot take down the tick loop — is achieved and verified in two independent ways (thread isolation + exception-boundary wrapping in `kernel.py`). The one place this protection does *not* extend is the RabbitMQ healthcheck dependency: a RabbitMQ failure genuinely can take down `ai_worker`, an otherwise-unrelated subsystem, purely through a deploy-time dependency that has no functional justification.
- **Dependency saturation / reconnect storm:** On a sustained Redis outage, `RedisStreamConsumer.read_and_process` (`consumer.py:104-108`) sets `_connected = False` and returns 0; the outer loop retries roughly every ~100ms with no backoff. Small blast radius (Tier 3 only), but it is the same *shape* as a retry storm against a downstream dependency, just against Redis instead of a payment processor.
- **Starvation:** Not observed as an acute risk given the confirmed thread/queue isolation. The clearer starvation-shaped risk is the RabbitMQ dependency above — a low-value, zero-traffic dependency capable of starving a real subsystem of the ability to even start.
- **Load shedding:** Present and working at the observability layer (severity-aware drop). Absent entirely at the HTTP layer (no rate limiting, no admission control on REST).
- **Graceful degradation:** The clearest and best-documented instance is `observability_hot_path_safety_contract.md`'s four explicit modes — NORMAL / PRESSURE / DEGRADED / SURVIVAL — driven by queue-fill ratio, with SURVIVAL specified as "zero IO, no locks, no allocations." This is a real, wired instance of exactly the operating-mode model the review framework recommends considering — worth highlighting as something to *extend* to the HTTP layer (which currently has no equivalent mode vocabulary at all) rather than invent from scratch.

---

## H. Observability and Operability

Can an operator answer the framework's diagnostic questions today?

| Question | Answer |
|---|---|
| Is the system degraded? | Partially. `WorkerStatus` and the hot-path-safety modes surface this for the observability subsystem. The engine/API layer has no equivalent explicit mode signal beyond `/metrics`. |
| Is a workflow stuck? | For the tick loop: only via `/metrics`' `sim_current_tick` stall detection (10s poll, 3-cycle threshold, log-only escalation). For the agent-dev-workflow: only via epic-staleness file-mtime checks, not `runs.jsonl` itself. |
| Which dependency is responsible for a failure? | Weak. 481 broad-except sites and a single `logger.error(f"...{ex}")` pattern in the stream consumer mean root cause is frequently reduced to a string in a log line rather than a typed, queryable failure category. |
| Are events accumulating / are compensations failing? | No metric distinguishes malformed-payload drops from transient-failure drops from orphaned-PEL messages in the stream consumer — all three currently look identical: one `logger.error` line each. |
| How much capacity remains? | For the tick loop: yes, via the Emergency Throttling/Governor state and `PhaseBudgetGovernor` metrics. For the HTTP layer: no equivalent exists. |

Positive: structured logs, `python-json-logger`, Prometheus + Grafana + Loki/Promtail are real, wired infrastructure, and the failure-containment logging pattern in `anomaly/worker.py` (log once, don't duplicate at every layer) is a genuinely good pattern already present. The gap is not "no observability" — it's that the observability layer's own internal failures (the stream consumer's silent drops) are under-instrumented relative to the sophistication of the rest of the stack.

---

## I. Risk Register

| # | Finding | Severity | Likelihood | Trigger | Evidence | Mitigation |
|---|---|---|---|---|---|---|
| R1 | Unused RabbitMQ/Kafka infra hard-blocks `ai_worker` startup via `depends_on: rabbitmq: condition: service_healthy`, despite zero code using either broker | **Critical/High** | Medium | RabbitMQ container fails its healthcheck (resource pressure, config drift, disk) | `docker-compose.yml:70-71`; repo-wide grep for `pika`/`confluent_kafka` = 0 matches | Remove `rabbitmq`, `kafka`, `zookeeper` services and the `pika`/`confluent-kafka` deps, or if there's real future intent, un-couple `ai_worker`'s startup from a broker it doesn't use and track adoption as an explicit, separate item |
| R2 | `/health` is a hardcoded stub, not an engine-liveness check; the one system meant to notice (`SimulationWatchdog`) only logs, never remediates or alerts externally | High | Medium | Engine background thread crashes/deadlocks while the FastAPI process stays up | `src/api/server.py:126-128`; `src/observability/watchdog.py:106-108`; `docs/architecture/simulation_watchdog.md` (`Status: Proposed`) | Make `/health` check engine-thread liveness + last-tick recency; wire at least one real external alert channel, or explicitly document watchdog as log-only until built |
| R3 | Redis Stream consumer ACKs malformed payloads and transient handler failures identically; no DLQ; orphaned pre-ACK messages never reclaimed | High | Medium-High | Any transient hiccup in a stream-event handler; a process death between handler success and ACK | `src/observability/stream/consumer.py:79-102` (verified directly) | Separate malformed-payload handling (ack+drop is fine) from handler-exception handling (bounded nack/retry + literal DLQ stream); add `XCLAIM`/`XPENDING`-based PEL reclaim; add backoff+jitter to the ~100ms reconnect loop |
| R4 | Three documents disagree on the authoritative pipeline's phase count (6 / 7 / 32); one cites a source file that does not exist; the watchdog doc describes an implementation path that doesn't match reality and is marked Proposed while referenced elsewhere as operative | Medium-High | High (already observed) | Any engineer or agent reasoning from the wrong doc — including this repo's own AI-agent workflow, which treats these docs as authoritative | `docs/guides/simulation.md:19-26` vs `src/engine/phases.py:13-21` vs root `CLAUDE.md`; `docs/architecture/simulation_watchdog.md` header | Reconcile phase-count language against `TickPhase`; correct file-path references; mark watchdog status accurately everywhere it's cited, or finish building it |
| R5 | Determinism/mutation-guard proof is mode-dependent: Tier-2 fingerprint check gated behind `audit_mode`; canonical hash skipped in DEGRADED, absent in SURVIVAL | Medium | Low-Medium | A subtle off-path mutation bug occurring during a default (non-audit) run, especially one that also triggers DEGRADED/SURVIVAL | `kernel.md:36-44, 100-109` | Consider a cheap always-on partial/sampled fingerprint instead of all-or-nothing `audit_mode` gating; at minimum, flag DEGRADED/SURVIVAL run outputs as "reduced verification" |
| R6 | No auth or rate limiting on the FastAPI layer; CORS configured with `allow_origins=["*"]` + `allow_credentials=True` (spec-invalid combination) | Medium (deployment-dependent) | Depends entirely on exposure | Any non-local/internet-facing deployment | `src/api/server.py:73-80` | Add auth middleware before any exposure beyond a trusted network; fix the CORS config regardless — it signals unreviewed middleware setup even though it's inert today given the read-only route surface |
| R7 | Sole retry/backoff implementation (`WebhookAlertSink`) is linear despite a comment claiming exponential, has no jitter, no circuit breaker | Low-Medium | Medium | A webhook endpoint goes permanently dead | `src/observability/alerts/sinks.py:39-92` | Add a simple circuit breaker (open after N consecutive failures, half-open retry); fix the comment or implement real exponential backoff+jitter |
| R8 | 481 broad `except Exception`/bare `except` sites coexist with a 40+-class exception taxonomy that's largely unused by callers | Low (individually), Medium (aggregate erosion) | Ongoing | N/A — steady-state maintainability risk | e.g. `src/world/environment.py:88` | Targeted review of the highest-consequence sites (mutation, persistence, replay) only — not a blanket sweep |

---

## J. Recommended Architecture Improvements

**P0 — correctness / catastrophic failure risk**
- Remove the RabbitMQ hard-dependency from `ai_worker`'s startup (R1). This is the one finding in this audit that can cause an outage of a real subsystem for a reason unrelated to that subsystem's actual function.
- Fix `/health` to reflect real engine liveness (R2).

**P1 — resilience / operational risk**
- Redis Stream consumer failure differentiation + DLQ + reconnect backoff (R3).
- Reconcile the three conflicting pipeline-phase docs and the watchdog status/path mismatch (R4).
- HTTP-layer auth, before any deployment beyond a trusted network (R6, conditional on deployment plans).

**P2 — scalability / maintainability**
- Cheap always-on partial determinism fingerprint to shrink the audit-mode-only coverage gap (R5).
- Targeted review of the highest-risk broad-except sites (R8, scoped, not blanket).

**P3 — optimization / future scale**
- Circuit breaker + real exponential backoff+jitter for `WebhookAlertSink` (R7).
- Decide the actual fate of RabbitMQ/Kafka: either commit to a real use case and build it, or delete the dependencies, services, and env vars entirely. Do not leave them provisioned-but-unused indefinitely — every day they exist is attack surface, credential surface, and operational confusion with zero return.

**Explicitly not recommended:** introducing a workflow engine (Temporal-style), Sagas, or distributed transactions anywhere in this codebase. The confirmed architecture (single-writer commit + frozen state + per-tick atomicity) already achieves the correctness properties those tools exist to provide, at a fraction of the operational cost. The one genuine complexity-without-payoff instance already present in this repo is RabbitMQ/Kafka — which argues *against* adding more infrastructure speculatively, not for it.

---

## K. Failure-Action Matrix

| Failure | Criticality | Retry | Fallback | Compensation | Event | Alert | Final State |
|---|---|---|---|---|---|---|---|
| Malformed stream event | Low | No (by design, correct) | No | No | Log only | No | Dropped |
| Stream handler transient failure | Medium | **None (bug — should be bounded retry)** | No | No | Log only | No | **Dropped (should be: DLQ)** |
| Process dies between handler success and XACK | Medium | **None (bug — should be PEL reclaim)** | No | No | None | No | **Orphaned in PEL forever (should be: reclaimed via XCLAIM)** |
| Redis fully unavailable (extended) | Low (Tier 3 only) | Yes, ~100ms loop, **no backoff (should add jitter+backoff)** | Graceful (engine unaffected) | No | `dropped_count` metric | No | Degraded mode, engine unaffected |
| RabbitMQ healthcheck fails | **High (misapplied)** | No | **None — hard startup block (should be: no dependency at all)** | No | None | No | `ai_worker` fails to start |
| Engine background thread crash/deadlock | Critical | No | No | No | None visible | **Log-only after 30s (should be: real alert + accurate `/health`)** | Silent stall |
| Tick exceeds time budget (2x avg or hard cap) | Medium | No (by design) | Governor → DEGRADED, drop remaining work | N/A | Warning log | Threshold-based (governor state) | Degraded, continues |
| Webhook alert endpoint down | Low | Bounded (3, linear, no jitter) | No | No | N/A | N/A (this *is* the alert path) | Delayed/dropped alert |
| FastAPI request storm | Medium (deployment-dependent) | N/A | **None (should be: rate limiting)** | N/A | None | No | Resource contention on read locks/workers |

---

## L. Resource Governance Proposal

The system already has real, working resource governance in two places — `WorkerManager`'s bulkhead/semaphore/queue-depth fallback, and `RedisStreamAdapter`'s bounded-queue/severity-eviction backpressure — plus a kernel-level tick-budget governor with an explicit DEGRADED transition. **The gap is not "no resource governance exists," it's that governance stops at the process boundary between the engine and the HTTP layer.**

The `observability_hot_path_safety_contract.md` already defines a four-mode vocabulary — NORMAL / PRESSURE / DEGRADED / SURVIVAL — for the observability subsystem. Rather than inventing a separate scheme, the most consistent fix is to **extend that same vocabulary to the HTTP layer**:

- **NORMAL:** all endpoints served normally.
- **PRESSURE:** (trigger: request concurrency or engine-lock contention crosses a threshold) — apply basic per-client rate limiting; heavier read endpoints (full-snapshot dumps) get lower priority than lifecycle-control endpoints (start/stop/pause).
- **DEGRADED:** (trigger: engine governor itself is in DEGRADED) — read endpoints return cached/last-known-good snapshots rather than triggering fresh serialization work; non-essential endpoints (history/timeline queries) are shed first.
- **EMERGENCY:** only `/health` (once fixed) and lifecycle-control endpoints remain admitted.

Hysteresis: use the same threshold-crossing-with-cooldown pattern implied by the existing `PhaseBudgetGovernor` (don't invent a new mechanism) — require N consecutive over-threshold samples to enter a mode and M consecutive under-threshold samples to exit, so a single spiky request doesn't flap the system between modes.

This is explicitly **not** a recommendation to add Kafka, a service mesh, or a generic rate-limiting framework — a single in-process token-bucket or sliding-window limiter in the FastAPI middleware stack is sufficient at this system's current scale, and the RabbitMQ/Kafka situation in this same repo is a live cautionary example of what happens when infrastructure is added ahead of actual need.

---

## M. Refactoring Roadmap

Staged, incremental, no step requires downtime beyond a normal deploy:

**Stage 1 — immediate, low-risk, no architecture change** *(Necessary now)*
1. Fix `/health` to check engine-thread liveness + last-tick recency (R2).
2. Add backoff+jitter to the Redis reconnect loop (R3).
3. Separate malformed-payload handling from handler-exception handling in the stream consumer; add a literal DLQ stream (R3).
4. Reconcile the three conflicting phase-count docs against `src/engine/phases.py`'s actual `TickPhase` enum; fix the watchdog doc's file-path reference and status flag (R4).

**Stage 2 — decide and resolve the dead-infrastructure question** *(Necessary now — the decision, not necessarily the build-out)*
5. Either commit to a real RabbitMQ/Kafka use case and scope it properly, or remove the services, dependencies, and env vars entirely.
6. Regardless of which path: un-couple `ai_worker`'s startup from RabbitMQ's healthcheck immediately — this is a pure risk-reduction step independent of the broader decision (R1).

**Stage 3 — before any exposure beyond a trusted network** *(Valuable soon, gate explicitly on deployment plans)*
7. Add HTTP-layer admission control per the mode proposal in §L.
8. Fix the CORS `allow_origins`/`allow_credentials` configuration.
9. Add authentication to the API surface.

**Stage 4 — extend existing patterns rather than build new ones** *(Valuable soon)*
10. Extend the observability hot-path mode vocabulary (NORMAL/PRESSURE/DEGRADED/SURVIVAL) to the HTTP layer, reusing the existing governor pattern rather than inventing a new one.
11. Add a circuit breaker to `WebhookAlertSink` (R7).

**Stage 5 — longer-horizon, targeted, not blanket** *(Only needed at larger scale / probably-unnecessary-until-then)*
12. Cheap always-on partial determinism fingerprint to shrink the `audit_mode`-only coverage gap (R5) — only worth doing if off-path mutation bugs have actually occurred or are a live concern; otherwise this is "valuable soon" at best.
13. Targeted review of the highest-consequence broad-except sites (R8) — explicitly scoped, not a full-codebase sweep.

---

## Evidence Note

All file:line citations above were either verified directly in this session or cross-checked across at least two independent investigation passes before inclusion. Claims marked without a "Confirmed"/"Inferred"/"Unable to verify" qualifier in running text are Confirmed unless stated otherwise. Two items are explicitly flagged as **not fully verified** and would need a follow-up pass if they matter for a decision: (1) whether hardware-class (A/B/C) budgets are runtime-enforced or configuration-only; (2) whether in-game economy invariants (e.g., no negative gold) are structurally prevented or only test-covered.
