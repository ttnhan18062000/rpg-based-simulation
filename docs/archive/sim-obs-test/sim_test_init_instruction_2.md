---
status: archive
authority: P2
audience: historical
layer: testing
original_date: unknown
---

You are an expert simulation-engine architect and observability engineer.

We already have your first current-state observability report for the V2 RPG Simulation Engine. The report identified these major findings:

- `promtail-config.yml` appears to promote `tick` into a Loki label, causing high-cardinality risk.
- Prometheus/Grafana appear configured, but FastAPI/backend does not expose `/metrics`.
- `TraceEvent` exists but domain-level structured events are limited.
- Runtime invariant enforcement exists in parts of the engine/tests, but no continuous `HardLawMonitor` exists.
- Existing telemetry includes `WorldMetrics`, `PressureSignals`, `RuntimeStatus`, `SignalCollector`, `BenchHarness`, watchdog/certification tools, replay traces, and JSON logging.
- Proposed future architecture includes `SimulationEvent`, `EventBus`, `MetricsCollector`, `HardLawMonitor`, `AnomalyRuleEngine`, `BalanceAnalyzer`, `EntityTimelineRecorder`, `AutoTriageEngine`, `RunReportGenerator`, `LokiExporter`, `GrafanaMetricsExporter`, and `ScenarioSweeper`.

Now I need a second-pass clarification report.

Do not implement code.

Do not repeat the first report generally.

Focus only on the unclear points below and provide concrete evidence from the codebase.

For every answer, cite exact file paths, class names, function names, config blocks, and test names.

If something is not found, say: “not found in current codebase.”

## 1. Loki label safety deep dive

Please inspect all logging and Promtail/Loki-related configuration.

Answer:

- Is `tick` definitely promoted to a Loki label?
- Are `entity_id`, `worker_id`, `component`, `region_id`, `quest_id`, `target_id`, or other dynamic values also promoted to labels?
- Which values are safe labels?
- Which values must remain JSON fields only?
- Does Promtail correctly parse nested JSON fields like `context.tick`?
- What exact config change is needed?
- Could changing labels break any existing Grafana/Loki queries?

Output a table:

- Current label
- Cardinality risk
- Keep as label?
- Move to field?
- Evidence
- Recommended change

## 2. Prometheus and Grafana metric mapping

Please inspect:

- `docker-compose.yml`
- `prometheus.yml`
- Grafana dashboard JSON files
- FastAPI server files
- worker daemon files
- runtime metrics classes

Answer:

- What exact endpoint does Prometheus scrape?
- Does the backend expose `/metrics`?
- Which process actually owns the simulation metrics: FastAPI backend, worker daemon, kernel process, or certification runner?
- List every PromQL metric name expected by Grafana dashboards.
- For each expected metric, map it to an existing source if possible.

Output a table:

- Grafana/PromQL metric name
- Existing source class/function if available
- Missing or available?
- Metric type: counter/gauge/histogram/summary
- Recommended exporter location
- Notes

## 3. Existing event and trace inventory

Please inspect all event-like mechanisms.

Search for:

- `TraceEvent`
- `transaction_trace`
- `intent_results`
- `latest_result`
- `event`
- `trace`
- `audit`
- `replay`
- `checkpoint`
- `fingerprint`
- `logger`
- `print(`

Answer:

- Every place structured events are created.
- Every place transaction traces are appended.
- Every place domain logic emits string logs instead of structured events.
- Whether action results already contain enough data to create semantic events.
- Which current event/trace objects are replay-critical.
- Which are observation-only.

Output a table:

- Mechanism
- File/class/function
- Structured or string-based?
- Replay-critical?
- Domain coverage
- Missing fields
- Can be reused for `SimulationEvent`?

## 4. `TraceEvent` vs new `SimulationEvent`

Please analyze whether the future event model should:

- Extend `TraceEvent`
- Wrap `TraceEvent`
- Replace `TraceEvent`
- Keep `TraceEvent` for replay and create separate `SimulationEvent` for observability

Compare options.

Output:

- Option
- Pros
- Cons
- Risk to determinism
- Migration complexity
- Recommendation

## 5. Domain event volume policy

Please estimate event volume risk by domain.

Domains:

- movement
- combat
- resource harvesting
- inventory transfer
- shop/economy
- quest
- strategic project
- lifecycle/death
- region/faction
- anomaly events
- hard law violations

For each domain, recommend one of:

- always emit
- emit only state transitions
- emit sampled events
- emit only on anomaly
- aggregate into metrics only

Output a table:

- Domain
- Expected frequency
- Recommended emission policy
- Required event fields
- Loki export policy
- Timeline retention policy

## 6. Hard law inventory

Please identify existing hard laws from code/tests/checklists.

Group by:

- movement
- combat
- inventory/resource
- quest/reward
- lifecycle/death
- strategic/project
- economy/shop
- region/faction
- determinism/replay

For each law, identify:

- Existing runtime enforcement location
- Existing test coverage
- Whether it should be monitored every tick
- Whether it can be DirtySet-scoped
- Whether it requires full-world scan
- Recommended severity if violated
- Whether violation should stop certification run

Output a table:

- Law
- Domain
- Enforcement location
- Test coverage
- Runtime monitor needed?
- DirtySet-scoped?
- Severity
- Notes

## 7. HardLawMonitor first version scope

Based on the inventory, propose the smallest safe first version of `HardLawMonitor`.

Constraints:

- Must be useful.
- Must not kill performance.
- Must support long-run simulations.
- Must distinguish certification mode from light mode.

Output:

- P0 laws to monitor first
- P1 laws for later
- Laws that should remain test-only
- Suggested monitor cadence
- Suggested DirtySet usage
- What to emit on violation

## 8. Anomaly engine architecture decision

Please evaluate three options:

1. In-process live anomaly detection during/after each tick
2. Out-of-process consumer reading EventBus or queue
3. Post-run analyzer reading replay/event chunks

Compare:

- Determinism risk
- Runtime overhead
- Memory overhead
- Implementation complexity
- Best fit for first release
- Best fit for long-run certification
- Best fit for production deployment

Give a recommendation for v1 and v2.

## 9. Entity timeline retention model

Please propose a concrete retention policy.

Evaluate:

- Per-entity ring buffer
- Global event ring buffer
- Flagged-entity-only timeline
- Disk-backed timeline
- Reconstruct timeline from replay chunks

For each, compare:

- Memory risk
- Debugging usefulness
- Implementation complexity
- Determinism risk
- Best use case

Recommend a v1 retention model.

## 10. WorldMetrics and semantic metrics gap analysis

Please inspect `WorldMetrics`, `MetricsService`, `PressureSignals`, `RuntimeStatus`, and benchmark output.

For each desired semantic metric below, say whether it exists or must be added:

- alive entity count
- active entity count
- idle ratio
- stuck ratio
- movement failure rate
- oscillation count
- position swap count
- resource produced per window
- resource consumed per window
- resource stockpile
- inventory full ratio
- shop transaction rate
- gold created/destroyed
- combat start/end rate
- combat duration
- faction win rate
- death rate
- quest started/completed/rewarded
- quest stall count
- project started/completed/stalled
- blocker creation/resolution rate
- goal churn rate
- anomaly count by type
- hard law violation count

Output a table:

- Metric
- Exists?
- Current source
- Missing data
- Recommended collector
- Grafana priority

## 11. Balance profile readiness

Please inspect whether scenario expectations or balance profiles already exist.

Answer:

- Are scenario expectations modeled today?
- Can scenarios define expected ranges?
- Are thresholds hard-coded in tests?
- Is there any YAML/JSON scenario config?
- What would be the best place to define balance profiles?

Output:

- Existing mechanism
- Reusable?
- Gap
- Recommendation

## 12. Production watchdog readiness

Please inspect production runtime/worker daemon code.

Answer:

- Is there a production worker daemon?
- Does it run the simulation kernel?
- Does it have watchdog protection?
- Does it emit structured failure records?
- What should happen when watchdog fires?
- Is certification watchdog reusable?

Output a table:

- Runtime path
- Watchdog present?
- Failure behavior
- Structured event support
- Gap
- Recommendation

## 13. Final output format

Return a second-pass clarification report with these sections:

A. Executive Summary of Remaining Unknowns  
B. Loki Label Safety Findings  
C. Prometheus/Grafana Metric Mapping  
D. Event/Trace Inventory  
E. TraceEvent vs SimulationEvent Recommendation  
F. Event Volume Policy  
G. Hard Law Inventory  
H. HardLawMonitor V1 Scope  
I. Anomaly Engine Architecture Decision  
J. Entity Timeline Retention Recommendation  
K. Semantic Metrics Gap Table  
L. Balance Profile Readiness  
M. Production Watchdog Readiness  
N. Final Recommendations Before Implementation Planning  

Be specific. Do not guess. Cite exact file paths, classes, functions, and tests.
