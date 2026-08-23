---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260823-HTTP-API-KEY-AUTH
artifact_type: plan
tags: [architecture, security, api-design]
---

# Implementation Plan — TCK-20260823-HTTP-API-KEY-AUTH

## Summary

Add `src/api/auth.py`, a new module holding a frozen, hashable `ClientIdentity` model and
three `Depends()`-callables (`require_api_key`, `require_api_key_header_or_query`,
`require_api_key_ws`) that validate an incoming API key by SHA-256-hashing it and comparing
against a module-level `{sha256hex: client_id}` map via `hmac.compare_digest` (never `==`).
The map is parsed once per `create_v2_app()` call, from a new plain-`str` `RuntimeProfile`
field, `api_key_hashes`, holding comma-separated `client_id:sha256hex` pairs — loaded through
`ConfigLoader`'s existing CLI>Env>YAML>Defaults chain with zero changes needed to
`loader.py` itself (its generic env-var loop already handles any plain-`str` field), plus a
new `--api-key-hashes` CLI flag wired into `_run_serve()`'s `cli_overrides`. `server.py` wires
the dependency onto all 10 `include_router()` call sites (corrected from the ticket's/
investigation's stated "9" — direct grep confirms 10) and 17 of 18 inline routes (corrected
from "17 total" — direct grep confirms 18 inline routes; `/health` is the sole exemption, so
17 of them get gated). Three browser-facing dashboard routes and `stream.router`'s three
WebSocket routes get a header-or-query-param dependency instead of the strict header-only
one, because a plain browser `fetch()`/`WebSocket()` cannot attach a custom header — this
plan resolves that open question by choosing option (a) (query-param key as an additional
channel), with the tradeoff (keys can appear in URLs/access logs/browser history) documented
in a new `docs/architecture/http_api_key_authentication.md` ADR and the parity ledger entry.
A previously-unflagged, source-verified technical hazard is also corrected here: raising
`fastapi.HTTPException` inside a WebSocket-route dependency is not safely handled by the
installed FastAPI 0.128.4/Starlette 0.52.1 (confirmed by direct read of
`fastapi/routing.py`'s `get_websocket_app()` and `starlette/middleware/exceptions.py`'s
`ExceptionMiddleware`), so `stream.router` gets its own dependency,
`require_api_key_ws`, which raises `starlette.exceptions.WebSocketException` instead — the
one exception type that `ExceptionMiddleware` maps to a clean `websocket.close(code=...)`.
Two existing tests are fixed (a default auth header on `test_scenario_runtime_api.py`'s
`TestClient` fixture; an env-seeded key for `test_metrics_export.py`'s subprocess test), one
new test file (`tests/api/test_api_key_auth.py`) is added covering test_plan.md's 12 named
tests plus 2 plan-added WebSocket-auth tests the newly-discovered hazard requires, and one
new parity ledger entry (`INFRA-377`, `priority: P1`) is appended.

## Key Decisions

**Decision 1 — Route-count corrections (source-verified, not from investigation.md).**
`grep -n "app.include_router" src/api/server.py` returns **10** matches, not 9:
`stream.router`, `history.router`, `search.router`, `behavior.router`, `decisions.router`,
`scenarios.router`, `campaigns.router`, `chronicle.router`, `economy.router`,
`quality_routes.router` (server.py:86,89,92,95,98,101,104,107,110,113). `grep -c "^\s*@app\."
src/api/server.py` returns **18**, not 17 (server.py:118,128,134,144,154,168,175,183,192,203,
208,213,235,246,252,276,2370,2374). The ticket's Request Summary and investigation.md both
undercounted both figures by one; this plan uses the corrected counts throughout. This does
not change the mechanism (`dependencies=` at `include_router()`/route-decorator call sites),
only the enumeration every step below is checked against.

**Decision 2 — Route exemption/classification (final, ratifying investigation's
recommendation with the corrected counts).** Exactly **one** exemption: `/health`
(server.py:128). `/metrics` (server.py:118) is explicitly **not** exempt — ratifying
investigation's reasoning (no repo convention treats it as infra-only; it exposes sensitive
gold/hard-law/entity data now reachable "on the public internet, multi-tenant" per the
ticket's own Request Summary). Full classification of all 28 protected surfaces (10 routers +
18 inline routes):

| Surface | Dependency | Reasoning |
|---|---|---|
| 9 of 10 `include_router()` calls (`history`, `search`, `behavior`, `decisions`, `scenarios`, `campaigns`, `chronicle`, `economy`, `quality_routes`) | `require_api_key` | Ordinary REST sub-routers |
| `stream.router` (`include_router()`, server.py:86) | `require_api_key_ws` | Contains only `@router.websocket(...)` routes (`src/api/ws/stream.py:18,81,147`) — see Decision 4, not `require_api_key` |
| `/health` (server.py:128) | none (exempt) | Liveness probe; infra-orchestration caller, not a tenant client |
| `/metrics` (server.py:118) | `require_api_key` | Sensitive operational data, no repo precedent for treating as infra-only |
| 13 other inline GET/POST routes (`live/status`, `live/snapshot`, `live/entities/{id}`, `state`, `inspect`, `entities`, `entities/{id}`, `control/pause`, `control/resume`, `test/publish_event`, `live/health`, `live/stream-health`, `history/runs/{run_id}/report`) | `require_api_key` | Ordinary REST/mutation routes, including the two lifecycle-mutation endpoints the ticket names as the highest-consequence unauthenticated writes |
| `/api/v1/observability/ui`, `/observability/ui`, `/api/v1/observability/live/ui` (server.py:276,2370,2374) | `require_api_key_header_or_query` | Browser-facing dashboard pages — see Decision 3 |

Count check: 9 (`require_api_key` routers) + 1 (`require_api_key_ws` router) + 1 (`/metrics`)
+ 13 (other inline) + 3 (dashboard) + 1 (`/health`, exempt) = 10 routers + 18 inline routes. ✓
(Corrected during Review — Decision 2's original prose said "12," an internal off-by-one
against its own itemized list of 13 and against Step 4/Step 9, which already correctly said
13/14. See Review event log for TCK-20260823-HTTP-API-KEY-AUTH.)

**Decision 3 — Dashboard-routes auth resolution: option (a), a `key` query-parameter as an
additional auth channel, scoped ONLY to the 3 dashboard routes.** This resolves the open
question investigation.md explicitly flagged as unresolved. Reasoning: option (b) (leaving
the dashboard permanently inaccessible without a header-injecting proxy/extension) would
mean AC #1 ("every route requires a valid key... except any explicitly-justified
exemption") is technically satisfiable but produces a materially worse operator experience
for a tool this ticket's own Request Summary frames as needing to stay usable ("operable"),
for zero corresponding security benefit — the AC requires a valid key be presented, and a
query-param key still satisfies that requirement; it does not mandate the header channel
specifically. The tradeoff (keys visible in URLs, server access logs, browser history) is
real and is documented, not hidden: (1) in `docs/architecture/http_api_key_authentication.md`
(Step 8), (2) in the new parity ledger entry's `text` field (Step 9), and (3) by keeping the
query-param dependency (`require_api_key_header_or_query`) a **separate, narrowly-named**
function from the strict `require_api_key` used everywhere else — so the weaker channel can
never silently leak onto a non-dashboard route by accidental reuse. Anti-Drift Notes below
make this explicit for the implementer and any future editor.

**Decision 4 — WebSocket routes need a THIRD dependency, `require_api_key_ws`, raising
`starlette.exceptions.WebSocketException` instead of `fastapi.HTTPException` — a
previously-unflagged technical hazard, confirmed by direct source read, not present in
investigation.md or the ticket.** `src/api/ws/stream.py` (the module backing
`stream.router`, one of the 10 `include_router()` sites) defines exactly 3 routes, all
`@router.websocket(...)` (stream.py:18 `/ws`, :81 `/ws/observe`, :147
`/ws/observability/events`) — zero HTTP routes. Applying `dependencies=[Depends(require_api_key)]`
uniformly to this router (as investigation's Anti-Drift Hazards literally instructs for "the
9"/10 routers with no exception noted) would attach an `HTTPException`-raising dependency to
a websocket-scoped route. Confirmed by direct read:
- `fastapi/routing.py:477-511` (`get_websocket_app`): dependency resolution
  (`solve_dependencies(request=websocket, ...)`, line 496) runs and can raise **before**
  `websocket.accept()` is ever called by the handler (the handler's own `await
  websocket.accept()` only runs inside `dependant.call(...)`, line 509 — never reached if a
  dependency raises).
- `starlette/middleware/exceptions.py:27-30`: `ExceptionMiddleware` registers **two separate**
  handlers — `HTTPException: self.http_exception` and `WebSocketException:
  self.websocket_exception` — not one shared handler.
- `starlette/middleware/exceptions.py:66-69` (`http_exception`): builds a `PlainTextResponse`
  and calls it as an ASGI app — this sends `http.response.start`/`http.response.body`
  messages, which are not valid on a `scope["type"] == "websocket"` ASGI connection.
- `starlette/middleware/exceptions.py:72` (`websocket_exception`): `await
  websocket.close(code=exc.code, reason=exc.reason)` — the ASGI-websocket-safe close path,
  reached only for `WebSocketException`.

Installed versions confirmed: `fastapi==0.128.4`, `starlette==0.52.1` (both from
`requirements.txt` and a direct `python3 -c "import fastapi, starlette"` check against this
worktree's `.venv`). **Fix:** `require_api_key_ws` (in `src/api/auth.py`, Step 1) is applied
to `stream.router`'s `include_router()` call instead of `require_api_key`. It shares
`_resolve_client_id`'s lookup logic and accepts the same header-or-query channel as the
dashboard dependency (Decision 3) — a browser's native `WebSocket()` constructor also cannot
set custom headers, so the same tradeoff applies for the same reason. **This requires zero
changes to `src/api/ws/stream.py`** — the dependency is wired at the `include_router()` call
site in `server.py` exactly as investigation's Anti-Drift Hazard already prescribes ("do not
touch... `src/api/ws/stream.py`... pass `dependencies=[...]` to each `include_router()` call
inside `server.py` itself"); only the *which dependency function* changes for this one router,
not the mechanism or the file touched.

**Decision 5 — Inline routes: individual `dependencies=[Depends(...)]` kwargs on each
`@app.get`/`@app.post` decorator, NOT a grouped local `APIRouter(dependencies=[...])`.**
The 18 inline route decorators are interleaved across `server.py`'s full 2378 lines with a
~2090-line inline HTML/JS string (lines 278–2367, the dashboard's `html_content` literal) —
confirmed by direct read. Converting to a grouped router would require relocating up to 17
route definitions (including one, `get_observability_ui` at line 276, that sits immediately
before the HTML blob, and two, at lines 2370/2374, that sit immediately after it) out of
their current positions into a new contiguous block — a much larger, higher-risk diff for
identical runtime behavior, and one that risks disturbing the untouched HTML content in the
process. Adding one `dependencies=[Depends(require_api_key)]` (or
`require_api_key_header_or_query` for the 3 dashboard routes) kwarg per decorator, in place,
is the minimal-footprint change with the same effect.

**Decision 6 — `RuntimeProfile.api_key_hashes: str` field; zero changes needed to
`ConfigLoader`.** Confirmed by direct read of `src/config/loader.py:54-70`: the env-var loop
iterates `RuntimeProfile.model_fields`, and for any field whose `annotation` is exactly `str`
(not a subclass wrapped in `Optional`/`List`/`Dict`), it hits the `elif issubclass(field_type,
str): base_data[field] = val` branch (loader.py:67) with no casting needed — a plain string
assignment. Since `api_key_hashes` is declared as a bare `str` (see Step 2), `RPG_API_KEY_HASHES`
already works through the existing generic loop with no new code in `loader.py`. Confirmed
the alternative (`List[str]`/`Dict[str,str]`) would hit `issubclass(field_type, str)` →
`TypeError` (uncaught — only `ValueError` is caught, loader.py:69) the moment the env var is
set — this is exactly the hazard investigation.md flagged; this plan avoids it entirely by
keeping the field a bare `str` and doing all structured parsing downstream in
`src/api/auth.py::_parse_api_key_hashes`, never on `RuntimeProfile` itself (frozen; parsing
logic does not belong in a resource-envelope contract).

**Decision 7 — Delimited format: comma-separated `client_id:sha256hex` pairs, one colon per
pair, whitespace-tolerant, malformed entries skipped with a logged warning (never raised).**
Example: `"alice:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae,bob:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"`.
Parsing splits on `,` for pairs, then `.partition(":")` per pair (client_id cannot itself
contain `:`); empty entries (trailing comma) are skipped silently; entries missing a `:` or
with an empty client_id/hash half are skipped with `logger.warning` (never the raw entry
content, to avoid any risk of a hash appearing in logs — see Security Considerations).
Skip-not-raise is deliberate: one malformed operator-supplied entry must not crash server
startup (`create_v2_app()` would abort entirely if `configure_api_keys()` raised). Default
value is `""` (parses to an empty map) — the fail-closed default: with no keys configured,
every protected route 401s for every caller, never silently opens.

**Decision 8 — Doc home: new `docs/architecture/http_api_key_authentication.md`, not
`docs/guidelines/design_patterns.md`.** Investigation offered both as options ("the same way
`WorkerManager`/`ObservabilityController` are documented... or a new `docs/architecture/`
ADR"). Direct check of `docs/guidelines/design_patterns.md`'s existing structure (`grep -n
"^## \|^### "`) shows it is organized as 6 numbered code-shape Patterns (Domain Phase Class,
Decision/Mutation Separation, Presenter Separation, Feature Pack Registration, Combat
Extension, Compile-Time Pillar Activation) plus legacy V1 patterns — none of which
`WorkerManager`/`ObservabilityController` actually appear in (`grep -rl "WorkerManager"
docs/architecture/ docs/guidelines/` finds only `docs/architecture/
kernel_concurrency_design_philosophy.md`, not `design_patterns.md`). `docs/architecture/`
already holds several freestanding, single-topic ADR-shaped docs at exactly this grain
(`observability_hot_path_safety_contract.md`, `simulation_watchdog.md`,
`kernel_concurrency_design_philosophy.md`) — a new sibling doc there is the better-fitting,
lower-risk home, and matches this ticket's own `layer: architecture`.

**Decision 9 — Parity ledger: new entry `INFRA-377`, `priority: P1`.** Next free ID
confirmed by `tail -60 docs/parity_ledger/infrastructure.yaml`: `INFRA-376` is the last entry
at plan-write time. `priority: P1` (not `P2`, unlike the recent rendering-calibration
entries `INFRA-370`-`376`) because this entry covers a live, request-path security control
gating a "public internet, multi-tenant" deployment (the ticket's own framing) — materially
higher consumption risk than diagnostic/report-only tooling, and consistent with the ticket's
own `## Priority` field (`P1`) and with `INFRA-199`'s existing `P1` precedent for another
live, request-path-adjacent behavioral contract.

## Steps

### Step 1 — Create `src/api/auth.py`

**Files:** `src/api/auth.py` (new)

**Change:** New module, public API:

```python
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Dict, Optional

from fastapi import Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import WebSocketException

from src.config.profiles import RuntimeProfile

logger = logging.getLogger(__name__)

# Sole writer: configure_api_keys(), called once per create_v2_app() invocation
# (src/api/server.py). Mirrors src/api/dependencies.py's set_x/get_x singleton
# pattern (server.py:11-14) -- same last-call-wins semantics across multiple
# create_v2_app() calls in one process as the existing _engine_manager global.
_client_keys: Dict[str, str] = {}


class ClientIdentity(BaseModel):
    """Resolved identity of an authenticated API caller. Reusable by
    TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL to key its own per-client
    state. Keep this small and stable -- do not add auth-only fields here."""
    model_config = ConfigDict(frozen=True)
    client_id: str


def configure_api_keys(profile: RuntimeProfile) -> None:
    """Parse profile.api_key_hashes into the module-level key store. Must be
    called once at create_v2_app() time, before any request is served."""
    global _client_keys
    _client_keys = _parse_api_key_hashes(profile.api_key_hashes)


def _parse_api_key_hashes(raw: str) -> Dict[str, str]:
    """'client_id:sha256hex,client_id2:sha256hex2' -> {sha256hex: client_id}.
    Malformed entries are skipped with a logged warning (never the raw entry
    content), never raised -- one bad config entry must not crash startup."""
    result: Dict[str, str] = {}
    if not raw:
        return result
    for index, entry in enumerate(raw.split(",")):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            logger.warning("Skipping malformed api_key_hashes entry at index %d (missing ':')", index)
            continue
        client_id, _, key_hash = entry.partition(":")
        client_id, key_hash = client_id.strip(), key_hash.strip()
        if not client_id or not key_hash:
            logger.warning("Skipping malformed api_key_hashes entry at index %d (empty half)", index)
            continue
        result[key_hash] = client_id
    return result


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _resolve_client_id(raw_key: str) -> Optional[str]:
    """Constant-time lookup across every configured key hash. Never raises --
    an empty/malformed raw_key simply fails to match and returns None. Iterates
    and calls hmac.compare_digest for every entry (not a dict __contains__
    shortcut) so lookup time does not vary by which entry would have matched."""
    if not raw_key:
        return None
    candidate_hash = _hash_key(raw_key)
    for stored_hash, client_id in _client_keys.items():
        if hmac.compare_digest(candidate_hash, stored_hash):
            return client_id
    return None


async def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> ClientIdentity:
    """Strict header-only auth dependency for ordinary REST routes."""
    client_id = _resolve_client_id(x_api_key or "")
    if client_id is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return ClientIdentity(client_id=client_id)


async def require_api_key_header_or_query(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    key: Optional[str] = Query(default=None),
) -> ClientIdentity:
    """Header-or-query-param auth, scoped ONLY to the 3 browser-facing dashboard
    routes (see docs/architecture/http_api_key_authentication.md, Decision 3) --
    a plain browser navigation cannot attach a custom header. Keys can appear in
    URLs/access logs/browser history via this channel; do not reuse this
    dependency on any non-dashboard route."""
    raw = x_api_key or key or ""
    client_id = _resolve_client_id(raw)
    if client_id is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return ClientIdentity(client_id=client_id)


async def require_api_key_ws(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    key: Optional[str] = Query(default=None),
) -> ClientIdentity:
    """WebSocket-scoped auth for stream.router's 3 websocket routes. MUST raise
    WebSocketException, never HTTPException -- see plan.md Decision 4 for the
    source-verified reason (fastapi/routing.py's get_websocket_app() resolves
    dependencies before websocket.accept(); starlette's ExceptionMiddleware only
    safely closes a websocket connection for WebSocketException, not
    HTTPException). Same header-or-query channel as the dashboard dependency,
    since a browser's native WebSocket() constructor also cannot set headers."""
    raw = x_api_key or key or ""
    client_id = _resolve_client_id(raw)
    if client_id is None:
        raise WebSocketException(code=1008, reason="Invalid or missing API key.")
    return ClientIdentity(client_id=client_id)
```

`ClientIdentity` is hashable automatically: pydantic v2 `frozen=True` `BaseModel`s generate
`__hash__` from their field values when all fields are themselves hashable (`client_id: str`
is), so `ClientIdentity(client_id="x")` is usable as a dict key with no extra code — confirmed
required by test_plan.md's `test_client_identity_exposes_client_id`.

**Other writers to `_client_keys`:** none besides `configure_api_keys()` — a brand-new
module-level dict, this ticket's sole author. `configure_api_keys()` is called once per
`create_v2_app()` invocation (Step 4); if `create_v2_app()` is called more than once in the
same process (e.g. multiple `TestClient` apps built in one test session, or
`test_multiple_registries_prevent_collision`-style scenarios), the later call's parsed map
wins — the same last-call-wins semantics `src/api/dependencies.py`'s existing
`set_engine_manager`/`_engine_manager` global already has (`src/api/dependencies.py:12-15`),
so this is a consistent, not a new, risk. `test_multiple_registries_prevent_collision`
(test_plan.md's Regression Surface) is unaffected regardless, since it constructs
`V2EngineManager` directly and never calls `create_v2_app()`.

**Do NOT touch:** `src/api/schemas.py` (response-shape-only module, per its own docstring —
`ClientIdentity` must not be added there), `src/api/dependencies.py` (a separate, unrelated
singleton store for the engine manager/quality hub — do not fold `_client_keys` into it).

**Verify:** `test_client_identity_exposes_client_id`, `test_keys_never_stored_or_compared_as_plaintext`
(both new, Step 7).

### Step 2 — Add `RuntimeProfile.api_key_hashes` field

**Files:** `src/config/profiles.py`

**Change:** Add, after the existing `lod_enabled` field (`src/config/profiles.py:54`, the
last field before the `@field_validator`):

```python
    # Security (HTTP API-key auth, TCK-20260823-HTTP-API-KEY-AUTH)
    api_key_hashes: str = Field(
        default="",
        description=(
            "Comma-separated 'client_id:sha256hex' pairs. Must stay a plain str -- "
            "ConfigLoader's env-var loop (src/config/loader.py:54-70) only handles "
            "scalar field types and raises an uncaught TypeError on List/Dict "
            "annotations. Parsed into a {hash: client_id} mapping by "
            "src/api/auth.py::configure_api_keys(), never on this model (frozen). "
            "Empty string means no keys configured -- every protected route then "
            "401s for every caller (fail-closed default)."
        ),
    )
```

No changes needed to `PROD_SMALL`/`PROD_DEFAULT`/`PROD_LARGE`/`PROD_STRESS`
(`src/config/profiles.py:65-139`) — the field has a default, so all four existing
constructors continue to build successfully with `api_key_hashes=""` (no keys configured),
matching every existing test that constructs these profiles without expecting auth.

**Other writers to `RuntimeProfile`:** none besides this field addition — `RuntimeProfile` is
frozen (`ConfigDict(frozen=True)`, `profiles.py:19`) and every other field is set only at
construction time by `ConfigLoader.load_profile()` (Step 3) or a direct literal
constructor call (test fixtures, `PROD_*` constants) — this new field follows the exact same
pattern as every other field, no special-casing needed.

**Do NOT touch:** `cadence: SystemCadence` or any other existing field's default/validation.

**Verify:** `test_config_loader_env_var_seeds_api_keys` (Step 7) exercises this field through
the real `ConfigLoader` env-var path end to end.

### Step 3 — `--api-key-hashes` CLI flag

**Files:** `src/cli/entry.py`

**Change:** In `_build_parser()`'s `srv` subparser block (`src/cli/entry.py:22-28`), add
after `--log-level`:

```python
    srv.add_argument(
        "--api-key-hashes", type=str, default=None,
        help="Comma-separated 'client_id:sha256hex' pairs for API-key auth "
             "(RPG_API_KEY_HASHES env var also supported)"
    )
```

In `_run_serve()` (`src/cli/entry.py:262-284`), extend `cli_overrides` (currently
`{"max_worker_count": args.workers}`, line 272-274):

```python
    cli_overrides = {
        "max_worker_count": args.workers,
        "api_key_hashes": args.api_key_hashes,
    }
```

`ConfigLoader.load_profile()`'s CLI-override step (`loader.py:82-84`) already does
`base_data.update({k: v for k, v in cli_overrides.items() if v is not None})` — the default
`None` for `--api-key-hashes` is filtered out automatically, so an operator who doesn't pass
the flag falls through to the env-var/YAML/default layers unchanged, exactly matching
`--workers`'s existing behavior.

**Other writers to `cli_overrides`:** none in this file besides `_run_serve()`'s own
assignment (`_run_cli()`'s separate `cli_overrides` dict, line 190-192, is for the headless
`cli` subcommand, which builds a `Kernel` directly and never calls `create_v2_app()` — no HTTP
auth applies there, so it is deliberately left untouched).

**Do NOT touch:** `_run_cli()`, the `cli` subparser, or any other subcommand's argument
block — only the `serve` path reaches `create_v2_app()`.

**Verify:** `test_config_loader_env_var_seeds_api_keys` (Step 7) covers the env-var path;
CLI-flag parsing itself is exercised implicitly by `_build_parser()` already being covered by
existing CLI tests (no new CLI-specific test required beyond what test_plan.md lists — the
flag is a thin `cli_overrides` passthrough with no independent logic of its own).

### Step 4 — Wire `configure_api_keys()` + dependencies into `server.py`

**Files:** `src/api/server.py`

**Change:**

1. Add import near the other `src.api.*` imports (`server.py:11-17`):
   ```python
   from src.api.auth import configure_api_keys, require_api_key, require_api_key_header_or_query, require_api_key_ws
   ```
2. As the first statement inside `create_v2_app(profile)` (`server.py:21-23`, right after the
   docstring, before `lifespan` is defined):
   ```python
   configure_api_keys(profile)
   ```
3. Add `dependencies=[Depends(require_api_key)]` to 9 of the 10 `include_router()` calls
   (`server.py:89,92,95,98,101,104,107,110,113` — `history`, `search`, `behavior`,
   `decisions`, `scenarios`, `campaigns`, `chronicle`, `economy`, `quality_routes`), e.g.:
   ```python
   app.include_router(history.router, prefix="/api/v1", dependencies=[Depends(require_api_key)])
   ```
4. Add `dependencies=[Depends(require_api_key_ws)]` to the 10th (`stream.router`,
   `server.py:86`) — per Decision 4, NOT `require_api_key`:
   ```python
   app.include_router(stream.router, prefix="/api/v1", dependencies=[Depends(require_api_key_ws)])
   ```
5. Add `dependencies=[Depends(require_api_key)]` to the 14 protected inline route decorators
   per Decision 2's table (`server.py:118` `/metrics`, `:134,144,154` `live/status`,
   `live/snapshot`, `live/entities/{entity_id}`, `:168` `/api/v1/state`, `:175` `/api/v1/inspect`,
   `:183,192` `/api/v1/entities`, `/api/v1/entities/{entity_id}`, `:203,208`
   `/api/v1/control/pause`, `/api/v1/control/resume`, `:213` `/api/v1/test/publish_event`,
   `:235,246` `live/health`, `live/stream-health`, `:252`
   `observability/history/runs/{run_id}/report`), e.g.:
   ```python
   @app.get("/metrics", dependencies=[Depends(require_api_key)])
   async def get_metrics(manager: V2EngineManager = Depends(get_engine_manager)):
   ```
   (add the kwarg alongside any existing `response_model=` kwarg on the same decorator line;
   do not remove or reorder existing kwargs).
6. Leave `/health` (`server.py:128`) completely unchanged — no `dependencies=` kwarg. This
   is the exemption's entire mechanism.
7. Add `dependencies=[Depends(require_api_key_header_or_query)]` to the 3 dashboard routes
   (`server.py:276` `/api/v1/observability/ui`, `:2370` `/observability/ui`, `:2374`
   `/api/v1/observability/live/ui`):
   ```python
   @app.get("/api/v1/observability/ui", response_class=HTMLResponse, dependencies=[Depends(require_api_key_header_or_query)])
   async def get_observability_ui():
   ```

**Other writers to `server.py`'s route table:** none currently — `server.py` is the sole
place routers are wired together in this repo (confirmed by the parent epic investigation
and reconfirmed here: no other module calls `app.include_router` or defines `@app.get`/
`@app.post` against this specific `FastAPI` instance). This step's edits are additive kwargs
on existing lines only — no route is added, removed, or reordered, and the ~2090-line inline
HTML string (`server.py:278-2367`) is never touched.

**Do NOT touch:** the inline HTML/JS dashboard content (`server.py:278-2367`); any of
`src/api/routes/*.py`, `src/api/ws/stream.py`, or `src/simulation_quality/api/routes.py`'s
own `APIRouter(...)` constructor calls (per investigation's Anti-Drift Hazard — the
dependency is applied only at `server.py`'s `include_router()`/decorator call sites, never
inside the 10 router-owning files themselves); `src/api/routes/control.py`, `health.py`,
`state.py` (confirmed still-empty, unwired dead files, unrelated to this ticket).

**Verify:** `test_health_exempt_from_auth`, `test_metrics_requires_auth`,
`test_missing_api_key_returns_401_on_protected_route`,
`test_control_mutation_routes_require_auth`, `test_valid_api_key_allows_request_through`,
`test_websocket_route_requires_valid_key_and_closes_cleanly` (Step 7); plus re-running
`tests/api/test_cors_config.py` and `tests/api/test_health_liveness.py` unmodified (both
must stay green — they only ever hit `/health`).

### Step 5 — Fix `tests/api/test_scenario_runtime_api.py`'s `client` fixture

**Files:** `tests/api/test_scenario_runtime_api.py`

**Change:** This file's `client` fixture (`tests/api/test_scenario_runtime_api.py:27-44`)
builds `RuntimeProfile(name="test", ...)` with no `api_key_hashes` and drives ~14 assertions
against `/api/v1/scenarios/...` (the `scenarios` sub-router, which gets `require_api_key` at
Step 4) with no auth header — every one of these would start 401ing once Step 4 lands.
Cheapest fix per test_plan.md: add a default header to the `TestClient` construction (one
line) rather than touching all ~14 call sites. Add near the top of the file:

```python
import hashlib

_TEST_CLIENT_ID = "scenario-runtime-test-client"
_TEST_RAW_KEY = "scenario-runtime-test-key"
_TEST_KEY_HASH = hashlib.sha256(_TEST_RAW_KEY.encode("utf-8")).hexdigest()
```

In the `client` fixture, add `api_key_hashes=f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"` to the
`RuntimeProfile(...)` constructor call, and change:

```python
    with TestClient(app, raise_server_exceptions=True) as c:
```

to:

```python
    with TestClient(app, raise_server_exceptions=True, headers={"X-API-Key": _TEST_RAW_KEY}) as c:
```

**Other writers to this file:** none — this is the file's own, sole fixture.

**Do NOT touch:** any of the ~14 individual `test_*` functions or their
`client.get`/`client.post` call sites — the header is attached once, at the `TestClient`
level, and applies to every request made through `c`.

**Verify:** `pytest tests/api/test_scenario_runtime_api.py -v` fully green (this is
test_plan.md's `test_scenario_runtime_client_fixture_still_passes_with_auth` — a regression
guard, not a new test).

### Step 6 — Fix `tests/observability/test_metrics_export.py::test_metrics_endpoint_integration`

**Files:** `tests/observability/test_metrics_export.py`

**Change:** This test (`tests/observability/test_metrics_export.py:152-178`) launches a real
`python3 -m src serve --port 8011 --log-level ERROR` subprocess and scrapes `/metrics` with
`requests.get(...)` and no key — `/metrics` is not exempt (Decision 2), so this will start
401ing. Fix: seed the subprocess's environment and add the header to the scrape call:

```python
import hashlib
import os

_TEST_CLIENT_ID = "metrics-integration-test-client"
_TEST_RAW_KEY = "metrics-integration-test-key"
_TEST_KEY_HASH = hashlib.sha256(_TEST_RAW_KEY.encode("utf-8")).hexdigest()

def test_metrics_endpoint_integration():
    port = 8011
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    env = {**os.environ, "RPG_API_KEY_HASHES": f"{_TEST_CLIENT_ID}:{_TEST_KEY_HASH}"}
    server = subprocess.Popen(cmd, env=env)
    time.sleep(3)
    try:
        resp = requests.get(
            f"http://127.0.0.1:{port}/metrics",
            headers={"X-API-Key": _TEST_RAW_KEY},
        )
        assert resp.status_code == 200
        ...  # rest of the existing assertions unchanged
    finally:
        server.terminate()
        server.wait()
```

This is the one test in the whole regression surface that exercises the full
CLI→env→`ConfigLoader`→`create_v2_app` chain end to end for the new field (per
test_plan.md) — do not let it silently start failing with 401 and get treated as flaky.

**Other writers to `test_metrics_export.py`:** none — `test_metrics_endpoint_direct` (calls
the route function directly, bypassing FastAPI's dependency injection entirely) and
`test_prometheus_metrics_registry_and_structure`/
`test_prometheus_hard_law_violation_metrics_export`/`test_multiple_registries_prevent_collision`
(construct `V2EngineManager` directly, never touch `create_v2_app`/HTTP) are unaffected and
must be left unmodified.

**Do NOT touch:** `test_metrics_endpoint_direct` or the three `V2EngineManager`-direct tests
in this same file.

**Verify:** `pytest tests/observability/test_metrics_export.py -v` fully green.

### Step 7 — New `tests/api/test_api_key_auth.py`

**Files:** `tests/api/test_api_key_auth.py` (new)

**Change:** Implement all 12 tests named in test_plan.md's "New Tests Required" section,
following `tests/api/test_cors_config.py`'s established pattern (real `TestClient`, real
response status/headers, no subprocess), plus 2 plan-added tests covering Decision 4's
WebSocket-auth hazard (not in test_plan.md's original list — added here because Step 4's
`require_api_key_ws` dependency is a new code path test_plan.md's authors could not have
anticipated; see Decision 4).

Shared module-level fixtures:
```python
import hashlib
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.api.server import create_v2_app
from src.config.profiles import RuntimeProfile, HardwareClass

TEST_CLIENT_ID = "test-client"
TEST_RAW_KEY = "test-raw-key-12345"
TEST_KEY_HASH = hashlib.sha256(TEST_RAW_KEY.encode("utf-8")).hexdigest()

def _make_profile(**overrides):
    base = dict(
        name="auth-test", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=256, max_cpu_percent=100.0, max_worker_count=0,
        max_queue_depth=100, max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0, max_tick_budget_ms=200.0,
        api_key_hashes=f"{TEST_CLIENT_ID}:{TEST_KEY_HASH}",
    )
    base.update(overrides)
    return RuntimeProfile(**base)
```

Tests (from test_plan.md, category noted): `test_missing_api_key_returns_401_on_protected_route`
(integration; `TestClient(create_v2_app(_make_profile()))`, GET `/api/v1/state` with no
header, assert 401 — no `with` context manager needed, since `require_api_key` runs before
`get_engine_manager`'s own dependency and raises first, so the engine never needs to start
for this assertion); `test_invalid_api_key_returns_401_on_protected_route` (same route,
`X-API-Key: wrong-key`, 401); `test_malformed_api_key_header_returns_401_not_500` (empty
string header, and a header containing non-ASCII/control characters e.g.
`"X-API-Key": "\x00\xff invalid é"`, both assert 401 not 500 — note in a comment that
this is inherently safe because `str.encode("utf-8")` cannot raise for any Python `str`, so
`_hash_key` never throws regardless of header content); `test_valid_api_key_allows_request_through`
(`with TestClient(...) as client:` — needs the real lifespan/engine started this time — GET
`/api/v1/state` with `X-API-Key: TEST_RAW_KEY`, assert 200); `test_health_exempt_from_auth`
(GET `/health` with no key, assert 200); `test_metrics_requires_auth` (GET `/metrics` with no
key, assert 401); `test_control_mutation_routes_require_auth` (POST `/api/v1/control/pause`
and `/api/v1/control/resume`, no key, both assert 401); `test_key_comparison_is_constant_time`
(architecture guard; `unittest.mock.patch("src.api.auth.hmac.compare_digest",
wraps=hmac.compare_digest)`, make a valid-key request, assert the spy was called);
`test_keys_never_stored_or_compared_as_plaintext` (unit; call `configure_api_keys(profile)`
directly, assert `TEST_RAW_KEY not in src.api.auth._client_keys` and
`TEST_KEY_HASH in src.api.auth._client_keys`, and that every key in `_client_keys` is a
64-char lowercase hex string); `test_config_loader_env_var_seeds_api_keys` (integration; use
`monkeypatch.setenv("RPG_API_KEY_HASHES", f"{TEST_CLIENT_ID}:{TEST_KEY_HASH}")`, call
`ConfigLoader.load_profile(profile_name="cli_default")`, assert
`profile.api_key_hashes == f"{TEST_CLIENT_ID}:{TEST_KEY_HASH}"`, then build
`create_v2_app(profile)` and assert a `X-API-Key: TEST_RAW_KEY` request to `/api/v1/state`
succeeds); `test_client_identity_exposes_client_id` (unit; `from src.api.auth import
ClientIdentity`; `ci = ClientIdentity(client_id="abc")`; assert `.client_id == "abc"` and
`{ci: 1}` works, i.e. `ci` is hashable).

Plan-added (Decision 4 coverage): `test_websocket_route_requires_valid_key_and_closes_cleanly`
(connect to `/api/v1/ws` with no key via `client.websocket_connect(...)`, assert
`WebSocketDisconnect` is raised on entering the `with` block — confirming the connection is
cleanly rejected via `WebSocketException`→`websocket.close(code=1008)`, not an unhandled
server-side exception that would otherwise crash the ASGI connection);
`test_websocket_route_accepts_valid_key_via_query_param` (connect to
`f"/api/v1/ws?key={TEST_RAW_KEY}"`, assert no `WebSocketDisconnect` on entry — the handshake
proceeds far enough to reach `stream.py`'s own protocol-negotiation logic).

**Other writers to this file:** none — new file, this ticket's sole author.

**Do NOT touch:** any file under `tests/api/` other than this new one and the two named in
Steps 5-6.

**Verify:** `pytest tests/api/test_api_key_auth.py -v` fully green; then the full scoped
command from test_plan.md: `pytest tests/api/ tests/observability/test_metrics_export.py -m
"not slow" -v` fully green.

### Step 8 — New doc: `docs/architecture/http_api_key_authentication.md`

**Files:** `docs/architecture/http_api_key_authentication.md` (new)

**Change:** New ADR-shaped doc (per Decision 8), mirroring
`docs/architecture/observability_hot_path_safety_contract.md`'s and
`simulation_watchdog.md`'s existing grain (a focused, single-mechanism architecture doc, not
a numbered pattern). Required sections: (1) **Mechanism** — `Depends()`-based, not
middleware, applied per-route/per-router at `server.py`'s `include_router()`/decorator call
sites; storage (SHA-256 hashed-at-rest, `RuntimeProfile.api_key_hashes`, delimited format
from Decision 7); comparison (`hmac.compare_digest`, constant-time, iterates every configured
hash — Step 1). (2) **Route classification** — the exact table from Decision 2 (which routes
get `require_api_key` vs `require_api_key_header_or_query` vs `require_api_key_ws` vs
exempt), so a future route addition has a documented default to follow (default: protected,
via `require_api_key`, unless there's a documented reason otherwise). (3) **Dashboard/browser
auth tradeoff** — Decision 3 in full: the query-param channel, why it exists, and the
explicit security tradeoff (keys in URLs/access logs/browser history) an operator should
weigh before relying on it for a real public deployment. (4) **WebSocket auth exception-type
hazard** — Decision 4 in full, with the same source citations, so a future contributor adding
a new WebSocket route to this app knows to use `require_api_key_ws`
(`WebSocketException`-raising), not `require_api_key` (`HTTPException`-raising). (5)
**`ClientIdentity`'s reuse contract** — states explicitly that
`TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL` is expected to key its own per-client state
off this object, and that its shape (`client_id: str`, frozen, hashable) should not be
narrowed without checking that ticket's needs first.

**Other writers to `docs/architecture/`:** none relevant — this is a new file; no existing
doc in that directory covers HTTP authentication (confirmed by investigation.md's grep).

**Do NOT touch:** any existing file under `docs/architecture/` — this step only adds one new
file.

**Verify:** no automated test; verified by the standard doc-integrity/frontmatter checks this
repo already runs on `docs/` (`tests/docs/test_doc_integrity.py`, unmodified by this ticket).

### Step 9 — New parity ledger entry `INFRA-377`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Immediately before appending, re-run `grep -n "^- id: INFRA-37" docs/
parity_ledger/infrastructure.yaml | tail` to reconfirm `INFRA-376` is still the last entry
(this repo's working directory can be shared by concurrent sessions per CLAUDE.md's Hard
Rules — another session may have appended an entry between plan-write time and
implementation time). Append, following the existing 8-field shape (`id`, `text`, `status`,
`priority`, `v2_evidence`, `test_path`, `divergence_note`, `proof_type`):

```yaml
- id: INFRA-377
  text: Per-client API-key authentication (src/api/auth.py) gates every route in
    src/api/server.py except /health (liveness probe, the sole exemption) via
    dependencies=[Depends(require_api_key)] at 9 of 10 app.include_router() call
    sites and on 14 of 18 inline routes. Keys are stored hashed-at-rest (SHA-256)
    in RuntimeProfile.api_key_hashes (a plain str of comma-separated
    'client_id:sha256hex' pairs, loaded via ConfigLoader's CLI>Env>YAML>Defaults
    chain / RPG_API_KEY_HASHES env var / --api-key-hashes CLI flag) and compared
    via hmac.compare_digest (never ==). stream.router's 3 WebSocket routes use a
    dedicated require_api_key_ws dependency that raises WebSocketException
    instead of HTTPException, since FastAPI's websocket dependency resolution
    (fastapi/routing.py get_websocket_app) runs before websocket.accept() and
    only WebSocketException is safely converted to a clean websocket.close() by
    Starlette's ExceptionMiddleware. The 3 browser-facing dashboard routes
    (/api/v1/observability/ui and its 2 redirects) and the 3 WebSocket routes
    additionally accept a 'key' query-param as a documented, narrower-scoped
    auth channel (keys can appear in URLs/access logs/browser history) since a
    plain browser fetch()/WebSocket() cannot attach a custom header. The
    resolved ClientIdentity (frozen, hashable, client_id: str) is a reusable
    identity object for the sibling per-client admission-control ticket
    (TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL).
  status: verified
  priority: P1
  v2_evidence: src/api/auth.py, src/api/server.py
  test_path: tests/api/test_api_key_auth.py::test_missing_api_key_returns_401_on_protected_route
  divergence_note: null
  proof_type: contract
```

**Other writers to this file:** `docs/parity_ledger/infrastructure.yaml` is a single YAML
list appended to by every ticket that lands a new infrastructure-layer parity fact — the same
shared-resource caveat prior tickets in this file (e.g. `INFRA-374`-`376`) have already
documented for this exact file. `INFRA-376` is the immediately preceding entry and is already
merged (no concurrent-write race against it).

**Do NOT touch:** any existing entry in this file, including `INFRA-364` (CORS fix) and
`INFRA-365` (`GovernorPolicy.from_mode()`) — both confirmed unrelated to authentication by
the parent epic investigation.

**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
parses without error; the cited `test_path` (Step 7) must exist and pass before this entry
can honestly claim `status: verified`.

## Scope Guards

Must NOT be touched or introduced by this ticket, per the ticket's Out of Scope,
investigation.md's Anti-Drift Hazards, and this plan's own decisions:

- **No OAuth/JWT/third-party identity federation** — despite `pyjwt` already being a
  dependency (`requirements.txt`), it is not used, imported, or referenced anywhere in this
  plan.
- **No per-client rate limiting / admission control of any kind** — that is
  `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`'s scope; `ClientIdentity` is built to be
  reusable by it, but no admission/throttling logic is added here.
- **No self-service key issuance/rotation UI or API** — the only provisioning path is the
  operator-facing CLI flag / env var / YAML config (Steps 2-3); no endpoint in this plan
  creates, lists, or revokes keys.
- **No new distributed infrastructure** — no Redis-backed key storage (despite `redis`
  already being a dependency); the module-level `_client_keys` dict (Step 1) is
  single-process, in-memory, matching the ticket's Out of Scope explicitly.
- **Do not add `dependencies=[Depends(...)]` to any `APIRouter(...)` constructor call** in
  `src/api/routes/*.py`, `src/api/ws/stream.py`, or `src/simulation_quality/api/routes.py` —
  every dependency is wired at `server.py`'s `include_router()`/route-decorator call sites
  only (Step 4).
- **Do not touch `src/api/routes/control.py`, `health.py`, `state.py`** — confirmed
  still-empty, unwired dead files, unrelated to this ticket.
- **Do not add `ClientIdentity` to `src/api/schemas.py`** — that file is response-shape-only
  per its own docstring; `ClientIdentity` lives in `src/api/auth.py`.
- **Do not exempt `/metrics`, `/api/v1/control/pause`, `/api/v1/control/resume`, or
  `/api/v1/test/publish_event`** — Decision 2's classification table is final for this
  ticket; only `/health` is exempt.
- **Do not reuse `require_api_key_header_or_query`'s or `require_api_key_ws`'s query-param
  channel on any route outside the 3 dashboard routes and the 3 WebSocket routes
  respectively** — the weaker channel is deliberately scoped narrowly (Decision 3/4); every
  other protected route uses the strict header-only `require_api_key`.
- **Do not touch the ~2090-line inline HTML/JS dashboard content** (`server.py:278-2367`) —
  only decorator kwargs change on the routes that wrap it.
- **Do not modify `docs/plans/http_admission_control_epic.md`,
  `docs/architecture/observability_hot_path_safety_contract.md`, or
  `docs/engine/known_limitations.md`** — all three are the parent epic's or the sibling
  admission-control ticket's doc-update scope, not this ticket's (confirmed by both
  investigations: this ticket's own investigation found no existing "no HTTP auth" line in
  `known_limitations.md` to update, and the observability hot-path contract is
  `ObservabilityMode`-specific, unrelated to authentication).
- **Do not add a `List[str]`/`Dict[str, str]`-typed field to `RuntimeProfile` for this
  purpose** — `api_key_hashes` must stay a plain `str` (Decision 6).

## Dependency Map

- Step 1 (`src/api/auth.py`) has no dependencies on other steps; it is first (everything else
  imports from it).
- Step 2 (`RuntimeProfile.api_key_hashes`) has no dependencies; independent of Step 1, though
  Step 1's `configure_api_keys(profile: RuntimeProfile)` signature references the type.
- Step 3 (CLI flag) depends on Step 2 (the field must exist for `cli_overrides` to have
  somewhere to land).
- Step 4 (`server.py` wiring) depends on Steps 1 and 2 (imports `src.api.auth`'s dependency
  functions; calls `configure_api_keys(profile)` which reads `profile.api_key_hashes`).
- Step 5 (`test_scenario_runtime_api.py` fix) depends on Step 4 (the `scenarios` router must
  already require auth for the fixture fix to be necessary/testable).
- Step 6 (`test_metrics_export.py` fix) depends on Steps 2-4 (needs the CLI/env path and
  `/metrics`'s new dependency to exist).
- Step 7 (new test file) depends on Steps 1-4 being complete; it exercises the full stack.
- Step 8 (new doc) depends on Steps 1-4's decisions being finalized (documents the shipped
  mechanism, not a proposal) — can be written in parallel with Step 7.
- Step 9 (parity ledger) depends on Step 7 passing, since the new entry's `test_path` cites a
  specific test that must exist and pass before the entry can honestly claim
  `status: verified`.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Every route requires a valid per-client API key, except an explicitly-justified exemption (`/health`) documented in Implementation Notes | Steps 1, 4 (Decision 2's classification table); Step 8 (doc) | `test_health_exempt_from_auth`, `test_metrics_requires_auth`, `test_missing_api_key_returns_401_on_protected_route`, `test_control_mutation_routes_require_auth`, `test_websocket_route_requires_valid_key_and_closes_cleanly` |
| An invalid, missing, or malformed key returns 401/403, not a 500 or pass-through | Step 1 (`require_api_key`/`require_api_key_header_or_query`/`require_api_key_ws` all raise 401 on `_resolve_client_id(...) is None`, never a bare pass-through) | `test_missing_api_key_returns_401_on_protected_route`, `test_invalid_api_key_returns_401_on_protected_route`, `test_malformed_api_key_header_returns_401_not_500` |
| Keys stored hashed-at-rest, never plaintext, loaded through the existing `ConfigLoader` precedence chain | Step 2 (`RuntimeProfile.api_key_hashes`, storing hashes not raw keys), Step 1 (`_parse_api_key_hashes`/`_resolve_client_id` never compare raw plaintext), Step 3 (CLI flag), Decision 6 (`ConfigLoader` needs zero code changes) | `test_keys_never_stored_or_compared_as_plaintext`, `test_config_loader_env_var_seeds_api_keys` |
| Key comparison uses constant-time comparison (`hmac.compare_digest`), not `==` | Step 1 (`_resolve_client_id`) | `test_key_comparison_is_constant_time` |
| The resulting client-identity object is reusable by a future admission-control layer without rework | Step 1 (`ClientIdentity`, frozen + hashable, `client_id: str`); Step 8 (doc's reuse-contract section) | `test_client_identity_exposes_client_id` |
| `tests/api/` gains real, in-process `TestClient`-based tests asserting real response status/headers | Step 7 (`tests/api/test_api_key_auth.py`) | All tests in Step 7 |

## Anti-Drift Notes

- **`require_api_key_header_or_query` and `require_api_key_ws` are deliberately separate,
  narrowly-scoped functions, never the default.** A future editor adding a new route must
  reach for `require_api_key` first; the query-param-accepting variants exist only because a
  browser cannot attach custom headers to the 3 dashboard pages / 3 WebSocket routes
  specifically — reusing them elsewhere silently reintroduces the "keys in URLs/logs"
  tradeoff onto a route that didn't need it.
- **`stream.router` MUST use `require_api_key_ws`, never `require_api_key`.** This is not a
  style preference — raising `HTTPException` on a websocket-scoped dependency is a real,
  source-verified failure mode with the installed FastAPI/Starlette versions (Decision 4), not
  a hypothetical. Do not "simplify" this back to a single shared dependency function without
  re-verifying the FastAPI/Starlette exception-handling behavior first.
- **`_client_keys` (Step 1) is process-global module state, refreshed on every
  `create_v2_app()` call.** This mirrors the pre-existing `_engine_manager` singleton pattern
  in `src/api/dependencies.py` and is not a new architectural risk this ticket introduces —
  but it does mean two `create_v2_app()`-built apps cannot coexist in the same process with
  different key sets (last call wins). No current test needs that; if a future test does, it
  needs its own isolation strategy (e.g. explicit `configure_api_keys()` calls interleaved
  with requests), not a change to this global's shape.
- **`api_key_hashes` must never become a `List[str]`/`Dict[str,str]`-typed `RuntimeProfile`
  field.** `ConfigLoader`'s env-var loop (`loader.py:54-70`) has no handling for non-scalar
  annotations and would crash with an uncaught `TypeError` the moment the corresponding env
  var is set (Decision 6). All structured parsing stays in `src/api/auth.py`.
- **Do not log the raw API key or the resolved SHA-256 hash anywhere in the request-handling
  path**, including inside `HTTPException`/`WebSocketException` `detail`/`reason` strings
  (both stay the generic `"Invalid or missing API key."`) or any future logging added to
  `require_api_key`/`_resolve_client_id`. The one place a hash-adjacent value is ever logged
  is `_parse_api_key_hashes`'s malformed-entry warning, which deliberately logs only the
  entry's index, never its content.
- **`/metrics` staying non-exempt is a deliberate decision (Decision 2), not an oversight** —
  do not silently re-exempt it in a future refactor "because metrics endpoints are usually
  public."

## Security Considerations

- **Timing-attack resistance:** `_resolve_client_id` (Step 1) iterates every configured
  `(hash, client_id)` pair and calls `hmac.compare_digest(candidate_hash, stored_hash)` for
  each — never a dict `in`/`==` shortcut, which would leak timing information about which
  stored hash (if any) partially matched. `hmac.compare_digest` itself performs a
  constant-time comparison for equal-length inputs; both `candidate_hash` and every
  `stored_hash` are fixed 64-character SHA-256 hex digests when configuration is well-formed,
  so length-based timing variance does not arise in the normal case.
- **Key exposure in logs:** neither the raw presented key nor its computed hash is ever
  passed to `logger.*` anywhere in `src/api/auth.py` (Step 1) or in either `HTTPException`/
  `WebSocketException` raised on failure — both use the fixed, generic message `"Invalid or
  missing API key."`. The one logging call that touches `api_key_hashes`-adjacent data
  (`_parse_api_key_hashes`'s malformed-entry warning) logs only a numeric index, never the
  entry's content, so a misconfigured hash never reaches a log line either.
- **Malformed input cannot crash the comparison path:** `hashlib.sha256(raw_key.encode(
  "utf-8")).hexdigest()` cannot raise for any Python `str` input (UTF-8 can encode every
  valid Python `str`, including empty strings and strings containing control/non-ASCII
  characters) — so `test_malformed_api_key_header_returns_401_not_500`'s edge cases are
  inherently safe by construction, not by a special-cased guard clause.
- **Dashboard/WebSocket query-param channel tradeoff (Decision 3/4):** accepting a key via
  `?key=...` means it can be captured in server access logs, browser history, and any
  intermediate proxy's request logs — a real, documented weakening relative to the
  header-only channel used everywhere else. This plan scopes the tradeoff to exactly the 6
  routes (3 dashboard pages + 3 WebSocket routes) that have no alternative given plain-browser
  client constraints, and documents it in `docs/architecture/http_api_key_authentication.md`
  (Step 8) and the parity ledger entry (Step 9) so it is discoverable, not silently accepted.

## Unresolved Questions

None. The two genuine open items investigation.md flagged (route exemption list; dashboard
browser-auth channel) are both resolved above (Decision 2, Decision 3), and the one
additional technical hazard this plan discovered during fact-verification (WebSocket
dependency exception-type handling) is resolved with a concrete, source-cited fix (Decision
4) rather than deferred.

## Deviations (recorded during Implement)

- **Step 7, `test_malformed_api_key_header_returns_401_not_500`'s non-ASCII/control-character
  case: header value passed as raw `bytes`, not `str`.** The plan's literal test code
  (`headers={"X-API-Key": "\x00\xff invalid é"}`) fails before the request is ever sent:
  httpx (the transport `starlette.testclient.TestClient` wraps) enforces a client-side ASCII-only
  check on `str` header values (`httpx/_models.py::_normalize_header_value`, `value.encode("ascii")`)
  and raises `UnicodeEncodeError` for the `\xff` byte — this is a restriction of the test
  transport library itself, not something `require_api_key`/`_resolve_client_id` needs to
  guard against, and it happens entirely outside the code this ticket owns. Fix: pass the
  same byte sequence as `bytes` (`headers={"X-API-Key": b"\x00\xff invalid e"}`), which
  bypasses httpx's client-side `str`-only ASCII check and reaches the server exactly as a
  real non-ASCII header would arrive over the wire (confirmed via a manual repro against the
  live app: returns 401, not 500). Comment added in the test explaining why. No production
  code changed by this deviation — `_hash_key`'s `str.encode("utf-8")` guarantee (Decision 7)
  is unaffected and still verified by the same test, just via a transport-compatible
  representation of the malformed input.
- **Step 9, parity ledger entry text: reworded one clause to avoid a YAML parse error.** The
  planned entry text included the literal substring `client_id: str` (describing
  `ClientIdentity`'s field) inside a plain (unquoted) multi-line YAML scalar. `client_id:` was
  parsed by PyYAML as a nested mapping key inside the block scalar (`mapping values are not
  allowed here`, confirmed via `python3 -c "import yaml; yaml.safe_load(...)"` failing at the
  exact line/column of that clause). Reworded to "with a client_id string field" — same
  meaning, no colon-space token. No other content changed; re-validated the full file parses
  and the appended entry is `docs/parity_ledger/infrastructure.yaml`'s last entry with
  `id: INFRA-377` after the fix.
- **Document-Update phase (not Implement): `docs/plans/http_admission_control_epic.md` was
  edited despite this plan's own Scope Guard saying not to.** The Scope Guards section above
  says this file is "the parent epic's or the sibling admission-control ticket's doc-update
  scope, not this ticket's." The Document-Update agent deviated deliberately, with real
  precedent: the same file already carries an identical strikethrough-plus-Resolved edit made
  by a prior, unrelated hotfix ticket (`TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`)
  on the sibling CORS acceptance-signal bullet immediately above the one this ticket resolves
  -- confirmed via `git log --follow -- docs/plans/http_admission_control_epic.md`. Struck
  through and resolved the "At least one auth mechanism gates the API surface" bullet, citing
  this ticket, `INFRA-377`, and `docs/architecture/http_api_key_authentication.md`. The
  orchestrator separately, directly edited the same file (outside this agent dispatch): the
  stale `Priority: P2 -- explicitly gate on deployment plans` line (updated to P1, since the
  gating deployment decision fired 2026-08-23) and a new intro line naming both child tickets
  extracted from the parent epic. Recorded here per Architecture-Verify's finding that this
  deviation, while disclosed in the Document-Update agent-monitoring event at the time, was
  not yet reflected in this plan.md or the ticket's own Files Changed section.
