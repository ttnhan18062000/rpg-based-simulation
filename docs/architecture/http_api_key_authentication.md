---
status: active
layer: architecture
authority: P1
audience: developer
---

# HTTP API-Key Authentication

This document describes the per-client API-key authentication mechanism gating
`src/api/server.py::create_v2_app()`'s HTTP and WebSocket routes, added by
TCK-20260823-HTTP-API-KEY-AUTH. It is item 1 of 2 extracted from
`docs/plans/http_admission_control_epic.md`; item 2,
`TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`, builds per-client
rate-limiting/admission control on top of the `ClientIdentity` object this
mechanism establishes.

---

## 1. Mechanism

Authentication is implemented as FastAPI `Depends()` dependencies
(`src/api/auth.py`), not middleware — auth needs to run per-route with clean
401 responses, and must not blanket-gate framework-level routes (`/health`,
`/docs`, `/openapi.json`) the way a global middleware would unless carefully
special-cased.

- **Storage**: keys are stored hashed-at-rest, never in plaintext. Operators
  provision `RuntimeProfile.api_key_hashes`, a plain `str` of comma-separated
  `client_id:sha256hex` pairs (e.g.
  `"alice:2c26b46b...,bob:9f86d081..."`), loaded through the existing
  `ConfigLoader` precedence chain (CLI > Env > YAML > Defaults) via the
  `--api-key-hashes` CLI flag or the `RPG_API_KEY_HASHES` env var. The field
  is deliberately a bare `str`, not `List[str]`/`Dict[str, str]` — see
  Section 5.
- **Parsing**: `src/api/auth.py::configure_api_keys(profile)` is called once,
  as the first statement inside `create_v2_app()`, and parses
  `profile.api_key_hashes` into a module-level `{sha256hex: client_id}` dict
  (`_client_keys`) via `_parse_api_key_hashes()`. Malformed entries (missing
  `:`, empty client_id/hash half) are skipped with a `logger.warning` that
  logs only the entry's index, never its content — one bad config entry must
  not crash server startup, and no hash-adjacent data reaches a log line.
- **Comparison**: `_resolve_client_id(raw_key)` SHA-256-hashes the presented
  key and iterates every configured `(hash, client_id)` pair, calling
  `hmac.compare_digest(candidate_hash, stored_hash)` for each — never a dict
  `in`/`==` shortcut, which would leak timing information about which stored
  hash (if any) partially matched.
- **Identity**: a successful lookup returns `ClientIdentity` (frozen,
  hashable, `client_id: str`) via `Depends()`. See Section 5 for its reuse
  contract.
- **Failure**: an unresolved key raises `HTTPException(401)` (ordinary
  routes) or `WebSocketException(code=1008)` (WebSocket routes — see Section
  4) with the fixed, generic detail `"Invalid or missing API key."` — never
  the raw key, its hash, or any other identifying detail.

---

## 2. Route Classification

Every route in `create_v2_app()` falls into exactly one of four buckets. The
default for any new route is **protected, via `require_api_key`** — deviate
from that default only with a documented reason added to this table.

| Surface | Dependency | Reasoning |
|---|---|---|
| 9 of 10 `include_router()` calls (`history`, `search`, `behavior`, `decisions`, `scenarios`, `campaigns`, `chronicle`, `economy`, `quality_routes`) | `require_api_key` | Ordinary REST sub-routers |
| `stream.router` (`include_router()`) | `require_api_key_ws` | Contains only `@router.websocket(...)` routes — see Section 4 |
| `/health` | none (exempt) | Liveness probe; infra-orchestration caller, not a tenant client |
| `/metrics` | `require_api_key` | Sensitive operational data (gold/hard-law/entity metrics); no repo precedent for treating it as infra-only, especially once exposed on the public internet |
| 13 other inline GET/POST routes (`live/status`, `live/snapshot`, `live/entities/{id}`, `state`, `inspect`, `entities`, `entities/{id}`, `control/pause`, `control/resume`, `test/publish_event`, `live/health`, `live/stream-health`, `history/runs/{run_id}/report`) | `require_api_key` | Ordinary REST/mutation routes, including the two highest-consequence unauthenticated writes (`control/pause`, `control/resume`) |
| `/api/v1/observability/ui`, `/observability/ui`, `/api/v1/observability/live/ui` | `require_api_key_header_or_query` | Browser-facing dashboard pages — see Section 3 |

`/health` is the **sole** exemption. Do not add a second exemption without
updating this table and the accompanying parity ledger entry (`INFRA-377`).

---

## 3. Dashboard/Browser Auth Tradeoff

The 3 dashboard routes above are rendered by a plain browser navigation,
which cannot attach a custom `X-API-Key` header. `require_api_key_header_or_query`
accepts the key via that header **or** a `key` query-parameter, so the
dashboard stays operable without a header-injecting proxy/extension.

This is a real, deliberate security tradeoff, not an oversight: a key passed
via `?key=...` can be captured in server access logs, browser history, and
any intermediate proxy's request logs. It is scoped to exactly the 3
dashboard routes (plus the 3 WebSocket routes in Section 4, for the same
reason) via a **separate, narrowly-named** dependency function
(`require_api_key_header_or_query`), never reused elsewhere — so the weaker
channel cannot silently leak onto a non-dashboard route by accidental reuse.
An operator relying on the dashboard for a real public deployment should
weigh this tradeoff explicitly (e.g. restrict dashboard access at a network
layer, or accept the exposure).

---

## 4. WebSocket Auth Exception-Type Hazard

`stream.router` (backing `src/api/ws/stream.py`'s 3 `@router.websocket(...)`
routes: `/ws`, `/ws/observe`, `/ws/observability/events`) uses a dedicated
dependency, `require_api_key_ws`, which raises
`starlette.exceptions.WebSocketException` — **never** `fastapi.HTTPException`.

This is a source-verified technical requirement, not a style preference, with
the installed `fastapi==0.128.4`/`starlette==0.52.1`:

- `fastapi/routing.py`'s `get_websocket_app()` resolves dependencies
  (`solve_dependencies(request=websocket, ...)`) before the handler's own
  `await websocket.accept()` ever runs — a dependency can raise before the
  connection is accepted.
- `starlette/middleware/exceptions.py`'s `ExceptionMiddleware` registers
  **two separate** handlers: `HTTPException -> self.http_exception` and
  `WebSocketException -> self.websocket_exception`.
- `http_exception` builds a `PlainTextResponse` and calls it as an ASGI app —
  this sends `http.response.start`/`http.response.body` messages, which are
  not valid on a `scope["type"] == "websocket"` connection.
- `websocket_exception` calls `await websocket.close(code=exc.code,
  reason=exc.reason)` — the ASGI-websocket-safe close path, reached only for
  `WebSocketException`.

**A future contributor adding a new WebSocket route to this app must use
`require_api_key_ws`, not `require_api_key`.** Reusing `require_api_key` on a
websocket-scoped dependency would raise an `HTTPException` that
`ExceptionMiddleware` cannot safely convert to a clean `websocket.close()` —
do not "simplify" this back to a single shared dependency function without
re-verifying this FastAPI/Starlette exception-handling behavior first.

`require_api_key_ws` shares `_resolve_client_id`'s lookup logic and accepts
the same header-or-query channel as the dashboard dependency (Section 3) — a
browser's native `WebSocket()` constructor also cannot set custom headers, so
the same tradeoff applies for the same reason.

---

## 5. `ClientIdentity`'s Reuse Contract

`ClientIdentity` (`src/api/auth.py`) is a frozen, hashable Pydantic model
with a single field, `client_id: str`. It is a deliberately small, stable,
reusable identity object — `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`
is expected to key its own per-client rate-limiting/admission state off this
object (e.g. as a dict key or lookup identity). Its shape should not be
narrowed, and auth-only fields should not be added to it, without checking
that ticket's needs first.

`RuntimeProfile.api_key_hashes` must never become a `List[str]`/
`Dict[str, str]`-typed field. `ConfigLoader`'s env-var loop
(`src/config/loader.py:54-70`) only handles scalar field annotations and
raises an uncaught `TypeError` the moment a non-scalar-typed env var is set.
All structured parsing of the delimited format stays in `src/api/auth.py`,
never on `RuntimeProfile` itself (frozen; parsing logic does not belong in a
resource-envelope contract).
