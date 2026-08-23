---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC
artifact_type: investigation
tags: [architecture, observability]
---

# Investigation — TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC

## Search-Before-Grep Note

`mcp__knowledge-search__search_docs` was called first, per the Context Scan hard rule, with query
"HTTP admission control per-client rate limiting API key auth NORMAL PRESSURE DEGRADED SURVIVAL".
It returned `{"error":"index not found","action":"run make knowledge-index"}` — a confirmed,
persistent outage this session hit repeatedly. No retry was attempted; investigation proceeded to
`graphify query` per the fallback ordering. Two `graphify query` calls (`"HTTP admission control
API auth server.py"`, `"src/api/server.py CORSMiddleware"`) were re-run and expanded on, surfacing
`src/api/server.py::create_v2_app`, `src/api/engine_manager.py::V2EngineManager`,
`src/observability/config.py::ObservabilityConfig`, and the `.claude/skills/api-design-principles/`
assets — consistent with what the orchestrator's prior run had already found. All further findings
below come from reading the actual source and docs these queries pointed at.

## Current Behavior

**`src/api/server.py::create_v2_app()`** (2378 lines total; lines 1–277 are the FastAPI app/route
wiring, lines 278–2369 are an inline HTML string for `/api/v1/observability/ui`, a developer
dashboard — not relevant to this ticket beyond confirming it is also unauthenticated).

- Framework: FastAPI. `app = FastAPI(title="V2 RPG Simulation Engine", version="2.0.0",
  lifespan=lifespan)` (line 66).
- Middleware stack, in registration order: `CORSMiddleware` (lines 76–81,
  `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]`, no `allow_credentials` —
  already fixed by `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`, see parity entry
  INFRA-364), then `GZipMiddleware` (line 83). **No auth middleware, no rate-limit middleware, no
  admission-control middleware of any kind exist today.**
- Dependency injection pattern: a plain module-level singleton in `src/api/dependencies.py`
  (`set_engine_manager`/`get_engine_manager`, `set_quality_hub`/`get_quality_hub`, etc. — no
  request-scoped state, no `Depends()`-based auth pattern exists yet to mirror). Routes that need
  the engine use `Depends(get_engine_manager)` purely for the engine singleton, not for auth.
- Routes: 9 `include_router()` calls (`stream`, `history`, `search`, `behavior`, `decisions`,
  `scenarios`, `campaigns`, `chronicle`, `economy`, plus `quality_routes`), all mounted at
  `/api/v1` with zero per-router auth dependency, plus ~15 routes defined inline in
  `create_v2_app()` itself (`/metrics`, `/health`, `/api/v1/observability/live/*`,
  `/api/v1/state`, `/api/v1/inspect`, `/api/v1/entities*`, `/api/v1/control/pause`,
  `/api/v1/control/resume`, `/api/v1/test/publish_event`, etc.). All are open, unauthenticated,
  unrate-limited GET/POST endpoints, including two lifecycle-control mutation endpoints
  (`/api/v1/control/pause`, `/api/v1/control/resume`).
  `src/api/routes/control.py`, `health.py`, `state.py` exist as empty files — dead/unused, not
  wired into `create_v2_app()`; the inline routes duplicate what their names suggest. Not part of
  this ticket's scope, but worth noting as a pre-existing dead-code condition an implementer could
  otherwise mistake for "the control routes" when searching by filename.
- Concurrency/state safety: `V2EngineManager` (`src/api/engine_manager.py`) guards engine state
  with `self._state_lock = threading.Lock()` (`engine_manager.py:39`), taken around every state
  mutation/read (`engine_manager.py:75,150,192,200,207,214,221,233,287,293,343,354`). FastAPI's
  async event loop is single-process; this lock is what makes concurrent request handling safe
  against the engine's own tick loop, not anything HTTP-layer-specific.
- No existing test subprocess-launches the server; the established test pattern
  (`tests/api/test_cors_config.py`, `tests/api/test_health_liveness.py`) is in-process:
  `TestClient(create_v2_app(PROD_DEFAULT))`.

## Mechanics / Engine Constraints

- **`docs/architecture/observability_hot_path_safety_contract.md` §5 (OBS-BACKPRESSURE,
  INFRA-199)** is the actual, already-implemented four-mode vocabulary this ticket must extend:
  `NORMAL` (<70% fill) / `PRESSURE` (70–90%) / `DEGRADED` (90–100%) / `SURVIVAL` (≥100%), defined
  as `ObservabilityMode(str, Enum)` and evaluated by the pure function
  `ObservabilityController.evaluate(queue_fill_ratio)` in `src/observability/event_recorder.py`
  (lines 23–54). This is the literal source of the mode names the ticket's acceptance criteria
  cite — confirmed exact string match. §5 also documents the accessor contract this ticket should
  mirror: `observability_status() -> dict` (mode, ratio, dropped count, survival counts) and
  `reset_mode()` for test cleanup — a template for an equivalent `admission_status()`/
  `reset_admission_mode()` pair at the HTTP layer.
- **A second, distinct four-mode vocabulary already exists in the engine core** —
  `RuntimeMode(IntEnum)` in `src/core/governance.py` (`NORMAL=0, CONSTRAINED=1, DEGRADED=2,
  SURVIVAL=3`), driving `PhaseBudgetGovernor` (`src/engine/phase_governor.py`) and
  `GovernorPolicy.from_mode()` (`src/engine/policy.py`, parity entry INFRA-365). This vocabulary
  names its second tier `CONSTRAINED`, not `PRESSURE`. **The two vocabularies are not
  interchangeable and this ticket must pick one to extend, not both** — see Anti-Drift Hazards.
  Ticket acceptance criteria and `docs/audits/D23_architecture_resilience.md` §L both use
  `NORMAL/PRESSURE/DEGRADED/SURVIVAL`, which is `ObservabilityMode`'s exact naming, not
  `RuntimeMode`'s. Plan should extend/mirror `ObservabilityMode`'s vocabulary and pattern, and
  should not silently rename to `RuntimeMode`'s `CONSTRAINED`.
- **The actual hysteresis/threshold-crossing-with-cooldown mechanism referenced by the epic doc
  and D23 §L lives in `ResourceGovernor.evaluate()` (`src/engine/governor.py`), not in
  `PhaseBudgetGovernor`** as both docs state. `PhaseBudgetGovernor.evaluate()` is a pure consumer
  of an already-decided `RuntimeMode` — it has no hysteresis logic of its own. The real pattern is:
  escalation is immediate on any indicated-mode increase (`governor.py:43-45`), recovery is gated
  by `_can_recover()` requiring (a) `status.mode_dwell_ticks >= profile.dwell_time_ticks` and (b)
  `confidence_window_ticks` consecutive samples all below `recovery_watermark`-scaled thresholds
  (`governor.py:103-146`), and recovery steps down exactly one `RuntimeMode` level at a time
  (`governor.py:50`, "Law: Monotonic recovery"). `RuntimeProfile` already carries the exact tunable
  knobs this pattern needs (`recovery_watermark`, `dwell_time_ticks`, `confidence_window_ticks` —
  `src/config/profiles.py:42-44`), so an HTTP-layer admission controller reusing this pattern can
  reuse these same profile fields rather than inventing new ones. This is a factual correction to
  carry into Plan, not a blocker.
- **`docs/audits/D23_architecture_resilience.md` §L itself is internally inconsistent about the
  4th mode's name**: its introductory sentence says "extend NORMAL / PRESSURE / DEGRADED /
  SURVIVAL to the HTTP layer" but its own per-mode bullet list names the 4th tier `EMERGENCY`
  instead of `SURVIVAL`. The ticket's acceptance criteria say `SURVIVAL` (matching the
  observability layer's real vocabulary and the intro sentence). Plan should use `SURVIVAL` to
  stay consistent with the actual reused source (`ObservabilityMode`) and the ticket's own
  acceptance criteria, and should flag the `EMERGENCY` naming in §L as the design doc's own
  drafting inconsistency, not a real 5th option to reconcile.
- **`src/engine/worker_manager.py::WorkerManager`** (parity entry INFRA-017/PERF-010) is the
  other cited precedent bulkhead: `threading.Semaphore(effective_cap)` throttle plus an explicit
  `max_queue_depth` fallback to synchronous execution once `_inflight_count >= max_queue_depth`
  (confirmed via `docs/audits/D23_architecture_resilience.md` §E, not independently re-read line
  by line in this pass — the audit's citations of `worker_manager.py:56,106,118-124` were treated
  as sufficiently precise since this ticket's own Related Code Areas is `src/api/server.py` only).
  This is a bulkhead-with-fallback pattern, distinct from the mode-vocabulary pattern above; the
  D23 doc cites it as evidence real governance exists, not as something the HTTP layer must
  literally reuse.

## Docs Requiring Update

- `docs/plans/http_admission_control_epic.md`: still frames this epic as gated/dormant
  ("Priority: P2 — explicitly gate on deployment plans") — needs updating to reflect the
  2026-08-23 activation, and should be corrected to resolve the `PhaseBudgetGovernor` /
  `ResourceGovernor` attribution and the `SURVIVAL`/`EMERGENCY` naming inconsistency inherited
  from D23 §L before Plan finalizes a design against it.
- `docs/architecture/observability_hot_path_safety_contract.md`: if the HTTP-layer admission
  controller literally reuses `ObservabilityMode`/`ObservabilityController` (recommended, see
  Anti-Drift Hazards) rather than a parallel copy, §5's "EventRecorder supports four dynamic
  modes" framing needs a line noting the HTTP layer is now also a consumer of this vocabulary —
  otherwise this contract will read as observability-subsystem-only while the code has grown a
  second, unrelated caller.
- `docs/parity_ledger/infrastructure.yaml`: two updates needed — (1) a new entry (or an update to
  INFRA-199) recording that the HTTP layer now surfaces a mode-driven admission state, with a real
  `test_path`; (2) a new entry for the per-client API-key auth mechanism itself (storage,
  hashing/comparison method, key issuance assumption) since no entry currently covers HTTP auth at
  all.
- `docs/guidelines/design_patterns.md` (or a new `docs/architecture/` ADR, per this ticket's own
  layer): the per-client API-key auth mechanism and the HTTP admission-control state machine are
  new durable-state-adjacent concepts (see Risks — key storage location, admission-mode-per-client
  state) that should get a design-pattern or ADR-shaped writeup once implemented, matching how
  `WorkerManager` and `ObservabilityController` are documented as named, citable patterns rather
  than left implicit in code.
- `docs/engine/known_limitations.md`: currently makes no mention of the HTTP layer having no
  admission control — worth a line update once this ships, since the doc's purpose is to state
  current scope boundaries and this was a real, audited boundary until now.

## Parity Ledger Overlap

- `INFRA-364` (`docs/parity_ledger/infrastructure.yaml:10699`) — `verified`, P2. CORS
  wildcard+credentials fix, already resolved by
  `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`. Not reopened by this ticket; cited
  only because it's the CORS half of the same original epic scope, extracted before this session.
- `INFRA-365` (`infrastructure.yaml:10717`) — `verified`, P2. `GovernorPolicy.from_mode()`
  concurrency-limit-by-`RuntimeMode` rationale. Directly relevant as the "other" mode vocabulary
  this ticket must not accidentally conflate with (see Mechanics/Engine Constraints above).
- `INFRA-199` (`infrastructure.yaml:2284`) — `verified`, **P1**. The exact
  `NORMAL/PRESSURE/DEGRADED/SURVIVAL` vocabulary definition and behavior this ticket extends, with
  a real `test_path: tests/unit/observability/test_obs_backpressure.py`. **This is a P1 entry that
  the HTTP-layer extension must not regress** — if implementation touches
  `ObservabilityController`/`ObservabilityMode` directly (e.g. adding an HTTP-specific evaluate
  variant to the same module) rather than building a parallel HTTP-side controller, the existing
  `test_obs_backpressure.py` suite becomes part of this ticket's regression surface and must stay
  green.
- No existing parity entry covers HTTP authentication, per-client rate limiting, or an HTTP-layer
  admission state machine — both the auth mechanism and the admission-control mechanism are
  documentation gaps today, not just implementation gaps (see Docs Requiring Update).

## Prior Work

- `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG` (done): removed
  `allow_credentials=True` from `CORSMiddleware`. Directly relevant as the immediately-preceding
  hotfix on the exact file this ticket touches; its `test_path` (`tests/api/test_cors_config.py`)
  is the template this ticket's own middleware tests should follow (in-process `TestClient`, no
  subprocess, asserting real response headers not just constructor args).
- `docs/plans/http_admission_control_epic.md` and `docs/audits/D23_architecture_resilience.md`
  §E/§G/§L/R6: the original design source for this epic (read in full — see corrections above).
- No repo-wide credential-storage or constant-time-comparison convention exists to reuse (see
  Risks — this ticket must establish the pattern, not follow one). `hashlib.sha256` appears
  repeatedly elsewhere in the repo (`src/rendering/variants.py`, `src/worldmodules/repository.py`,
  `src/content/repository.py`, `src/engine/checkpoint.py`, etc.) but exclusively for content
  fingerprinting/determinism hashing, never for credential hashing or comparison — these are not a
  usable precedent for API-key storage, just confirmation that `hashlib` is an already-imported,
  familiar module in this codebase.
- `requirements.txt` already lists `pyjwt==2.13.0` and `redis==7.3.0` as dependencies. Per the
  requester's explicit 2026-08-23 decision, JWT is out of scope for auth — `pyjwt` presumably
  serves some other already-existing purpose in the repo and should not be treated as an implicit
  nudge toward JWT-based auth. `redis` is already available if per-process in-memory rate-limit
  state (the D23-recommended default, "sufficient at current scale") later proves insufficient
  under a real multi-worker-process deployment — flagged as a future option, not something to
  build now (Out of Scope explicitly excludes new distributed infra).

## Risks and Open Questions

- **Open — API key storage location and format is not decided by the ticket and has no repo
  precedent.** The ticket resolves *that* auth is per-client API key, not *where* keys/hashes are
  persisted (env var list, YAML file, SQLite, a new `AuthoritativeState`-adjacent structure) or
  *how* they're compared (plaintext env-var equality vs. `hashlib.sha256` digest vs.
  `hmac.compare_digest` constant-time compare against a hash). No `secrets`/`hmac`/constant-time
  comparison pattern exists anywhere in this repo to follow (confirmed via repo-wide grep — zero
  hits outside content-fingerprinting `hashlib.sha256` uses). This is a real design decision for
  Plan, not something Investigate should silently assume — recommend: hashed-at-rest keys (never
  plaintext), `hmac.compare_digest` for constant-time comparison against the hash, loaded via the
  existing `RPG_`-prefixed env var / YAML precedence pattern in `src/config/loader.py::ConfigLoader`
  (CLI > Env > YAML > Defaults) rather than inventing a new config-loading path — but this is a
  recommendation for Plan to confirm, not a decision already made.
- **Open — per-client admission-mode state is new durable-ish state with no existing lifecycle.**
  `ObservabilityMode` is a single global mode; extending it "per-client" means either (a) a
  dict keyed by client ID with its own mode/dwell-tick/confidence-window state per entry (unbounded
  by default — a noisy set of many distinct client IDs could grow this dict unboundedly; needs an
  eviction/TTL policy for stale clients), or (b) reusing `ResourceGovernor`'s
  `RuntimeStatus`-shaped pattern per-client. Neither is free — this is real per-client state that
  needs a bound, unlike the existing single global `ObservabilityMode`/`RuntimeMode` instances.
  This is likely the single largest genuinely new design surface in this ticket and should get
  explicit attention in Plan.
- **Tier/split question (ticket's own open question, addressed directly):** Investigation confirms
  this is **two substantially independent concerns** bolted into one ticket: (1) per-client API-key
  authentication (new credential storage/validation, ~1 middleware + config surface, no existing
  precedent to reuse — genuinely new subsystem), and (2) per-client HTTP admission control (new
  per-client state dict, mode-vocabulary extension, hysteresis reuse from `ResourceGovernor`,
  wiring into existing routes/middleware). They share only the "add a FastAPI middleware to
  `server.py`" mechanism and the fact that admission control conceptually depends on requests
  already being attributable to a client (which requires auth to exist first — a real sequencing
  dependency, not just a scope-convenience grouping). Given (a) neither existing repo precedent for
  credential storage, (b) the per-client state-bounding design question above, and (c) this
  session's own investigation already surfacing two distinct doc/parity-ledger update sets — this
  should be **split into two child tickets**: an auth ticket (must land first, since admission
  control needs a client identity to key on) and an admission-control ticket (built against the
  now-existing per-client identity). Recommend: keep this ticket as an epic/tracking parent (as it
  originally was before the 2026-08-18 downgrade) or split now into
  `TCK-20260817-HTTP-API-KEY-AUTH` and `TCK-20260817-HTTP-PER-CLIENT-ADMISSION-CONTROL`, sequenced
  auth-first. This reverses the 2026-08-18 downgrade decision, but that decision was made when the
  scope was still dormant/hypothetical; the real per-client state design surfaced above is bigger
  than what that downgrade anticipated ("bigger than the other downgrades... but still fit one
  standard-tier ticket" — the per-client state-bounding problem specifically was not part of that
  assessment, since the deployment plan wasn't real yet). **This is a recommendation for Plan/the
  orchestrator to act on, not a decision Investigate is authorized to make unilaterally.**
- **Open — key issuance/provisioning is explicitly Out of Scope, but the auth ticket still needs
  at least one concrete key to test against.** Plan needs to define a minimal
  operator-provisioning path (e.g., a CLI/env-var-seeded key list) that is not "self-service key
  management" (excluded) but is enough to make the auth mechanism testable and operable at all.

## Anti-Drift Hazards

- **Do not silently converge the two existing mode vocabularies.** `ObservabilityMode`
  (`NORMAL/PRESSURE/DEGRADED/SURVIVAL`) and `RuntimeMode`
  (`NORMAL/CONSTRAINED/DEGRADED/SURVIVAL`) are separate, independently-tested enums serving
  separate subsystems. The ticket's acceptance criteria specifically name the `ObservabilityMode`
  vocabulary — extending `RuntimeMode` instead, or introducing a third parallel enum with yet
  different names, would violate the ticket's own acceptance criteria even if functionally similar.
- **Do not attribute the hysteresis mechanism to `PhaseBudgetGovernor` in code comments or docs.**
  Both `docs/plans/http_admission_control_epic.md` and D23 §L do this; it is incorrect.
  `PhaseBudgetGovernor` has no hysteresis — `ResourceGovernor.evaluate()`/`_can_recover()` does.
  Propagating the wrong attribution into new code comments would compound an existing doc error.
- **Do not let admission-control implementation reach into `Engine`/`Kernel` internals.** The
  natural boundary is FastAPI middleware + `V2EngineManager`'s already-exposed read surface (e.g.
  an engine-pressure/governor-mode read, if admission control's DEGRADED trigger is meant to key
  off the engine's own `RuntimeMode` per D23 §L's "trigger: engine governor itself is in DEGRADED"
  design) — not new direct imports of `src/engine/governor.py`'s internals into `src/api/`, which
  would cross the API/engine module boundary this repo's layering otherwise respects (API reads
  engine state through `V2EngineManager`, never engine internals directly).
- **Do not implement API-key storage as a bare Python dict/list literal in source.** That would be
  durable secret material stored as an untyped, unversioned, hardcoded value — a Hard Rule
  violation ("Do not create hidden or implicit durable behavior", "Do not mutate durable state
  outside authoritative flows" analog for secrets). Must go through a typed config surface
  (Pydantic model, following `RuntimeProfile`'s pattern) loaded via `ConfigLoader`'s existing
  precedence chain or an equivalent typed loader, not inline.
- **Do not scope-creep into building distributed/shared rate-limit state (Redis-backed or
  otherwise) even though `redis` is already a dependency.** Out of Scope explicitly excludes new
  distributed infrastructure; D23 §L explicitly recommends single-process in-memory
  token-bucket/sliding-window as sufficient. `redis` being present is not license to use it here.
- **Do not touch `src/api/routes/control.py`, `health.py`, or `state.py`** (the empty, unwired
  route files) as part of this ticket — they are a pre-existing, unrelated dead-code condition,
  not part of this ticket's scope, and fixing them would be scope creep.
