---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M40
artifact_type: test_plan
tags: [sim, obs, m40]
---

# Test Plan — Milestone 40: Alert Routing and Incident Workflow

We will establish robust test suites covering both unit logic and integration paths to guarantee correctness, reliability, and security of the Alert Routing system.

---

## 🧪 Test Strategies

We will write two new test files as specified in the spec:
1. `tests/unit/observability/test_alert_router.py`
   - Verifies `AlertEvent` fields and JSON serialization.
   - Verifies `AlertDeduplicator` correctly suppresses repeat alerts within the sliding window, and allows them after window expiration or when a different `dedup_key` is used.
   - Verifies `AlertRouter` routes alerts to registered sinks.
   - Verifies severity threshold filtering works (e.g. routing only messages of a certain severity).
2. `tests/integration/observability/test_alert_webhook_sink.py`
   - Spawns a lightweight local HTTP server (using `http.server` or similar) in a separate thread to act as the Webhook target.
   - Asserts the Webhook sink successfully posts the structured JSON payload.
   - Asserts that when the Webhook target responds with error codes (e.g. 500) or times out, the simulation/worker thread does not crash and the failure is captured in logs.

---

## 🛠️ Verification Execution

We will run the tests using:
```bash
pytest tests/unit/observability/test_alert_router.py tests/integration/observability/test_alert_webhook_sink.py
```
And we will also run the full API and observability suite to check for regressions.
