# Investigation — Milestone 40: Alert Routing and Incident Workflow

This document records the investigation into existing code components, the anomaly worker, hard law monitor, and how we will safely route alerts.

---

## 🔍 Existing Systems & Decoupling

The RPG Engine and its observability platform are strictly designed to prevent runtime degradation due to telemetry processing. This is extremely critical because our engine is real-time and profile-driven.

### 1. Hard Law Violation Checks
The Hard Law checks occur at the end of each tick in `Kernel._run_hard_law_checks()`.
```python
        violations = HardLawMonitor.check(self._state, dirty_set)
        ...
        for v in violations:
            # logs warnings or raises exception depending on ObservabilityMode
```
To route these to alerts:
- We want to capture `violations` and construct an `AlertEvent` for each.
- The `AlertRouter` must process them. Since the `Kernel` tick is deterministic and synchronized, the router and any synchronous sink must not perform heavy or blocking I/O on the main simulation thread.
- **LogAlertSink** is synchronous but very fast (in-memory write to standard log buffers).
- **WebhookAlertSink** performs HTTP requests. We **must** execute this off the main thread, or use an async/non-blocking thread pool executor to prevent slowing down the engine pacing! This is a major structural safeguard to enforce compliance with the testing and architecture rules.

### 2. Anomaly Worker
The `LiveAnomalyWorker` is implemented in `src/observability/anomaly/worker.py`. Let's check how it runs. Let's do `grep_search` or view it to check its background loop.
Wait, let's view `src/observability/anomaly/worker.py` around lines 1-100 or use grep to see where it handles anomalies.
Let's see if the worker runs in a separate process or thread. Yes, `WorkerManager` or separate processes are used. We will ensure that when the worker captures critical exceptions or critical anomalies, it sends alerts asynchronously.

### 3. Webhook Delivery Resilience
- We will construct the `WebhookAlertSink` using python's `requests` library (which is already installed in the virtual environment).
- To prevent blocking, we will use a `ThreadPoolExecutor` inside `WebhookAlertSink` or `AlertRouter` to dispatch HTTP calls asynchronously.
- The `requests.post` call must have a strict `timeout` (e.g. 5.0 seconds).
- It must catch `requests.RequestException` and handle it gracefully (simply logging the delivery failure and continuing).
- It must support retries with exponential backoff or simply up to 3 quick retries, again performed in the background thread.
