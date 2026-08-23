---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260823-HTTP-API-KEY-AUTH
artifact_type: investigation
tags: [architecture, security, api-design]
---

# Investigation — TCK-20260823-HTTP-API-KEY-AUTH

## Search-Before-Grep Note

Per the Context Scan hard rule, `mcp__knowledge-search__search_docs` was called first with query
"FastAPI per-route Depends dependency router auth exemption health liveness API key" — it returned
`{"error":"index not found","action":"run make knowledge-index"}`, the same persistent outage the
parent epic investigation (`staging_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/investigation.md`)
hit and documented. `python3 tools/knowledge_search.py query "API key auth ClientIdentity
RuntimeProfile config loader precedence" --top-k 5` (the documented fallback) was also tried and
returned the same "knowledge index not found" outage — not silently skipped. `graphify query
"FastAPI Depends APIRouter dependencies auth"` was then run and returned 164 nodes (`RuntimeProfile`,
`server.py::create_v2_app`, `V2EngineManager`, the 9 route modules, `ObservabilityConfig`, etc.) —
consistent with, and narrower than, what the parent investigation's own graphify pass surfaced. All
findings below come from reading the actual source files these queries and the ticket's own Related
Code Areas point at. The parent investigation's findings on `src/api/server.py`'s overall shape,
middleware stack, and the "zero constant-time-comparison precedent" conclusion are re-confirmed by
this pass (see inline citations below) and are not re-derived from scratch.

## Current Behavior

**Full route enumeration of `src/api/server.py::create_v2_app()`** (2378 lines; confirmed via
`grep -n "^\s*@app\.\|^\s*app.include_router"`), superseding the parent investigation's
"~24 routes" estimate with an exact list:

Sub-router mounts (9, all at `/api/v1`, lines 86–113):
`stream.router` (`src/api/ws/stream.py`, `APIRouter()` — no prefix, no `dependencies=`),
`history.router` (`/observability/history`), `search.router` (`/observability/search`),
`behavior.router` (`/behavior`), `decisions.router` (`/observability`), `scenarios.router`
(`/scenarios`), `campaigns.router` (`/campaigns`), `chronicle.router` (`/chronicle`),
`economy.router` (no prefix printed by grep — confirmed `/economy` in file), `quality_routes.router`
(`/quality`, from `src/simulation_quality/api/routes.py`). **None of the 9 `APIRouter(...)`
constructor calls pass a `dependencies=` kwarg today** (verified by grepping every
`APIRouter(` call site in `src/api/routes/*.py`, `src/api/ws/stream.py`,
`src/simulation_quality/api/routes.py`).

Inline routes defined directly on `app` (lines 118–2377):
`/metrics` (118), `/health` (128), `/api/v1/observability/live/status` (134),
`/api/v1/observability/live/snapshot` (144), `/api/v1/observability/live/entities/{entity_id}` (154),
`/api/v1/state` (168), `/api/v1/inspect` (175), `/api/v1/entities` (183),
`/api/v1/entities/{entity_id}` (192), `/api/v1/control/pause` (203, POST, mutates engine state),
`/api/v1/control/resume` (208, POST, mutates engine state), `/api/v1/test/publish_event` (213, POST),
`/api/v1/observability/live/health` (235), `/api/v1/observability/live/stream-health` (246),
`/api/v1/observability/history/runs/{run_id}/report` (252), `/api/v1/observability/ui` (276, HTML
dashboard, ~2090 lines of inline HTML/JS), `/observability/ui` (2370, `RedirectResponse` to the
dashboard), `/api/v1/observability/live/ui` (2374, `RedirectResponse` to the dashboard). 17 inline
routes total.

**Dependency-injection pattern confirmed**: `src/api/dependencies.py` is a plain module-level
singleton store (`_engine_manager`, `_quality_hub`, `_quality_persistence` globals with
`set_x`/`get_x` pairs, no request-scoped state). `Depends(get_engine_manager)` is the one
established `Depends()` idiom in this file, used purely to inject the engine singleton, not for
auth. **Confirmed zero usage anywhere in `src/` of `fastapi.security.APIKeyHeader`, `Header(...)`,
`Security(...)`, or `HTTPBearer`** — no FastAPI security-utility precedent exists (grep across all
of `src/`), consistent with and extending the parent investigation's "zero credential-comparison
precedent" finding to the specific FastAPI mechanism level.

**`RuntimeProfile` (`src/config/profiles.py:14-61`)**: a frozen (`ConfigDict(frozen=True)`)
Pydantic `BaseModel`, documented as "Authoritative resource-envelope contract... hard ceilings for
engine execution" — 19 fields, all scalar (`str`/`int`/`float`/`bool`/`HardwareClass` enum) except
`cadence: SystemCadence`. `create_v2_app(profile: RuntimeProfile)` already receives the full
profile object as its sole argument (server.py:21), so any new field added to `RuntimeProfile` is
directly available inside `create_v2_app()` with no new plumbing.

**`ConfigLoader.load_profile()` (`src/config/loader.py:18-86`)**: implements the CLI > Env > YAML >
Defaults precedence law. The YAML layer (step 2) merges an arbitrary dict from
`yaml_data["profiles"][profile_name]` — any field type works here. **The env-var layer (step 3,
lines 54-70) is type-constrained**: it does `field_type = RuntimeProfile.model_fields[field]
.annotation` then dispatches on `field_type == int`, `== float`, `== bool`, else
`issubclass(field_type, str)`. `issubclass()` raises `TypeError` (not caught — only `ValueError` is
caught) if `field_type` is a non-class typing construct like `List[str]` or `Dict[str, str]`. **A
new field intended to be settable via `RPG_<FIELD>` env var must therefore be typed as a plain
`str` (or another of the four already-handled scalar types)** — a `List[str]`/`Dict[str,str]` field
would silently work when supplied via YAML but crash `ConfigLoader.load_profile()` with an
uncaught `TypeError` the moment its env var is set. This is a concrete, previously-undocumented
constraint on the "CLI/env-var-seeded key list" the ticket asks for.

**`src/cli/entry.py`**: both `_run_cli()` (lines 184-197) and `_run_serve()` (lines 262-284) build
`cli_overrides` as a hand-written dict (currently only `{"max_worker_count": args.workers}`) and
call `ConfigLoader.load_profile(profile_name="cli_default", config_path=args.config,
cli_overrides=cli_overrides)`. `_run_serve()` is the actual server entry point — it calls
`create_v2_app(profile)` directly after loading. A new `--api-key-hashes` CLI flag would need a new
`argparse.add_argument` call plus a new `cli_overrides` entry in both functions (or at least
`_run_serve`) to reach `create_v2_app`.

**Existing typed-config precedent found for comparison**: `ObservabilityConfig`
(`src/observability/config.py`) is a second, independent config-resolution pattern in this repo —
plain classmethods reading `os.environ.get("SIM_X") or os.environ.get("RPG_X") or default`,
outside `ConfigLoader`/`RuntimeProfile` entirely. It is **not** a better fit than `RuntimeProfile`
for this ticket (the parent investigation's recommendation to use `ConfigLoader`'s precedence chain
stands — `ObservabilityConfig`'s ad hoc dual-prefix pattern is not typed/validated the way
`RuntimeProfile`'s Pydantic fields are, and mixing a second config-loading path into `src/api/`
would itself be an inconsistency), but it confirms `RPG_`-prefixed env vars are the house style.

**Route-mounted test apps vs. bare-router test apps**: only 4 test files anywhere under `tests/`
construct the full app via `create_v2_app(...)` + `TestClient` (`grep -rl "create_v2_app("
tests/`): `tests/api/test_cors_config.py`, `tests/api/test_health_liveness.py`,
`tests/api/test_scenario_runtime_api.py`, `tests/observability/test_metrics_export.py`. All other
`tests/api/*.py` files (e.g. `test_decision_api.py`) invoke route handler functions directly
(`@pytest.mark.anyio`, direct call, no `TestClient`) or build their own bare `FastAPI()` +
single-router app (mirroring `tests/simulation_quality/test_api_routes.py::_make_app()`) — these
are **not** wired through `create_v2_app()`'s `include_router()` calls and are therefore unaffected
by an auth dependency added at the `include_router()`/`server.py` level. This significantly narrows
the real regression surface — see Test Plan.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter constrains HTTP-layer authentication — this is infrastructure, not
simulation law. The applicable constraints are architectural (CLAUDE.md Hard Rules: "Do not create
hidden or implicit durable behavior," "Do not mutate durable state outside authoritative flows")
and the Durable State Rule (typed model, stable location, lifecycle, inspection/debug visibility,
tests) — both already correctly invoked by the parent investigation's Anti-Drift Hazard against a
bare dict/list literal for key storage, reconfirmed here against the real `RuntimeProfile`/
`ConfigLoader` code.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: no entry currently covers HTTP authentication (parent
  investigation's finding, reconfirmed — grepped the file for "auth"/"api_key"/"credential", no
  hits). A new entry is required once implemented. Next available sequential ID is `INFRA-377`
  (highest existing ID confirmed via file tail is `INFRA-376`); confirm this is still true at
  Implement/Parity time in case a concurrent ticket has claimed it meanwhile.
The API-key auth mechanism (hashed storage, constant-time comparison, `ClientIdentity` shape) is
a new, named, durable-state-adjacent pattern with no existing documentation home — it needs a
writeup the same way `WorkerManager`/`ObservabilityController` are documented, not left implicit
in `src/api/auth.py`'s docstrings alone. Two candidate homes were considered: `docs/guidelines/
design_patterns.md` (path: `docs/guidelines/design_patterns.md`, under `docs/`) is not required to
change for this ticket — Plan should choose between it and a new `docs/architecture/` ADR
(matching this ticket's own `layer: architecture`), and only the chosen path is a real
requirement; do not treat both as required.

The `docs/engine/known_limitations.md` doc (path: `docs/engine/known_limitations.md`, under
`docs/`) is not required to change for this ticket: it is checked for whether it documents "no
HTTP authentication" as a scope boundary (`grep -i "auth" known_limitations.md` found no existing
mention), so there is no stale line to remove or update — a non-issue for this ticket
specifically, unlike the parent epic's more general admission-control note which is a separate
doc's concern.
- `.claude/skills/api-design-principles/assets/api-design-checklist.md`: not a doc this ticket edits
  (it's a checklist to run against, not a record of behavior), but its two relevant checked-off
  items should be referenced in Implementation Notes as evidence of compliance — see below.

## Parity Ledger Overlap

- No existing `docs/parity_ledger/infrastructure.yaml` entry covers HTTP auth (confirmed above) —
  this ticket adds a new entry, does not modify an existing one. Suggested `text` should record:
  storage format (hashed-at-rest, `hmac.compare_digest` comparison), the config field name/type
  once Plan finalizes it, and the route-exemption list. `status: verified` once implemented, with a
  real `test_path` pointing at the new `tests/api/test_api_key_auth.py` (per schema.json, `status:
  verified` requires both `v2_evidence` and `test_path` to be non-null strings).
- `INFRA-364` (CORS wildcard+credentials fix) and `INFRA-365` (`GovernorPolicy.from_mode()`) —
  both cited by the parent investigation as adjacent-but-not-overlapping; reconfirmed not relevant
  to auth specifically (CORS governs cross-origin browser behavior, not credential validation).

## Prior Work

- Parent investigation (`staging_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/investigation.md`)
  — read in full; its findings on `create_v2_app()`'s overall shape, the `V2EngineManager` locking
  model, the "no repo-wide credential-storage/constant-time-comparison precedent" conclusion, and
  the recommendation to store keys hashed-at-rest via `hmac.compare_digest` + `ConfigLoader` are
  reused, not re-derived, and remain accurate against a direct re-read of the same files.
- `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG` (done) — immediately-preceding hotfix
  on the same file; its test (`tests/api/test_cors_config.py`) is this ticket's own cited template,
  confirmed to use the exact `TestClient(create_v2_app(PROD_DEFAULT))` pattern (see Regression
  Surface in test_plan.md).
- No prior ticket in `tickets/done/` or `stored_artifacts/` addresses API authentication — this is
  genuinely new subsystem territory, matching the parent investigation's conclusion.

## Risks and Open Questions

- **Open — route exemption list (ticket's own open question, resolved below with a recommendation,
  not a decision).** Recommend exempting exactly one route: **`/health`**. Reasoning: (1) it is the
  literal liveness probe this repo's own test convention already names as such
  (`tests/api/test_health_liveness.py`'s docstring: "liveness-aware route wiring"); (2) the ticket's
  own Scope section already states the intent ("not a blanket middleware that would also gate
  framework-level routes like `/health` if not careful"), i.e. the requester has effectively
  pre-decided this; (3) infra liveness probes (k8s-style, load-balancer health checks) conventionally
  run unauthenticated because the probing agent is the orchestration layer itself, not a tenant
  client, and gating it would risk false-negative liveness failures cascading into unwanted restarts
  if the key-provisioning path ever breaks independently of the engine's actual health.
  **Recommend NOT exempting `/metrics`**, despite it being a "sometimes exempt" candidate in other
  systems: no existing convention in this repo treats it as infra-only (unlike `/health`, no test or
  doc names it a probe-equivalent), it exports operationally sensitive data (`sim_gold_circulation_total`,
  `sim_hard_law_violations`, entity counts) that the ticket's own Request Summary says is now
  reachable "on the public internet, multi-tenant," and Prometheus scrape configs support
  bearer/custom-header auth natively, so exempting it buys no real operability benefit. This is a
  recommendation for Plan to ratify or override, not a final decision.
  **The two dashboard routes (`/api/v1/observability/ui`, and its two redirects
  `/observability/ui`, `/api/v1/observability/live/ui`) should NOT be exempted** — they expose live
  simulation internals — but this surfaces a real, unresolved usability gap: the dashboard is meant
  to be opened directly in a browser, and a plain browser navigation cannot attach a custom
  `X-API-Key`-style header. **This is a genuine open question for Plan**, not something Investigate
  should silently resolve — options include a query-string key parameter (weaker: keys end up in
  server access logs/browser history) or leaving the dashboard's own browser-facing auth story as an
  explicit Out-of-Scope/known-limitation note for this ticket. Flagging, not deciding.
- **Open — RuntimeProfile is semantically resource-envelope-only; adding auth-secret material to it
  is a genuine layering tension, not a clean fit, even though it is the only existing typed
  CLI>Env>YAML>Defaults surface in the repo.** Recommend proceeding anyway (per parent
  investigation's direction to reuse `ConfigLoader`, not invent a new config path) but naming the
  new field narrowly and documenting the tension in Implementation Notes, e.g.
  `api_key_hashes: str = Field(default="", description=...)` — see the concrete design below. The
  field **must** stay a plain `str` (not `List[str]`/`Dict[str,str]`) or `ConfigLoader`'s env-var
  loop crashes with an uncaught `TypeError` (see Current Behavior) — parsing into a structured
  client-id→hash mapping must happen downstream, in the new auth module, not in `RuntimeProfile`
  itself.
- **Open — regression surface on `tests/api/test_scenario_runtime_api.py`.** This file's `client`
  fixture builds `create_v2_app(RuntimeProfile(name="test", ...))` and its ~14 assertions call
  `/api/v1/scenarios/...` routes (the `scenarios` router, one of the 9 mounted sub-routers) with no
  auth header. If the `scenarios` router gets the auth dependency at its `include_router()` call
  site (recommended mechanism, see below), every one of these calls will start returning 401 unless
  the fixture's `RuntimeProfile` is seeded with a valid test key and every `client.get`/`client.post`
  call in the file is updated to send it (or the fixture attaches a default header to the
  `TestClient` itself, e.g. `TestClient(app, headers={"X-API-Key": "..."})` — cleaner, one-line
  fixture change vs. touching ~14 call sites). Flagged concretely for Test Plan/Implement, not
  silently assumed away.
- **Open — `tests/observability/test_metrics_export.py::test_metrics_endpoint_integration`** launches
  a real subprocess server (`python3 -m src serve ...`) and scrapes `/metrics` over real HTTP with
  no key. If `/metrics` is not exempted (this investigation's recommendation), this test needs a
  key supplied to both the subprocess's env (`RPG_API_KEY_HASHES=...`, confirming the env-var path
  actually works end-to-end) and the `requests.get(...)` call's headers. This is the one test in the
  regression surface that is a genuine integration/subprocess test, not an in-process `TestClient`
  one — worth calling out because it validates the full CLI→env→ConfigLoader→server chain, which no
  other existing auth-adjacent test does.

## Anti-Drift Hazards

- Do not add `dependencies=[Depends(require_api_key)]` to any of the 9 `src/api/routes/*.py` /
  `src/api/ws/stream.py` / `src/simulation_quality/api/routes.py` `APIRouter(...)` constructor
  calls. **The clean mechanism is to pass `dependencies=[...]` to each `app.include_router(...)`
  call inside `server.py` itself** (FastAPI supports `dependencies=` at both `APIRouter()`
  construction time and `include_router()` call time — the latter composes without touching any of
  the 9 router files, confirmed by FastAPI's own dependency-injection model and consistent with
  this repo's existing pattern of `server.py` being the sole place routers are wired together).
  Editing each router file individually would be unnecessary scope creep and duplicated
  auth-wiring logic across 9 files.
- Do not silently exempt any inline route beyond `/health` without documenting the reasoning in
  Implementation Notes — in particular, do not reflexively exempt `/metrics` just because "metrics
  endpoints are sometimes public" in other systems; this repo has no such convention and the data
  it exposes is sensitive per the ticket's own stated multi-tenant-public-internet threat model.
  Do not exempt `/api/v1/control/pause`/`/resume` (lifecycle-mutation endpoints) or
  `/api/v1/test/publish_event` (event-injection endpoint) — these are the most consequential
  unauthenticated writes in the current surface and are explicitly named as a concern in the
  ticket's own Request Summary.
- Do not add the new API-key field to `RuntimeProfile` as anything but a plain `str` type — see the
  `ConfigLoader` env-var-loop `TypeError` risk above. Do not store the parsed
  client-id→hash structure back onto the frozen `RuntimeProfile` instance (it's frozen, and
  auth-parsing logic doesn't belong in a resource-envelope contract) — parse once inside the new
  auth module and hold the parsed mapping in that module's own state, keyed off the profile at
  `create_v2_app()` call time.
- Do not touch `src/api/routes/control.py`, `health.py`, or `state.py` (empty, unwired dead files) —
  reconfirmed still empty and still unrelated to this ticket, per the parent investigation's same
  flag.
- Do not let `ClientIdentity` become a response-schema type in `src/api/schemas.py` — that file is
  explicitly scoped to outbound response shapes (its own module docstring), and `ClientIdentity` is
  a request-scoped, internal auth artifact, not something ever serialized back to a caller. Give it
  its own home in the new auth module.
