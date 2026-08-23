---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC
artifact_type: test_plan
tags: [architecture, observability]
---

# Test Plan — TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC

**Note:** Investigation recommends splitting this ticket into two child tickets (auth,
admission-control), sequenced auth-first — see `investigation.md`'s Risks and Open Questions. This
test plan is written against the ticket's current single-ticket acceptance criteria so it remains
usable either way: if the split is taken, each child ticket inherits the relevant subset below
(auth ticket: New Tests items 1-5; admission-control ticket: items 6-11).

## Regression Surface

Existing tests that must keep passing — scoped to `src/api/server.py` and the mode vocabulary this
ticket extends:

**unit**
- `tests/unit/observability/test_obs_backpressure.py` — `ObservabilityMode`/
  `ObservabilityController` behavior (INFRA-199, P1 parity entry). Must not regress if
  implementation touches this module directly rather than building a parallel HTTP-side
  controller.

**integration (API)**
- `tests/api/test_cors_config.py` — CORS middleware ordering/behavior; a new auth/rate-limit
  middleware must not change CORS header behavior on existing routes.
- `tests/api/test_health_liveness.py` — `/health` route wiring; `/health` is explicitly called out
  in D23 §L as one of the routes that must remain admitted even in the most degraded admission
  mode, so this test doubles as a floor for that requirement.
- `tests/api/test_scenario_runtime_api.py`, `test_decision_api.py`, `test_chronicle_api.py`,
  `test_campaign_history_api.py`, `test_cognition_history_api.py`,
  `test_phase27_behavior_query_api.py`, `test_historical_event_search_api.py`,
  `test_live_observability_status.py`, `test_live_health_api.py`,
  `test_live_entity_inspection.py`, `test_paged_logic.py`, `test_rest_parity.py` — every existing
  route must remain reachable and return its current shape under NORMAL mode with a valid (or,
  pre-auth-ticket-landing, still-optional-during-rollout) API key; these are the routes at risk of
  an over-broad middleware accidentally gating or 429-ing normal traffic.
- `tests/api/test_ws_protocol.py`, `test_observability_websocket.py` — WebSocket routes are a
  distinct protocol from REST; confirm whether admission control is scoped to REST only or must
  also cover the WS upgrade handshake (open question for Plan — flag if WS is out of scope, don't
  silently skip verifying it either way).

**architecture guard**
- `tests/tools/test_parity_index_baseline.py` (or equivalent) — if new parity entries are added
  without `test_path`, this baseline may drift; check after adding INFRA entries for auth/admission
  control.

## New Tests Required

Per acceptance criteria (`At least one auth mechanism gates the API surface` /
`HTTP requests are admitted/throttled/shed per-client, per NORMAL/PRESSURE/DEGRADED/SURVIVAL`):

**Auth (acceptance criterion 1)**

1. **`test_request_without_api_key_is_rejected`**
   Category: integration. Verifies: a request to a protected route with no `X-API-Key` (or
   equivalent) header returns 401, not a silent pass-through or a 500.
   Location: `tests/api/test_api_key_auth.py`

2. **`test_request_with_invalid_api_key_is_rejected`**
   Category: integration. Verifies: a syntactically well-formed but unregistered/incorrect key
   returns 401, and the response body does not leak whether the key format was valid vs. the key
   itself was wrong (no oracle for key enumeration).
   Location: `tests/api/test_api_key_auth.py`

3. **`test_request_with_valid_api_key_is_admitted`**
   Category: integration. Verifies: a request bearing a correctly-provisioned key succeeds and
   reaches the underlying route handler (assert on real route behavior, not just status code, per
   this repo's existing `test_cors_config.py`/`test_health_liveness.py` convention of asserting
   real response content over a real `TestClient`, not mocked headers).
   Location: `tests/api/test_api_key_auth.py`

4. **`test_api_key_comparison_is_constant_time`** (or equivalent: assert the comparison function
   used is `hmac.compare_digest` / `secrets.compare_digest`, not `==`)
   Category: unit / architecture guard. Verifies: the key-comparison implementation does not use a
   short-circuiting `==` string comparison (timing side-channel). Given no repo precedent exists
   for this, this test should assert against the actual comparison call site directly (e.g. via
   `inspect` or a source-scan guard) rather than trying to measure timing, which is unreliable in
   CI.
   Location: `tests/unit/api/test_api_key_storage.py` (or wherever the auth module lands)

5. **`test_api_key_never_appears_in_logs_or_error_responses`**
   Category: integration. Verifies: a request with an invalid key, and a request causing a
   500-level error, do not echo the submitted key value back in the response body or in captured
   log output — a Security section item from `.claude/skills/api-design-principles/assets/
   api-design-checklist.md` ("No secrets in responses").
   Location: `tests/api/test_api_key_auth.py`

**Admission control (acceptance criterion 2)**

6. **`test_normal_mode_admits_all_requests`**
   Category: integration. Verifies: under no pressure signal, all routes respond normally (no
   throttling, no shedding) — the NORMAL-mode floor.
   Location: `tests/api/test_http_admission_control.py`

7. **`test_pressure_mode_rate_limits_per_client_not_globally`**
   Category: integration. Verifies: once a single client's request rate crosses the PRESSURE
   trigger, that client is throttled but a second, distinct client (different API key) is not —
   the core "one noisy tenant must not degrade service for others" requirement from the ticket's
   own scope. This is the single most important new test in this ticket; a global (not per-client)
   limiter would pass every other test here and still fail the ticket's actual purpose.
   Location: `tests/api/test_http_admission_control.py`

8. **`test_degraded_mode_sheds_non_essential_endpoints_first`**
   Category: integration. Verifies: when a client is in DEGRADED, non-essential/heavy endpoints
   (e.g. `/api/v1/inspect`, full-snapshot dumps) are shed/return degraded responses before
   lifecycle-control endpoints (`/api/v1/control/pause`, `/api/v1/control/resume`) and `/health`,
   matching D23 §L's stated per-mode endpoint priority.
   Location: `tests/api/test_http_admission_control.py`

9. **`test_survival_mode_admits_only_health_and_control`**
   Category: integration. Verifies: in the most degraded mode (SURVIVAL, matching the ticket's
   acceptance-criteria naming — see investigation.md's note on the `EMERGENCY` vs `SURVIVAL` naming
   inconsistency in the source design doc), only `/health` and lifecycle-control endpoints remain
   admitted for the affected client; everything else is shed with a clear status
   (429/503, not a silent hang or generic 500).
   Location: `tests/api/test_http_admission_control.py`

10. **`test_admission_mode_recovery_requires_dwell_and_confidence_window`**
    Category: unit / architecture guard. Verifies: mode recovery (e.g. PRESSURE -> NORMAL) is
    gated by dwell time + N-consecutive-under-threshold samples, mirroring
    `ResourceGovernor._can_recover()`'s pattern — not an instant snap-back on the first
    good sample, which would flap. Directly tests the hysteresis reuse called out in
    investigation.md.
    Location: `tests/unit/api/test_admission_controller.py` (or co-located with the new
    controller module)

11. **`test_admission_status_endpoint_reports_per_client_mode`**
    Category: integration. Verifies: an accessor mirroring `observability_status()` (per
    investigation.md's recommendation) exists and reports mode/fill-state per client, not just a
    single global value — needed for operability (this is the HTTP-layer equivalent of
    `docs/architecture/observability_hot_path_safety_contract.md` §5's `observability_status()`
    contract).
    Location: `tests/api/test_http_admission_control.py`

12. **`test_unbounded_client_state_is_bounded_or_evicted`**
    Category: architecture guard. Verifies: the per-client admission-state store (dict keyed by
    client ID) has an eviction/TTL/max-size policy and does not grow unboundedly as new distinct
    client IDs are seen — directly tests investigation.md's flagged "new durable-ish state with no
    existing lifecycle" risk. Simulate many distinct client IDs hitting the API and assert the
    state store's size is bounded.
    Location: `tests/unit/api/test_admission_controller.py`

## Scoped Pytest Commands

```
pytest tests/api/ tests/unit/observability/test_obs_backpressure.py tests/unit/api/ -m "not slow"
```

If the auth/admission-control child tickets are split (per investigation.md's recommendation),
scope each independently:

```
# auth ticket
pytest tests/api/test_api_key_auth.py tests/unit/api/test_api_key_storage.py tests/api/ -m "not slow"

# admission-control ticket
pytest tests/api/test_http_admission_control.py tests/unit/api/test_admission_controller.py \
  tests/unit/observability/test_obs_backpressure.py tests/api/ -m "not slow"
```

Never `pytest tests/` — scope stays within `tests/api/`, the new `tests/unit/api/` (if created),
and `tests/unit/observability/test_obs_backpressure.py` as the one cross-subsystem regression this
ticket's mode-vocabulary reuse touches.

## Anti-Drift Test Guards

- **`test_pressure_mode_rate_limits_per_client_not_globally`** (item 7) is itself the primary
  anti-drift guard for this entire ticket: it is the one test that would fail if implementation
  quietly reverted to a simpler global rate limiter instead of the ticket's actual per-client
  requirement.
- **`test_admission_mode_recovery_requires_dwell_and_confidence_window`** (item 10) catches drift
  toward a naive instant-recovery implementation that would flap between modes under bursty
  traffic — the exact failure mode D23 §L's hysteresis requirement exists to prevent.
  `tests/unit/observability/test_obs_backpressure.py` staying green is the adjacent-system guard
  confirming the *existing* `ObservabilityMode` machinery wasn't altered as a side effect of
  building the HTTP-layer extension.
- **A guard against vocabulary drift**: a test asserting the HTTP-layer mode enum's member names
  are exactly `{"NORMAL", "PRESSURE", "DEGRADED", "SURVIVAL"}` (matching `ObservabilityMode`'s
  literal values) would catch an accidental implementation using `RuntimeMode`'s
  `CONSTRAINED`-named vocabulary instead, or a third, newly-invented set of names, either of which
  would violate the ticket's own acceptance criteria while looking functionally correct.
- **`test_api_key_never_appears_in_logs_or_error_responses`** (item 5) guards against a common
  incremental-implementation drift where a debug log line temporarily added during development
  (`logger.info(f"checking key {key}")`) ships accidentally.
- **`tests/api/test_cors_config.py` staying green untouched** guards against a new middleware
  being inserted in the wrong order relative to `CORSMiddleware` (FastAPI middleware order affects
  header behavior) — a real risk when adding auth/rate-limit middleware to an existing stack.
