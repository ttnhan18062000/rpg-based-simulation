# Legacy `src` Add-On Checklist

## Missing items not included in the previous RPG-core checklists

This checklist is an **additive checklist** for original `src` behaviors that were **not** included in the previous RPG-core atomic logic checklists.

It covers only the missing legacy replacement surface:

- CLI / entrypoint behavior
- configuration / environment-flag behavior
- broker-disabled and infrastructure fallback behavior
- chaos / resilience / infrastructure determinism
- replay / logging / metrics / observability compatibility
- API transport / protocol / compression compatibility
- import-time and integration-time infrastructure isolation

This checklist should remain **separate** from the RPG-core checklist.

---

## Status legend

For each item below, recording status as [x] (fully supported) or [ ] (unsupported/divergent).

### Section A: Headless Runner / Command Line Interface (CLI)

- [x] Command Line Interface (CLI) provides a standard entry point for headless execution.
- [ ] Subcommands for specific simulation tasks (run, profile, analyze).
- [ ] Profile-based overrides for simulation parameters via CLI flags.
- [ ] Diagnostic output (metrics, events) returned to stdout/stderr.

original evidence: `src/__main__.py`, `src/utils/cli_parser.py`
`src_v2` evidence: `src_v2/certification/harness.py`
divergence note: v2 leverages a profile-driven `CertificationHarness` as the primary headless entry point, replacing legacy subcommand dispatch with a structured certification flow.
proof path: `tests_v2/certification/test_harness_behavior.py`

### CLI mode and parser contract

- [ ] `python -m src` defaults to server mode when no subcommand is provided.
- [ ] `python -m src serve` accepts the original `--host`, `--port`, `--seed`, `--entities`, `--workers`, `--log-level` arguments.
- [ ] `python -m src cli` accepts the original `--ticks`, `--entities`, `--seed`, `--workers`, `--grid-width`, `--grid-height`, `--replay`, `--log-level` arguments.
- [ ] `python -m src inspect` accepts the original `--id`, `--seed`, `--ticks`, `--entities`, `--workers`, `--log-level` arguments.
- [ ] CLI argument defaults remain compatible with legacy expectations.
- [ ] Invalid CLI arguments fail in a controlled, parser-driven way.
- [ ] CLI replay-file argument writes to the expected output path semantics.
- [ ] CLI mode still initializes the same baseline world-building flow (town, sanctuary, camps, hero spawn, goblin spawn) under equivalent config.

### CLI environment boot behavior

- [ ] CLI mode forces broker-disabled behavior through environment setup when not already set.
- [ ] CLI startup still loads registries before simulation loop startup.
- [ ] CLI startup still wires logging before engine loop execution.
- [ ] CLI shutdown still tears down worker infrastructure cleanly after simulation.

---

# B. Optional-broker disabled-mode compatibility

Relevant original source/test evidence:

- `tests/api/test_broker_isolation.py`
- `tests/integration/infra/test_brokerless_import.py`

### RabbitMQ disabled-mode behavior

- [ ] `DISABLE_RABBITMQ=1` causes RabbitMQ client code to enter explicit disabled mode.
- [ ] RabbitMQ client imports do not crash when disabled.
- [ ] RabbitMQ public accessors return safe no-op values (`None`) when disabled.
- [ ] RabbitMQ disabled-mode behavior remains safe even when broker libraries are missing.

### Kafka disabled-mode behavior

- [ ] `DISABLE_KAFKA=1` causes Kafka client code to enter explicit disabled mode.
- [ ] Kafka client imports do not crash when disabled.
- [ ] Kafka public accessors return safe no-op values (`None`) when disabled.
- [ ] Kafka disabled-mode behavior remains safe even when broker libraries are missing.

### Redis disabled / missing-package behavior

- [ ] Redis client behavior remains safe when Redis package or runtime is unavailable.
- [ ] Redis accessors fail safely without crashing simulation bootstrap when Redis is optional.

### Disabled-mode import isolation

- [ ] Headless runner imports still succeed when optional brokers are disabled.
- [ ] Action-system imports still succeed when optional brokers are disabled.
- [ ] Import-time behavior does not accidentally force broker setup.

---

# C. Worker-pool and infrastructure fallback behavior

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_infrastructure_isolation.py`
- worker-pool usage in original CLI and loop wiring

#### Section C: Worker Fallback & Scaling

- [x] Simulation remains functional when worker counts are set to 0 (workerless/sequential mode).
- [x] Work selection logic is identical between sequential and concurrent execution (deterministic priority).
- [x] Worker errors are handled without halting the entire tick loop (error isolation).
- [ ] Dynamic worker scaling supports adjusting pool size during runtime.

original evidence: `engine/worker_pool.py`, `engine/executor.py`
`src_v2` evidence: `src_v2/engine/executor.py` (`SequentialExecutor` vs `ConcurrentExecutor`)
divergence note: v2 enforces identical work-selection logic across both executors to ensure deterministic parity regardless of concurrency settings.
proof path: `tests_v2/engine/test_worker_equivalence.py`

### Worker fallback semantics

- [ ] Worker pool falls back to inline/local execution when broker transport is unavailable.
- [ ] Worker pool does not require live RabbitMQ/Kafka to execute local simulation behavior.
- [ ] Worker fallback preserves authoritative action generation semantics.
- [ ] Worker fallback preserves deterministic ordering expectations in local mode.
- [ ] Worker shutdown remains safe after fallback execution paths.
- [ ] Missing broker infrastructure does not block minimal simulation startup.

### Import/runtime isolation

- [ ] Infrastructure module isolation prevents optional dependencies from contaminating normal simulation imports.
- [ ] Runtime paths that do not require brokers do not import or initialize them accidentally.
- [ ] Fallback behavior is exercised by real tests, not only by mocks or assumptions.

---

# D. Chaos mode and infrastructure resilience

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_chaos.py`

### Chaos resilience

- [ ] Chaos-enabled runs survive AI-result drop conditions without immediate simulation failure.
- [ ] Chaos-enabled runs continue ticking through configured chaos-drop scenarios.
- [ ] Chaos does not corrupt authoritative world state shape.
- [ ] Chaos does not break snapshot acquisition.

### Chaos determinism

- [x] Given identical seed and identical chaos configuration, repeated chaos-mode runs remain deterministic..
- [x] Chaos-mode determinism is verified by repeated world-state fingerprint comparison.
- [x] Chaos-enabled infrastructure does not introduce hidden non-determinism into equivalent runs.

---

# E. Replay compatibility outside pure RPG-core semantics

Relevant original source/test evidence:

- replay usage in `src/__main__.py`
- replay-related explainability / determinism / regression tests
- `tests/e2e/test_deterministic_replay.py`

### Replay output contract

- [ ] Replay files are written in the expected legacy location/format semantics for headless runs.
- [ ] Replay snapshots preserve deterministic entity ordering and field availability where legacy tests rely on them.
- [x] Replay preserves enough world-state detail to support legacy fingerprinting and regression assertions.
- [x] Replay can support structural comparison between repeated runs with same seed.
- [ ] Replay remains aligned with other truth surfaces where legacy tests expect parity.

### End-to-end deterministic replay path

- [x] Same seed and equivalent configuration produce identical replay-visible state across runs..
- [ ] Different seeds produce divergent replay-visible state.
- [ ] Replay includes ground-item state where legacy determinism tests inspect it.
- [ ] Replay includes enough actor combat/progression/mind state for state-fingerprint checks.

---

# F. Structured logging compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py`
- original logging setup and JSON formatter usage in source

#### Section F: Logging & Observability

- [x] Structured logs provide machine-readable event streams (JSON).
- [x] Contextual attributes (tick, entity_id, correlation_id) are automatically attached to log messages.
- [x] Signal collection aggregates multi-domain updates into a single stream.
- [x] Signal flushing is synchronized with the authoritative world-state advancement.

original evidence: `utils/logging.py`, `engine/observability.py`
`src_v2` evidence: `src_v2/engine/observability.py`
divergence note: v2 replaces ad-hoc logging with a centralized `SignalCollector` that enforces contextual truth and tick-atomic flushing.
proof path: `tests_v2/engine/test_signals_persistence.py`

### Logging format contract

- [ ] CLI stdout logs remain valid JSON line-by-line.
- [ ] Each emitted structured log includes mandatory fields:
  - [ ] `timestamp`
  - [ ] `level`
  - [ ] `message`
  - [ ] `component`
- [ ] Log output remains machine-parseable under normal CLI execution.

### Logging context injection

- [ ] World-loop logs include tick context.
- [ ] World-loop logs preserve identifiable component naming.
- [ ] Worker-pool logs preserve identifiable component naming where emitted.
- [ ] Main entrypoint logs preserve identifiable `__main__` or equivalent component identity.
- [ ] Structured logging remains compatible with legacy context-injection expectations.

---

# G. Metrics and monitoring compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py` (Prometheus check)
- original metrics/logging stack wiring in source

### Prometheus / telemetry compatibility

- [ ] Simulation metrics remain scrapeable by Prometheus in equivalent stack configurations.
- [ ] Legacy-queried metric names remain available where replacement claims require them.
- [ ] Tick-duration metrics remain emitted under the expected metric contract.
- [ ] Monitoring stack checks do not silently pass with empty data.

### Operational observability

- [ ] Engine-side metrics remain available without forcing gameplay divergence.
- [ ] Metrics do not rely on broker-only paths if local/headless execution is supposed to work without brokers.
- [ ] Monitoring compatibility is verified under realistic stack conditions, not just unit stubs.

---

# H. API protocol and transport compatibility

Relevant original source/test evidence:

- API metadata tests
- websocket handshake tests
- gzip compression test

### Metadata endpoints

- [ ] Protocol metadata endpoint remains available at the expected route.
- [ ] Metadata response still includes entity key mapping where legacy consumers expect it.
- [ ] Metadata response still includes state enum mapping where legacy consumers expect it.
- [ ] Protocol metadata field order/meaning remains compatible where clients depend on it.

### WebSocket protocol behavior

- [ ] WebSocket endpoint still supports legacy handshake semantics.
- [ ] JSON handshake mode remains supported.
- [ ] MessagePack handshake mode remains supported.
- [ ] Initial post-handshake payload remains structurally compatible with legacy client expectations.
- [ ] Tick/entity/event payload shape remains compatible where explicitly defined by legacy tests.

### Compression behavior

- [ ] GZip middleware or equivalent response compression remains functional for large metadata responses.
- [ ] Compression support does not break standard metadata endpoint access.

---

# I. Headless runner / final-system execution compatibility

Relevant original source/test evidence:

- headless runner import/use tests
- deterministic replay tests
- brokerless import tests
- cognition/replay consistency regression tests

### Headless execution path

- [ ] A minimal production-like headless run can still execute without optional brokers when disabled.
- [ ] Headless run still produces the expected result artifacts (at minimum replay, and where applicable manifest/graph outputs).
- [ ] Headless runner import remains isolated from optional broker setup.
- [ ] Final-system path remains suitable for regression use rather than demo-only use.

### Artifact consistency

- [ ] Final-system artifacts remain mutually consistent where legacy tests compare them.
- [ ] Structural graph/export surfaces remain aligned with replay where legacy tests require parity.
- [ ] Artifact generation failure paths remain visible rather than silently swallowed.

---

# J. Infrastructure-side “unhappy path” compatibility actually evidenced in legacy tests

Only include source-grounded unhappy paths.

### Disabled/missing dependency paths

- [ ] Missing RabbitMQ package with disabled flag does not crash import.
- [ ] Missing Kafka package with disabled flag does not crash import.
- [ ] Missing Redis package does not crash safe initialization paths where optional.
- [ ] Missing broker dependencies do not block headless runner imports.

### Runtime degradation paths

- [ ] Worker transport degradation falls back safely to local execution.
- [ ] Chaos-mode packet/result drop does not terminate the simulation prematurely under supported settings.
- [ ] Monitoring checks fail loudly when expected data is missing.

### CLI/runtime robustness

- [ ] CLI execution still emits structured logs under minimal simulation runs.
- [ ] Short runs still produce enough output for regression inspection.
- [ ] Minimal runs do not require full external stack unless explicitly in E2E stack mode.

---

# K. Explicit exclusions from this add-on checklist

These should stay out unless you create a third checklist:

- generic security advice not tied to actual legacy code/tests
- generic performance wishes not evidenced by legacy behavior
- speculative logging/telemetry fields not checked in legacy code/tests
- invented infra classes or APIs not present in legacy source
- non-gameplay docs/release-gate concerns already tracked elsewhere

---

# L. Recommended artifact name

`legacy_src_system_compatibility_checklist.md`

---

# M. Recommended ledger columns

For each checklist item above, record:

- legacy area
- atomic item
- original source evidence
- original test evidence
- `src_v2` evidence
- status
- divergence note
- proof path
- owner
- phase target
