---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC
artifact_type: test_plan
tags: [observability]
---

# Test Plan — TCK-20260817-ERROR-HANDLING-HYGIENE-EPIC

This supersedes the placeholder `test_plan.md` written while this ticket was still epic-tier
(scope-only). The ticket was downgraded to standard tier on 2026-08-18 with concrete acceptance
criteria, so this is the real pre-implementation test plan.

## Regression Surface

**Unit:**
- `tests/unit/observability/test_alert_router.py` — `TestAlertRouter`, `TestLogAlertSink`,
  `TestAlertDeduplicator`, `TestAlertEvent`. None construct a `WebhookAlertSink` directly, but
  `TestAlertRouter.test_sink_exception_does_not_crash` (line 260) verifies the router's per-sink
  exception guard, which must keep working if the webhook sink's exception surface changes shape.
- `tests/unit/observability/test_watchdog.py::test_run_cycle_trip_routes_alert_event` — cited by
  parity ledger entry `INFRA-358` (`docs/parity_ledger/infrastructure.yaml:10602`) as the test
  path proving the watchdog's `WatchdogTrip` alert reaches `AlertsManager`/`AlertRouter`. Depends
  on `WebhookAlertSink` continuing to accept registration and expose `.send()`/`.shutdown()` with
  their current signatures.

**Integration:**
- `tests/integration/observability/test_alert_webhook_sink.py` — `TestWebhookAlertSinkIntegration`
  (`test_successful_delivery`, `test_server_error_does_not_crash`,
  `test_connection_timeout_does_not_crash`, `test_disabled_sink_does_not_send`) and
  `TestAlertsManagerIntegration` (`test_manager_creates_router_with_log_sink`,
  `test_manager_singleton_returns_same_router`, `test_manager_reset_creates_new_router`). This is
  the direct regression surface for the file under change.
  - **`test_server_error_does_not_crash` needs attention, not just a pass/fail check**: it uses
    `max_retries=2` and a fixed `time.sleep(4.0)` wall-clock wait tuned to the *current* linear
    schedule (`0.5 * attempt`, i.e. one ~0.5s inter-attempt sleep). Once real exponential
    backoff+jitter replaces the linear formula, the worst-case inter-attempt delay changes (base
    formula dependent — confirm against whatever base/cap constants Plan chooses, mirroring
    `RedisStreamConsumer.BACKOFF_BASE_SECONDS`/`BACKOFF_CAP_SECONDS`). Update this sleep constant
    (or refactor the test to poll/wait deterministically) as part of implementation, not as an
    afterthought — verify it still passes rather than assuming the existing sleep budget covers
    the new schedule.
  - `test_disabled_sink_does_not_send` and `test_successful_delivery` don't touch the retry loop
    at all — least likely to need changes, but must still pass unmodified.

## New Tests Required

Per acceptance criteria:

1. **`test_backoff_delay_is_exponential_not_linear`**
   - Category: unit
   - Verifies: the delay computed between attempt N and N+1 grows exponentially (ratio ≈ 2x,
     modulo jitter/cap), not linearly. Directly targets AC #1 ("backoff behavior matches its own
     in-code documentation"). If implementation extracts a `_compute_backoff_delay`-style helper
     (recommended, mirroring `RedisStreamConsumer`'s precedent — see investigation.md Prior Work),
     test it directly and deterministically via an injectable `rng`/seed rather than asserting on
     wall-clock `time.sleep` durations.
   - Location: `tests/unit/observability/test_webhook_alert_sink.py` (new file — no unit-level
     test file exists for `sinks.py` today, only the integration-level
     `test_alert_webhook_sink.py`; mirrors the existing split between
     `test_stream_consumer_resilience.py` (unit, mocked client) and
     `test_redis_stream_adapter.py`/PEL-reclaim integration tests for the sibling
     `RedisStreamConsumer` fix).

2. **`test_backoff_has_jitter`**
   - Category: unit
   - Verifies: two computed delays for the same attempt number, using different RNG seeds/states,
     are not identical — confirms jitter is actually applied, not just present in a comment.
     Directly targets AC #1.
   - Location: `tests/unit/observability/test_webhook_alert_sink.py`

3. **`test_comment_matches_implementation`** (optional, low value if the above two exist) —
   alternatively, skip a dedicated test and rely on #1/#2 to make the in-code comment's claim
   either true or corrected; do not add a test that only asserts prose-matching, that's not a
   meaningful behavioral check.

4. **`test_circuit_breaker_opens_after_consecutive_failures`**
   - Category: unit
   - Verifies: after N consecutive failed deliveries (N = whatever threshold Plan picks), the
     sink stops issuing HTTP requests to the dead endpoint entirely (mock/patch `requests.post`
     and assert call count stays flat across further `send()` calls). Directly targets AC #2
     ("A circuit breaker prevents indefinite full-sequence retries against a dead endpoint").
   - Location: `tests/unit/observability/test_webhook_alert_sink.py`

5. **`test_circuit_breaker_half_open_retry_recovers`**
   - Category: unit
   - Verifies: after the open-state cooldown elapses, a single probe request is attempted
     (half-open state); if it succeeds, the breaker closes and normal delivery resumes; if it
     fails, it reopens. Directly targets AC #2's "half-open retry" language from the ticket Scope.
   - Location: `tests/unit/observability/test_webhook_alert_sink.py`

6. **`test_circuit_breaker_open_send_returns_false_not_silent`**
   - Category: unit / anti-drift guard
   - Verifies: when the circuit is open, `send()`/the underlying dispatch still resolves to a
     well-defined failure signal (not indistinguishable from success, not an unhandled exception)
     — guards against the Anti-Drift Hazard in investigation.md ("circuit breaker that makes
     failures indistinguishable from... successful delivery would regress observability").
   - Location: `tests/unit/observability/test_webhook_alert_sink.py`

7. **Broad-except targeted review — no new test required as a blanket rule**, but for any site
   where Plan/Implement decides a fix *is* warranted (none were identified as needing one during
   this investigation — see investigation.md's "Disposition of the targeted review"), that
   specific fix must get its own new/updated test at implementation time, scoped to that site.
   AC #3 ("names specific sites reviewed and their disposition") is satisfied by the investigation
   document's site-by-site writeup, not by a new automated test — there is no single test that can
   assert "the review was targeted, not blind."

## Scoped Pytest Commands

```
# Webhook sink — new unit tests + existing integration regression surface
pytest tests/unit/observability/test_webhook_alert_sink.py tests/integration/observability/test_alert_webhook_sink.py -v

# Alert routing/manager regression (router's per-sink exception guard, manager singleton lifecycle)
pytest tests/unit/observability/test_alert_router.py -v

# Watchdog wiring regression (INFRA-358 dependency — confirms webhook sink contract unchanged)
pytest tests/unit/observability/test_watchdog.py -v

# If any broad-except site review results in an actual code change, scope its own test file
# directly (e.g. tests/unit/engine/... or tests/integration/... matching the touched module) —
# do not run pytest tests/engine/ or any other unscoped directory-wide sweep.
```

Never `pytest tests/` — scope stays within `tests/unit/observability/` and
`tests/integration/observability/` for the webhook-sink/circuit-breaker portion of this ticket,
plus whatever narrow test path corresponds to any single broad-except site actually touched.

## Anti-Drift Test Guards

- **`test_disabled_sink_does_not_send`** (existing, `test_alert_webhook_sink.py:160`) must keep
  passing unmodified — guards against the circuit-breaker or backoff change accidentally making a
  disabled sink attempt delivery (e.g. if circuit-breaker state initialization runs before the
  `enabled` check).
- **`test_manager_singleton_returns_same_router`** / `test_manager_reset_creates_new_router`
  (existing, `test_alert_webhook_sink.py:190/196`) guard against circuit-breaker state accidentally
  leaking across `AlertsManager.reset()` boundaries — a fresh `WebhookAlertSink` built after
  `reset()` must start with a closed circuit, not inherit a prior instance's open state (this
  would only be a real risk if circuit-breaker state were implemented as a module-level global
  instead of an instance attribute — see investigation.md's Mechanics/Engine Constraints section
  on why it must be instance-scoped).
- **`test_sink_exception_does_not_crash`** (existing, `test_alert_router.py:260`) guards the
  router-level containment boundary independent of whatever `WebhookAlertSink` internally does —
  should be unaffected by this ticket's change, and passing it unmodified is itself evidence the
  external contract wasn't broken.
- A new guard worth adding — **`test_webhook_sink_send_signature_unchanged`** (or equivalent
  contract check) — is optional, but if added it should assert `send(alert: AlertEvent) -> bool`
  stays intact via `inspect.signature`, directly protecting `INFRA-358`'s "reused as-is, no new
  sink code" claim from silent invalidation.
- **Do not let any new backoff/circuit-breaker test rely on real wall-clock `time.sleep` for
  assertions** where avoidable — prefer an injectable clock/RNG (mirroring
  `RedisStreamConsumer._compute_backoff_delay`'s `rng: Optional[random.Random]` parameter) so
  tests are fast and deterministic rather than timing-flaky. The existing integration tests do use
  real sleeps (`test_successful_delivery`, `test_server_error_does_not_crash`) — that precedent is
  acceptable for integration-level end-to-end confirmation, but new unit-level backoff/jitter math
  tests should not repeat that pattern.
