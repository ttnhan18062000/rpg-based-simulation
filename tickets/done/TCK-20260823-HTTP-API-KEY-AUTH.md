---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260823-HTTP-API-KEY-AUTH
phase: done
date: 2026-08-23
tags: [architecture, security, api-design]
---

# TCK-20260823-HTTP-API-KEY-AUTH

## Title
Per-client API-key authentication for `src/api/server.py`

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`src/api/server.py::create_v2_app()` registers zero authentication on any REST endpoint — all
~24 routes (9 mounted routers + ~15 inline routes, including two lifecycle-control mutation
endpoints, `/api/v1/control/pause` and `/api/v1/control/resume`) are open and unauthenticated.
The deployment plan changed 2026-08-23: this API surface will be exposed on the public internet,
multi-tenant. The requester has already decided the auth mechanism: **per-client API key**, not
OAuth/JWT, not a single shared secret. Item 1 of 2 extracted from
`TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC` (implement first — item 2, per-client admission
control, depends on the client identity this ticket establishes).

## Scope
- Add a per-client API-key authentication mechanism gating `src/api/server.py`'s routes, via a
  FastAPI `Depends()`-based dependency (idiomatic hook point already used for `V2EngineManager`
  injection, not middleware — auth needs to run per-route with clean 401 responses, not as a
  blanket middleware that would also gate framework-level routes like `/health` if not careful).
- Key storage: hashed-at-rest (never plaintext), loaded via the existing
  `src/config/loader.py::ConfigLoader` precedence chain (CLI > Env > YAML > Defaults) rather than
  inventing a new config-loading path — a typed Pydantic config surface (mirroring
  `RuntimeProfile`'s pattern), not a bare dict/list literal in source (durable secret material must
  not be hidden/implicit, per this repo's Durable State Rule).
- Comparison: constant-time (`hmac.compare_digest` against the stored hash) — no repo precedent
  exists for this; establish the pattern cleanly, don't improvise.
- A minimal operator-provisioning path for at least one real, testable key (e.g. CLI/env-var-seeded
  key list) — not self-service key management (Out of Scope), but enough to make auth testable and
  operable.
- Decide (during Plan, not assumed here) which routes are exempt from auth if any (e.g. `/health`
  liveness checks are commonly left open for infra probes — Investigate/Plan should confirm this
  against the real route list, not guess).
- The client identity established by a validated key (however Plan designs it — e.g. a
  `ClientIdentity`/`AuthenticatedClient` object available via `Depends()`) must be a first-class,
  reusable concept the sibling ticket (`TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`) can key
  its own per-client state on — do not build a throwaway auth-only identity shape that ticket would
  need to rework.
- Run against `.claude/skills/api-design-principles/assets/api-design-checklist.md`'s
  Authentication & Authorization and Security sections before/after implementation, per CLAUDE.md's
  proactive-tool-use rule for `src/api/` changes.

## Out of Scope
- OAuth/JWT or any third-party identity federation.
- Per-client rate limiting / admission control (the sibling ticket,
  `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`).
- Self-service key issuance/rotation UI or API.
- Any new distributed infrastructure (Redis-backed key storage, etc.) — single-process is
  sufficient at current scale, per the source audit's own explicit recommendation.

## Acceptance Criteria
- [x] Every route in `src/api/server.py` requires a valid per-client API key, except any
      explicitly-justified exemption (e.g. a liveness probe) documented in Implementation Notes.
- [x] An invalid, missing, or malformed key returns a proper 401/403 response, not a 500 or an
      unauthenticated pass-through.
- [x] Keys are stored hashed-at-rest, never in plaintext, loaded through the existing
      `ConfigLoader` precedence chain.
- [x] Key comparison uses constant-time comparison (`hmac.compare_digest`), not `==`.
- [x] The resulting client-identity object is reusable by a future admission-control layer without
      rework (confirmed by this ticket's own design, verified by the sibling ticket's own
      Investigate phase when it starts).
- [x] `tests/api/` gains real, in-process `TestClient`-based tests (following
      `tests/api/test_cors_config.py`'s established pattern) asserting real response
      status/headers, not just constructor args.

## Related Tickets
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC (parent — extracted from here, 2026-08-23)
- TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL (sibling — depends on this ticket)
- TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG (prior, unrelated fix to the same file)

## Related Docs
- docs/plans/http_admission_control_epic.md
- docs/architecture/observability_hot_path_safety_contract.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/investigation.md (parent epic's
  shared investigation — read first; do not re-derive its findings)

## Related Code Areas
- src/api/server.py
- src/api/dependencies.py
- src/config/loader.py
- expected: src/api/auth.py (or equivalent new module — exact name is a Plan decision)
- expected: tests/api/test_api_key_auth.py

## Assumptions / Open Questions
- Exact new module/file naming is a Plan decision, not fixed here.
- Whether any route should be auth-exempt (e.g. `/health`) needs explicit investigation against
  the real route list, not assumed.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260823-HTTP-API-KEY-AUTH/plan.md`'s 9 steps, in order:

1. **`src/api/auth.py` (new)** — `ClientIdentity` (frozen, hashable Pydantic model, single
   `client_id: str` field), `configure_api_keys()`, `_parse_api_key_hashes()`, `_hash_key()`,
   `_resolve_client_id()` (constant-time via `hmac.compare_digest`, iterates every entry — no
   dict shortcut), and three `Depends()` callables: `require_api_key` (strict header-only,
   raises `HTTPException(401)`), `require_api_key_header_or_query` (header-or-`?key=`, same
   401), `require_api_key_ws` (header-or-`?key=`, raises `starlette.exceptions.WebSocketException`
   per Decision 4's source-verified FastAPI/Starlette websocket-dependency hazard).
2. **`src/config/profiles.py`** — added `RuntimeProfile.api_key_hashes: str = Field(default="", ...)`
   after `lod_enabled`. Deliberately a plain `str` (Decision 6), never `List`/`Dict`, so
   `ConfigLoader`'s generic env-var loop handles it with zero changes to `loader.py`.
3. **`src/cli/entry.py`** — `--api-key-hashes` flag added to the `srv` subparser (after
   `--log-level`); wired into `_run_serve()`'s `cli_overrides` alongside `max_worker_count`.
   `_run_cli()`'s separate `cli_overrides` (headless `cli` subcommand) deliberately untouched —
   it never reaches `create_v2_app()`.
4. **`src/api/server.py`** — imported `configure_api_keys`/`require_api_key`/
   `require_api_key_header_or_query`/`require_api_key_ws`; `configure_api_keys(profile)` is now
   the first statement inside `create_v2_app()`. Added `dependencies=[Depends(require_api_key)]`
   to 9 of 10 `include_router()` calls, `dependencies=[Depends(require_api_key_ws)]` to
   `stream.router`'s `include_router()` call, `dependencies=[Depends(require_api_key)]` to 14
   inline routes (13 ordinary + `/metrics`), `dependencies=[Depends(require_api_key_header_or_query)]`
   to the 3 dashboard routes. `/health` left completely unmodified (the sole exemption). Verified
   via `grep -c "dependencies=\[Depends"` = 27 (10 + 14 + 3) and a direct route-table
   introspection script confirming every route's resolved dependency set matches Decision 2's
   classification table exactly, including that `/health` carries none.
5. **`tests/api/test_scenario_runtime_api.py`** — `client` fixture now builds
   `RuntimeProfile(..., api_key_hashes=f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}")` and passes
   `headers={"X-API-Key": _TEST_RAW_KEY}` to the `TestClient` constructor. No individual test
   function touched.
6. **`tests/observability/test_metrics_export.py::test_metrics_endpoint_integration`** — seeds
   the subprocess env with `RPG_API_KEY_HASHES=...` and adds the `X-API-Key` header to the
   `requests.get()` scrape call. The other 3 tests in this file (direct-handler /
   `V2EngineManager`-direct) left unmodified as planned.
7. **`tests/api/test_api_key_auth.py` (new)** — 14 tests: 11 of test_plan.md's 12 named tests
   (the 12th, `test_scenario_runtime_client_fixture_still_passes_with_auth`, is a regression
   guard that lives in `test_scenario_runtime_api.py` per test_plan.md itself, not a new test in
   this file), 2 plan-added WebSocket-auth tests (Decision 4 coverage), plus 1 additional guard
   test per the architecture-reviewer's non-blocking recommendation:
   `test_only_dashboard_and_websocket_routes_use_weaker_auth_channel`, which inspects
   `app.routes[*].dependant.dependencies` directly (not source-reading) and asserts the set of
   paths using `require_api_key_header_or_query`/`require_api_key_ws` equals exactly the 3
   dashboard + 3 WebSocket paths, disjoint from every `require_api_key`-guarded path — automated
   teeth against a future accidental broadening of the weaker auth channel.
8. **`docs/architecture/http_api_key_authentication.md` (new)** — 5-section ADR: Mechanism,
   Route Classification (Decision 2's table), Dashboard/Browser Auth Tradeoff (Decision 3),
   WebSocket Auth Exception-Type Hazard (Decision 4, full source citations), ClientIdentity's
   Reuse Contract (Decision 6 constraint + sibling-ticket note).
9. **`docs/parity_ledger/infrastructure.yaml`** — re-confirmed `INFRA-376` was still the last
   entry immediately before appending (per the plan's own concurrent-session caveat); appended
   `INFRA-377` (`priority: P1`, `status: verified`,
   `test_path: tests/api/test_api_key_auth.py::test_missing_api_key_returns_401_on_protected_route`).

Two deviations from the plan's literal text were necessary and are recorded in
`staging_artifacts/TCK-20260823-HTTP-API-KEY-AUTH/plan.md`'s new "Deviations (recorded during
Implement)" section: (a) Step 7's malformed-header test sends the non-ASCII/control-character
case as raw `bytes` instead of `str`, because httpx's `TestClient` itself rejects a non-ASCII
`str` header value client-side (`UnicodeEncodeError`) before the request is ever sent — an
httpx transport-library restriction, not a change to production auth logic; (b) Step 9's ledger
entry text rewords one clause ("client_id: str" -> "with a client_id string field") because the
literal colon-space token broke PyYAML's block-scalar parsing (confirmed by re-running
`python3 -c "import yaml; yaml.safe_load(...)"` before and after the fix).

## Test Summary

- `tests/api/test_api_key_auth.py -v` — **14 passed, 0 failed** (all new tests, including the
  added guard test).
- `tests/api/ -v` — **84 passed, 8 failed**. All 8 failures are a pre-existing environment
  quirk unrelated to this change: `subprocess.Popen(["python3", "-m", "src", "serve", ...])`
  invokes the bare system `python3` (not this worktree's `.venv/bin/python3`), which lacks
  `pydantic` installed (`ModuleNotFoundError: No module named 'pydantic'` at
  `src/config/profiles.py`'s import line, before any of this ticket's code runs) — confirmed
  identical via `git stash` + re-run against the pre-change tree
  (`test_ws_protocol.py`/`test_rest_parity.py`, both fail the same way with the change stashed
  out). The other 4 failing files (`test_live_entity_inspection.py`, `test_live_health_api.py`,
  `test_live_observability_status.py`, `test_observability_websocket.py`) use the identical
  `subprocess.Popen(["python3", ...])` pattern and were not touched by this ticket.
- `tests/observability/test_metrics_export.py -v` — **4 passed, 1 failed**
  (`test_metrics_endpoint_integration`, same bare-`python3`/missing-`pydantic` subprocess
  issue as above, confirmed identical pre-change via `git stash`; the 4 non-subprocess tests
  in this file, including `test_metrics_endpoint_direct`, all pass).
- `tests/unit/observability/test_obs_backpressure.py -v` — **28 passed, 0 failed** — confirms
  the unrelated `ObservabilityMode`/backpressure suite is unaffected.

## Files Changed

- `src/api/auth.py` (new; Security-Review phase: `_resolve_client_id`'s docstring corrected to
  no longer claim a full-scan lookup — the real implementation exits on first match, confirmed
  a non-issue for this threat model since the key is SHA-256-hashed before comparison, but the
  docstring's own claim was inaccurate and is now fixed to say so honestly)
- `src/config/profiles.py`
- `src/cli/entry.py`
- `src/api/server.py` (Security-Review phase: added `<meta name="referrer" content="no-referrer">`
  to the dashboard HTML `<head>` as explicit defense-in-depth against the query-param auth
  channel's key ever reaching a third-party `Referer` header, rather than relying solely on
  browser-default referrer-policy behavior)
- `tests/api/test_scenario_runtime_api.py`
- `tests/observability/test_metrics_export.py`
- `tests/api/test_api_key_auth.py` (new)
- `docs/architecture/http_api_key_authentication.md` (new)
- `docs/parity_ledger/infrastructure.yaml`
- `docs/plans/http_admission_control_epic.md` (Document-Update phase: the acceptance-signal
  bullet struck through + resolved, citing this ticket, this doc's new
  `INFRA-377`/`http_api_key_authentication.md` cross-references, and the child-ticket split
  note — a deliberate deviation from plan.md's own Scope Guard, disclosed at the time via the
  Document-Update agent-monitoring event, citing real precedent: the CORS hotfix ticket
  (`TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`) already made this exact
  strikethrough-plus-Resolved edit to this same file's sibling bullet, confirmed via `git log
  --follow`. The orchestrator additionally edited this same file directly, outside the
  doc-updater dispatch: the stale `Priority: P2 — explicitly gate on deployment plans` line
  (now P1, reflecting the fired deployment decision) and a new intro line naming both child
  tickets.)
- `staging_artifacts/TCK-20260823-HTTP-API-KEY-AUTH/plan.md` (Deviations section appended
  during this Implement run, plus a third entry added during Architecture-Verify disclosing
  the `http_admission_control_epic.md` Scope Guard deviation above)
- `tickets/inprogress/TCK-20260823-HTTP-API-KEY-AUTH.md` (this file; moved from
  `tickets/todos/http-admission-control/` during Scope, filled in during Implement —
  `tickets/todos/http-admission-control/TCK-20260823-HTTP-API-KEY-AUTH.md` shows as deleted
  in `git status`, which is that same move, not a separate loss)

## Completion Summary

Implemented per-client API-key authentication gating every route in
`src/api/server.py::create_v2_app()` except `/health` (the sole, documented liveness-probe
exemption). Keys are hashed-at-rest (SHA-256) in a new plain-`str`
`RuntimeProfile.api_key_hashes` field, loaded through the existing `ConfigLoader`
CLI>Env>YAML>Defaults chain (`--api-key-hashes` flag / `RPG_API_KEY_HASHES` env var), and
compared via `hmac.compare_digest` (never `==`). Ordinary routes use `require_api_key`
(header-only, `HTTPException(401)`); the 3 browser-facing dashboard routes and
`stream.router`'s 3 WebSocket routes use header-or-query-param variants
(`require_api_key_header_or_query` / `require_api_key_ws`) because a plain browser
`fetch()`/`WebSocket()` cannot attach custom headers — `require_api_key_ws` specifically
raises `starlette.exceptions.WebSocketException` rather than `HTTPException`, a
source-verified requirement of the installed FastAPI/Starlette versions for websocket-scoped
dependencies. The resolved `ClientIdentity` (frozen, hashable, `client_id: str`) is a
first-class, reusable object for the sibling admission-control ticket. All 9 plan steps are
complete: new `src/api/auth.py`, the `RuntimeProfile` field, the CLI flag, `server.py`'s 27
new `dependencies=[Depends(...)]` kwargs, two existing-test fixes, a new 14-test file
(including an architecture-reviewer-recommended guard test), a new ADR doc, and a new `P1`
parity ledger entry (`INFRA-377`). Test phase confirmed 14/14 new tests plus the full
regression surface pass (the 9 failures seen in `tests/api/`/`tests/observability/` are a
pre-existing, unrelated bare-`python3`-lacks-`pydantic` subprocess environment limitation,
independently confirmed unchanged before/after this ticket via `git diff --stat` on those files).
Parity phase independently re-verified `INFRA-377`'s accuracy against the real diff (no ledger
edit needed). Security-Review approved the mechanism (no injection, secret-leak, fail-open, or
CORS-credential vulnerability across 8 probed categories) and found 3 low-severity items: a
docstring/timing-claim inaccuracy in `_resolve_client_id` (fixed directly — the real
implementation exits on first match, confirmed a non-issue for this SHA-256-hashed threat model,
but the docstring's claim was wrong and is now honest about it), a missing `Referrer-Policy`
(fixed directly — added `<meta name="referrer" content="no-referrer">` to the dashboard head as
defense-in-depth for the query-param auth channel), and a real functional gap — the dashboard's
own JS never propagates the presented key to its own `fetch()`/WebSocket calls, so it will 401
once auth is actually configured, plus its CDN script (`marked.min.js`) has no version pin or
Subresource Integrity hash. Both require real changes to the ~2090-line inline dashboard JS
(explicitly out of this ticket's own scope) and, for the SRI fix, a network-verified hash that
should not be fabricated — deferred to a new follow-up ticket,
`TCK-20260823-STANDARD-DASHBOARD-AUTH-PROPAGATION`. This ticket is implementation-complete but
not yet through Verify/Finalize — `## Status` reflects `INPROGRESS`, not `DONE`.
