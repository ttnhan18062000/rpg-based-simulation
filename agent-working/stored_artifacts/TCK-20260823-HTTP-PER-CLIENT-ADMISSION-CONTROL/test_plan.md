---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL
artifact_type: test_plan
tags: [architecture, observability, api-design]
---

# Test Plan — TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL

## Regression Surface

**Unit / observability:**
- `tests/unit/observability/test_obs_backpressure.py` — the existing `ObservabilityMode`/
  `ObservabilityController`/`EventRecorder` suite (INFRA-199, P1). Confirmed by direct read: every
  test imports `ObservabilityController`/`ObservabilityMode`/`EventRecorder` from
  `src.observability.event_recorder` and exercises them directly — no seam this ticket could widen
  unless `event_recorder.py` itself is edited (Out of Scope). Stays green by construction if this
  ticket only imports and instantiates `ObservabilityController` per-client without modifying the
  module; must be re-run regardless to make that claim honest rather than assumed.

**API / auth (this ticket's own dependency, and its adjacent regression surface):**
- `tests/api/test_api_key_auth.py` — all 14 tests, most importantly
  `test_only_dashboard_and_websocket_routes_use_weaker_auth_channel` (route-table introspection by
  `dependant.dependencies` name) and every 401/200 status assertion. Adding an
  `Depends(require_admission)` entry to existing `dependencies=[...]` lists changes route
  dependant metadata — this test's set-equality assertions on `found_weak_paths`/
  `found_strict_paths` must be re-verified to confirm the new dependency doesn't accidentally
  register under a name colliding with `require_api_key`/`require_api_key_header_or_query`/
  `require_api_key_ws` in the `dep_names` set comprehension (it won't, since it's a distinct
  function name, but this is exactly the kind of introspection-based test that would actually
  catch a wiring mistake, unlike a source-reading review).
- `tests/api/test_cors_config.py`, `tests/api/test_health_liveness.py` — must stay green
  unmodified; both only ever hit `/health` (unauthenticated, and — per this ticket's own Scope,
  admission control should also exempt `/health` the same way auth does, since it is a liveness
  probe with no per-client identity to key on).
- `tests/api/test_scenario_runtime_api.py` — the sibling ticket's fixture already seeds
  `api_key_hashes` and a default `X-API-Key` header; if this ticket's admission-control default
  (fresh client, first request) is permissive (NORMAL mode, full throughput), this suite's ~14
  assertions need no changes. If any admission-control default is *not* permissive-by-default for
  a brand-new client, this suite becomes an unintended regression surface — flagged as an
  implementation constraint for Plan (a first-ever request from any client must not be throttled;
  NORMAL is the correct starting mode for an unseen client, mirroring
  `ObservabilityController`'s/`ResourceGovernor`'s own zero-history defaults).
- `tests/observability/test_metrics_export.py::test_metrics_endpoint_integration` — subprocess
  test hitting `/metrics` with a seeded env key; single request per test run, should stay well
  under any reasonable per-client rate threshold, but confirm Plan's chosen default threshold
  doesn't accidentally throttle a single-request smoke test.

**Engine / governor (read-only precedent, not touched, but confirm no accidental coupling):**
- No test run required against `src/engine/governor.py` or
  `src/config/profiles.py`'s existing profile-construction tests, since Out of Scope forbids
  modifying `ResourceGovernor`/`RuntimeProfile`'s existing fields — but if Plan adds new
  `RuntimeProfile` fields (e.g. TTL/max-entries knobs), `tests/unit/config/` (or wherever
  `RuntimeProfile` construction is tested — confirm exact path at Plan time) becomes regression
  surface for "existing profile constructors still build with the new field's default."

## New Tests Required

All new tests live in a new `tests/api/test_admission_control.py`, following
`tests/api/test_api_key_auth.py`'s established conventions directly: real in-process `TestClient`
built from `create_v2_app(_make_profile(...))`, `hashlib.sha256`-derived test keys, real response
status/header assertions (never mocking the FastAPI dependency chain itself), and the same
`dependant.dependencies`-introspection technique for anti-drift route-coverage guards.

- **`test_admission_control_mode_vocabulary_matches_observability`** — unit. Verifies the
  admission-control mode enum/class exposes exactly `NORMAL`/`PRESSURE`/`DEGRADED`/`SURVIVAL`
  (string values, not `RuntimeMode`'s `CONSTRAINED` or any invented name). Lives in
  `tests/api/test_admission_control.py`.
- **`test_first_request_from_new_client_is_admitted`** — integration. A brand-new client_id's
  very first request is NORMAL/admitted (200), not throttled by default. `tests/api/
  test_admission_control.py`.
- **`test_escalation_is_immediate_on_pressure_signal`** — unit/integration (whichever layer Plan
  exposes for direct signal injection — e.g. driving the per-client rate signal above the
  PRESSURE threshold via repeated same-client requests, or a testable seam analogous to
  `_set_queue_fill` in `test_obs_backpressure.py`). Verifies mode escalates on the very next
  evaluation once the indicated mode increases — no dwell/confidence gating on the way up, mirroring
  `ResourceGovernor.evaluate()`'s "Escalation Rule: Immediate." `tests/api/
  test_admission_control.py`.
- **`test_recovery_is_gated_by_dwell_and_confidence`** — unit/integration. Verifies that once
  escalated, mode does NOT step down until both `dwell_time_ticks`-worth of per-client evaluations
  have elapsed AND `confidence_window_ticks` consecutive good samples are observed — mirroring
  `_can_recover()`'s two-gate structure. Include a sub-case confirming recovery steps down exactly
  one mode level at a time (e.g. SURVIVAL never jumps directly to NORMAL even if signal drops to
  zero). `tests/api/test_admission_control.py`.
- **`test_per_client_state_is_isolated`** — integration. Two distinct clients (both valid,
  distinct `X-API-Key` values resolving to distinct `client_id`s): drive client A into
  PRESSURE/DEGRADED via repeated requests; confirm client B, making its own requests concurrently
  or immediately after, is unaffected (still NORMAL, still 200) — this is the ticket's own AC #6
  ("at least 2 distinct simulated clients, one throttled, one unaffected"), and the core
  correctness property distinguishing this from the parent `ObservabilityMode`'s single global
  instance. `tests/api/test_admission_control.py`.
- **`test_survival_mode_sheds_or_rejects_requests`** — integration. Once a client is driven to
  SURVIVAL, confirm the ticket's chosen shedding behavior (429 Too Many Requests, or whatever
  status Plan specifies — must be decided and asserted explicitly, not left implicit) is applied
  to that client's further requests. `tests/api/test_admission_control.py`.
- **`test_idle_client_entry_is_evicted_after_ttl`** — unit. Directly exercises the per-client state
  store (module-level dict or whatever container Plan lands on): seed an entry, advance/mock the
  clock (or call the prune function directly with an injected `current_time`, mirroring
  `AlertDeduplicator.prune(current_time)`'s testable signature) past the idle-TTL threshold, assert
  the entry is gone after the next prune pass. `tests/api/test_admission_control.py`.
- **`test_max_entries_cap_evicts_least_recently_active`** — unit. Directly exercises the
  bounded-state container: fill it to the configured max-entries cap with distinct client_ids
  spaced by simulated activity, insert one more, assert the least-recently-active entry (not an
  arbitrary one) is evicted — verifying the LRU backstop, not just the idle-TTL path.
  `tests/api/test_admission_control.py`.
- **`test_eviction_does_not_lose_active_clients`** — unit/integration. A client with ongoing
  (non-idle) activity is never evicted by either the idle-TTL or max-entries mechanism while
  actively making requests, even as other idle clients churn through the same bounded store —
  guards against an eviction bug that punishes a legitimate heavy user. `tests/api/
  test_admission_control.py`.
- **`test_admission_status_accessor_shape`** — unit. Mirrors `test_status_initial_state`/
  `test_status_reflects_current_mode` from `test_obs_backpressure.py`: the new
  `admission_status()`-equivalent (scoped per-client, or accepting a `client_id`, per Plan's exact
  signature) returns a dict shaped analogously to `observability_status()` (mode +
  ticket-mandated fields), for at least one seeded client.
- **`test_reset_admission_mode_clears_state`** — unit. Mirrors `test_reset_mode_clears_state`:
  confirms the test-only reset accessor clears a given client's (or all clients') mode/dwell/
  confidence state back to NORMAL — needed for test isolation across this new file's own test
  functions, exactly as `EventRecorder.reset_mode()` is needed across `test_obs_backpressure.py`.
- **`test_admission_dependency_requires_resolved_client_identity`** — architecture guard. Confirms
  (via `app.routes[i].dependant.dependencies` introspection, `test_api_key_auth.py`'s established
  technique) that the admission-control dependency is declared as a parameter-chain dependent on
  `require_api_key`/`require_api_key_header_or_query`/`require_api_key_ws` (i.e., appears alongside
  or after the resolved-identity dependency in the dependant graph, never standalone reaching for
  its own header/query parsing) — guards against a future refactor accidentally duplicating
  identity-resolution logic instead of composing with `src/api/auth.py`'s existing functions.
- **`test_admission_control_covers_every_authenticated_route`** — architecture guard, same
  introspection technique. Confirms every route carrying `require_api_key`/
  `require_api_key_header_or_query`/`require_api_key_ws` in its `dependant.dependencies` ALSO
  carries the admission-control dependency, and `/health` (the sole auth exemption) is also the
  sole admission-control exemption — guards against a route being added to `server.py` in the
  future with auth but not admission control, or vice versa.
- **`test_admission_control_does_not_reach_into_governor_internals`** — architecture guard (static,
  not runtime). `grep`/`ast`-based check (or a simple import-graph assertion) that the new
  admission-control module does not import from `src.engine.governor` or
  `src.engine.phase_governor` — enforcing the ticket's own Out-of-Scope module-boundary rule with a
  real, automated check rather than only a code-review convention. Lives alongside the new module's
  own tests or in a shared architecture-guard test file if this repo has one (confirm at Plan time).

## Scoped Pytest Commands

```
pytest tests/api/ tests/unit/observability/test_obs_backpressure.py tests/observability/test_metrics_export.py -m "not slow" -v
```

This scopes to: the new admission-control test file, the full existing `tests/api/` auth/CORS/
health/scenario-runtime regression surface, the `ObservabilityMode` regression suite this ticket's
design reuses the pattern (and possibly the class) from, and the one subprocess-level integration
test that exercises the full CLI->env->`ConfigLoader`->`create_v2_app` chain end to end (relevant
if Plan adds new `RuntimeProfile` fields for TTL/cap tuning, mirroring `api_key_hashes`'s own
env-var-seedable pattern).

If Plan adds new `RuntimeProfile` fields, additionally run whichever suite covers
`RuntimeProfile`/`ConfigLoader` construction directly (path to be confirmed at Plan time by
locating the sibling ticket's own `test_config_loader_env_var_seeds_api_keys`-equivalent test
file) to confirm the four existing `PROD_*` profile constructors still build with the new
field(s)' defaults.

Never: `pytest tests/` (unscoped).

## Anti-Drift Test Guards

- `test_only_dashboard_and_websocket_routes_use_weaker_auth_channel` (existing,
  `tests/api/test_api_key_auth.py`) must be re-run and stay green unmodified after this ticket's
  wiring changes — confirms admission control's dependency additions don't accidentally alter
  which routes use the weaker auth channel.
- `test_admission_control_covers_every_authenticated_route` (new, above) — the primary structural
  guard against silent scope drift: any future route added to `server.py` with auth but no
  admission control (or the reverse) fails this test immediately, rather than being discovered as
  a production gap.
- `test_admission_control_does_not_reach_into_governor_internals` (new, above) — the structural
  guard against the Anti-Drift Hazard of the API layer reaching into `src/engine/governor.py`'s
  internals directly, since that violation would otherwise only be caught by manual code review.
- `test_admission_control_mode_vocabulary_matches_observability` (new, above) — guards against a
  future edit silently renaming a mode to `RuntimeMode`'s `CONSTRAINED` or inventing a third
  vocabulary (`EMERGENCY`, per the source docs' own drafting inconsistency the parent investigation
  flagged).
- All of `tests/unit/observability/test_obs_backpressure.py` re-run unmodified — the direct,
  automated confirmation (not just a code-review claim) that this ticket's implementation, however
  it reuses `ObservabilityController`'s pattern or class, never required editing
  `src/observability/event_recorder.py` itself.
- `test_per_client_state_is_isolated` (new, above) doubles as an anti-drift guard against the
  single-biggest regression risk specific to this ticket: silently sharing mutable mode state
  across clients (e.g. a module-level singleton mode variable instead of a per-client dict) would
  make this test fail immediately, since client B's requests would start reflecting client A's
  escalated mode.
