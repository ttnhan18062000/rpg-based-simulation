---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260823-LIVE-TEST-API-KEY-AUTH
phase: done
date: 2026-08-23
tags: [testing]
---

# TCK-20260823-LIVE-TEST-API-KEY-AUTH

## Title
Add per-client API-key auth to the live-server/WebSocket tests broken by TCK-20260823-HTTP-API-KEY-AUTH

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`TCK-20260823-HTTP-API-KEY-AUTH` (done) and its sibling `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`
(done) added mandatory per-client API-key auth (`require_api_key` / `require_api_key_header_or_query`
/ `require_api_key_ws`, chained under `require_admission*`) to every route in
`src/api/server.py::create_v2_app()` except bare `/health`. 7 pre-existing test files (9 named test
functions) spin up a real `create_v2_app()` server via `subprocess.Popen(["python3", "-m", "src",
"serve", ...])` and call REST/WebSocket endpoints with plain `requests`/`websockets` calls, never
supplying a key. A faithful local CI repro (PATH fixed to match GitHub Actions' `setup-python`
resolution) on branch `http-admission-control`, commit `1e637d6b`, confirms these now fail with
401 (REST) or HTTP 403 / WebSocket handshake rejection (WS) — not the "bare `python3` lacks
`pydantic`" subprocess-environment explanation the two done tickets' own Test Summaries gave for
this same file set (their `git stash` comparisons were run in a local dev sandbox where the bare
`python3` import error masks the auth failure entirely; under a real CI-equivalent `python3` that
has `pydantic`, the server boots fine and the tests then hit the new, intentional auth gate). Per
`docs/testing/regression_policy.md` §4's decision tree: this is an intentional, already-documented
behavior change (`docs/architecture/http_api_key_authentication.md`; parity ledger `INFRA-377`/
`INFRA-378`, both `status: verified`) — the fix is to update the tests to present a valid key, not
to weaken or bypass auth.

## Scope
- `tests/api/test_live_entity_inspection.py` (`test_live_entity_inspection`)
- `tests/api/test_live_health_api.py` (`test_live_health_api_suite`) — includes the
  `/api/v1/observability/ui` dashboard-HTML fetch, which uses the header-or-query channel
  (`require_api_key_header_or_query` / `require_admission_header_or_query`), not the strict
  header-only one.
- `tests/api/test_live_observability_status.py` (`test_live_observability_endpoints`; the sibling
  `test_live_observability_endpoints_idle` in the same file calls `LiveSnapshotProvider` directly,
  no HTTP involved — leave untouched).
- `tests/api/test_observability_websocket.py` (`test_observability_websocket_suite`) — connects to
  `/api/v1/ws/observability/events`, part of `stream.router` (`require_api_key_ws` /
  `require_admission_ws`, header-or-query channel).
- `tests/api/test_rest_parity.py` — `test_api_rest_parity`, `test_api_compression` (the file's
  `/health` check itself needs no key — the sole documented exemption — but every other call in
  both functions does).
- `tests/api/test_ws_protocol.py` — `test_ws_json_handshake`, `test_ws_msgpack_handshake` (connect
  to `/api/v1/ws`, also part of `stream.router`).
- `tests/observability/test_websocket_stream_events.py` (`test_ws_events_stream`) — connects to
  `/api/v1/ws/observe`, also part of `stream.router`.
- For each: seed the `subprocess.Popen` env with `RPG_API_KEY_HASHES=<client_id>:<sha256(raw_key)>`
  (mirroring `tests/observability/test_metrics_export.py`'s already-fixed
  `test_metrics_endpoint_integration` pattern) and attach the raw key to every call — `headers=
  {"X-API-Key": raw_key}` for strict-header routes; `X-API-Key` header or a `?key=` query param
  (either channel works) for the header-or-query and WebSocket routes.
- Confirm the fixed files pass under a `python3` that has `pydantic` importable (this repo's
  `.venv/bin/python3`, or an equivalent CI-matched interpreter) — not the bare system `python3`
  the prior tickets' local comparison used, which fails before the server (and thus auth) is ever
  reached.

## Out of Scope
- Any change to the auth/admission-control mechanism itself (`src/api/auth.py`,
  `src/api/admission_control.py`, `src/api/server.py`'s route wiring) — this ticket only makes
  pre-existing tests correctly use the mechanism that already exists and is already shipped.
- `tests/api/test_paged_logic.py` and `tests/api/test_phase27_behavior_query_api.py` — both named
  in `staging_artifacts/TCK-20260823-HTTP-API-KEY-AUTH/test_plan.md` as candidates during that
  ticket's own investigation, but neither uses the `subprocess.Popen`-live-server pattern this
  ticket fixes (one calls no HTTP surface at all; the other already uses an in-process
  `TestClient`). Not part of the request and not touched here.
- `TCK-20260823-STANDARD-DASHBOARD-AUTH-PROPAGATION`'s scope (the observability dashboard's own
  inline JS not re-attaching its presented key to its own `fetch`/WebSocket calls, and the
  unpinned `marked.min.js` CDN script) — a different, already-filed, already-scoped ticket.
- Any new parity ledger entry — no behavior changes here, and `INFRA-377`/`INFRA-378` already
  document and verify the auth/admission mechanism these tests are being updated to exercise
  correctly.
- Fixing any other pre-existing/unrelated test failure encountered incidentally while running the
  broader `tests/api/`/`tests/observability/` suites.

## Acceptance Criteria
- [x] `tests/api/test_live_entity_inspection.py::test_live_entity_inspection` passes under a
      `python3` interpreter with `pydantic` installed.
- [x] `tests/api/test_live_health_api.py::test_live_health_api_suite` passes, including its
      `/api/v1/observability/ui` fetch.
- [x] `tests/api/test_live_observability_status.py::test_live_observability_endpoints` passes
      (including its `/api/v1/control/pause` and `/api/v1/control/resume` calls).
- [x] `tests/api/test_observability_websocket.py::test_observability_websocket_suite` passes.
- [x] `tests/api/test_rest_parity.py::test_api_rest_parity` and `::test_api_compression` both pass.
- [x] `tests/api/test_ws_protocol.py::test_ws_json_handshake` and `::test_ws_msgpack_handshake`
      both pass.
- [x] `tests/observability/test_websocket_stream_events.py::test_ws_events_stream` passes.
- [x] No test in this set sends its raw API key anywhere other than the `X-API-Key` header or a
      `?key=` query param already accepted by `src/api/auth.py`'s existing dependencies (no
      mechanism change, no new bypass/backdoor).
- [x] `tests/api/test_live_observability_status.py::test_live_observability_endpoints_idle`,
      `tests/api/test_paged_logic.py`, and `tests/api/test_phase27_behavior_query_api.py` remain
      unmodified and still pass (regression guard on the Out-of-Scope boundary).

## Related Tickets
- TCK-20260823-HTTP-API-KEY-AUTH (done — introduced the auth gate that broke these tests; its own
  Test Summary mis-attributed these 9 failures to a bare-`python3`-lacks-`pydantic` subprocess
  quirk rather than the auth gate, confirmed inaccurate under a CI-matched interpreter)
- TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL (done — layered `require_admission*` on top of
  `require_api_key*`; the same valid API key satisfies both, no separate admission credential
  needed)
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC (done — grandparent epic both tickets above were split
  from)
- TCK-20260823-STANDARD-DASHBOARD-AUTH-PROPAGATION (open — sibling follow-up, different scope: the
  dashboard's own client-side JS, not these test files)

## Related Docs
- docs/architecture/http_api_key_authentication.md (the ADR describing the mechanism these tests
  must now exercise correctly — route classification table, header-or-query exemptions)
- docs/testing/regression_policy.md §4 ("Regression vs Expected Behavior Change") — this is the
  "intentional, documented behavior change → update the test" branch, not a code regression
- docs/plans/http_admission_control_epic.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260823-HTTP-API-KEY-AUTH/investigation.md, plan.md, test_plan.md (the
  test_plan.md explicitly names this same file set as a known, deferred gap — read first, do not
  re-derive)
- staging_artifacts/TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL/ (admission-control layering
  context)

## Related Code Areas
- tests/api/test_live_entity_inspection.py
- tests/api/test_live_health_api.py
- tests/api/test_live_observability_status.py
- tests/api/test_observability_websocket.py
- tests/api/test_rest_parity.py
- tests/api/test_ws_protocol.py
- tests/observability/test_websocket_stream_events.py
- src/api/auth.py (reference only — `require_api_key`, `require_api_key_header_or_query`,
  `require_api_key_ws`; not modified)
- src/api/admission_control.py (reference only — confirms a valid API key alone clears
  `require_admission*` too, under normal test-volume request counts; not modified)
- src/api/server.py (reference only — route-to-dependency wiring table; not modified)
- tests/observability/test_metrics_export.py (reference pattern — `test_metrics_endpoint_integration`
  already fixed by TCK-20260823-HTTP-API-KEY-AUTH with the exact subprocess-env-plus-header
  pattern this ticket replicates)
- tests/api/test_api_key_auth.py (reference — existing in-process auth test suite; not modified)

## Assumptions / Open Questions
- `layer: testing` chosen over `engine`/`observability` since every changed file is test
  infrastructure and no production code changes; if reviewers consider this an `observability`-layer
  fix instead (all 7 files exercise observability/live endpoints), that would also be defensible —
  flagging the choice rather than treating it as settled.
- Assumes the admission-control token bucket (30 capacity, 3/s refill,
  `src/api/admission_control.py`) will not be exhausted by any single test's request volume once a
  valid key is supplied — each of the 9 test functions issues well under 30 requests to any one
  route in its own run. If a specific test's retry/polling loop turns out to issue enough rapid
  calls to trip `SURVIVAL` mode (HTTP 429 / WS close 1013), that would need handling during
  Implement, not assumed away here.
- Assumes a `pydantic`-capable `python3` (this worktree's `.venv/bin/python3` or CI's
  `setup-python`-resolved interpreter) is available to actually prove these tests pass — the
  original tickets' own local `python3` lacked it, which is why their diagnosis differed from the
  CI-matched repro this ticket is based on.

## Implementation Notes
Applied the `tests/observability/test_metrics_export.py::test_metrics_endpoint_integration`
pattern (seed `RPG_API_KEY_HASHES=<client_id>:<sha256(raw_key)>` into the `subprocess.Popen` env,
send the raw key back on every call) to all 7 files/9 test functions named in Scope. Each file got
its own module-level `_TEST_CLIENT_ID` / `_TEST_RAW_KEY` / `_TEST_KEY_HASH` triple (distinct per
file, matching the existing `test_metrics_export.py` convention) rather than a shared constant, to
keep each test's server subprocess independently keyed.

- REST calls (`requests.get`/`requests.post`): added `headers={"X-API-Key": raw_key}` to every
  call except the one documented exemption (`/health` in `test_rest_parity.py::test_api_rest_parity`).
- `test_live_health_api.py`'s `/api/v1/observability/ui` fetch and its two redirect checks
  (`/observability/ui`, `/api/v1/observability/live/ui`) use `require_api_key_header_or_query` —
  confirmed via `src/api/server.py` route wiring that both redirect routes also carry that
  dependency (not just the terminal `ui` route), so all three needed the header too.
- WebSocket calls: used `websockets.connect(..., additional_headers={"X-API-Key": raw_key})`
  (websockets 16.0's `connect()` supports `additional_headers`) rather than the `?key=` query-param
  channel suggested as an alternative in Scope. Reason: `src/api/ws/stream.py`'s
  `/ws/observability/events` handler (`test_observability_websocket.py`) does its own domain-level
  query-param whitelist check (`allowed_keys = {"severity_min", "entity_id", "category",
  "event_category", "event_type", "region_id", "quest_id"}`) independent of FastAPI's own query
  parsing for the auth dependency — `key` is not in that whitelist, so attaching the API key via
  `?key=` would have tripped the route's own "Unsupported query parameter: key" rejection and
  broken the exact "reject unknown params" sub-test this same file verifies. The header channel
  avoids that collision entirely and is accepted identically by
  `require_api_key_ws`/`require_admission_ws` (same `x_api_key or key` fallback), so it was used
  uniformly across all WebSocket routes for consistency, not only the one route that required it.
- `/api/v1/ws` (`test_ws_protocol.py`) and `/api/v1/ws/observe`
  (`test_websocket_stream_events.py`) have no such domain-level whitelist, so the header channel
  there is a stylistic consistency choice, not a correctness requirement.
- Ran under `.venv/bin/python3` (this worktree has no local `.venv`; the checked-out repo's
  `/home/u24desktop/Working/rpg-based-simulation/.venv` is the `pydantic`-capable interpreter) with
  that path prepended to `PATH` so the tests' own literal `["python3", "-m", "src", "serve", ...]`
  subprocess commands resolve to it, matching CI's `setup-python`-resolved interpreter per the
  ticket's Assumptions.

No production code was touched; `src/api/auth.py`, `src/api/admission_control.py`, and
`src/api/server.py` route wiring were read-only references, exactly as scoped.

Also edited `docs/testing/regression_policy.md` (§3, "Soft Monitors" table, `Live observability
tests` row) during Document-Update: that row generically classified any failure of
`tests/api/test_live_health_api.py`/`tests/api/test_live_observability_status.py` as
"environment-dependent... deployment issues, not code regressions" — the exact framing that let
`TCK-20260823-HTTP-API-KEY-AUTH` and `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`'s own Test
Summaries misdiagnose these same 401/403 failures as a bare-`python3`/pydantic subprocess quirk
instead of the real auth-gate cause this ticket fixes. Added a carve-out clause to that row: a
401/403 on these tests means the subprocess server env is missing a valid `RPG_API_KEY_HASHES`
entry (a test-config gap, cross-referencing `docs/architecture/http_api_key_authentication.md`),
not a deployment issue — and noted this exact file set was already misdiagnosed twice before this
ticket fixed it. Not a scope change: this doc row was actively contributing to the same
misdiagnosis pattern this ticket exists to correct, so leaving it unedited would have left the
next 401/403 on these tests vulnerable to the identical mistake.

## Test Summary
All 9 named test functions across the 7 in-scope files pass under
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (pydantic-capable):
- `tests/api/test_live_entity_inspection.py::test_live_entity_inspection` — PASSED
- `tests/api/test_live_health_api.py::test_live_health_api_suite` — PASSED
- `tests/api/test_live_observability_status.py::test_live_observability_endpoints` — PASSED
- `tests/api/test_observability_websocket.py::test_observability_websocket_suite` — PASSED
- `tests/api/test_rest_parity.py::test_api_rest_parity` — PASSED
- `tests/api/test_rest_parity.py::test_api_compression` — PASSED
- `tests/api/test_ws_protocol.py::test_ws_json_handshake` — PASSED
- `tests/api/test_ws_protocol.py::test_ws_msgpack_handshake` — PASSED
- `tests/observability/test_websocket_stream_events.py::test_ws_events_stream` — PASSED

Regression guard (unmodified, out-of-scope files/functions) also re-run and confirmed passing:
`tests/api/test_live_observability_status.py::test_live_observability_endpoints_idle`,
`tests/api/test_paged_logic.py::test_api_paged`, all 8 functions in
`tests/api/test_phase27_behavior_query_api.py`, and all 5 functions in
`tests/observability/test_metrics_export.py` (including the already-fixed
`test_metrics_endpoint_integration` reference pattern).

## Files Changed
- tests/api/test_live_entity_inspection.py
- tests/api/test_live_health_api.py
- tests/api/test_live_observability_status.py
- tests/api/test_observability_websocket.py
- tests/api/test_rest_parity.py
- tests/api/test_ws_protocol.py
- tests/observability/test_websocket_stream_events.py
- docs/testing/regression_policy.md (§3 Soft Monitors table — corrected the "Live observability
  tests" row's Reason for Soft Status to stop attributing a 401/403 to generic
  environment-dependence; see Implementation Notes)
- tickets/inprogress/TCK-20260823-LIVE-TEST-API-KEY-AUTH.md (this file — Implementation Notes,
  Test Summary, Files Changed, Completion Summary, Status, Acceptance Criteria)

## Completion Summary
Updated the 7 pre-existing live-server/WebSocket test files (9 test functions) broken by
`TCK-20260823-HTTP-API-KEY-AUTH`'s mandatory API-key auth gate: each subprocess-spawned server now
gets a seeded `RPG_API_KEY_HASHES` env var, and every REST/WebSocket call in those tests now
presents the matching raw key via the `X-API-Key` header (WebSocket routes use
`additional_headers` rather than the `?key=` query-param alternative, to avoid colliding with one
route's own unrelated query-param whitelist check). All 9 target test functions pass under a
pydantic-capable interpreter, and all named regression-guard tests (the untouched sibling
function/files) still pass. No production code changed — this is a test-only fix matching already
shipped, already-intentional auth behavior; `behavior_changed=false`.
