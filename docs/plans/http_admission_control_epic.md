---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, observability]
---

# Epic Plan — HTTP-Layer Admission Control & Auth

**Tracking ticket:** `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §E, §G, §L (R6)
**Priority:** P1 — the gating deployment-plan decision fired 2026-08-23: this API surface now goes
public internet, multi-tenant (was trusted-network-only). Originally P2, gated on that decision not
being made yet; now active, no longer front-loaded speculatively. See
`tickets/todos/http-admission-control/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC.md` for the full
2026-08-23 investigation and split into child tickets.

## Problem

`src/api/server.py` registers only `CORSMiddleware` and `GZipMiddleware` — no rate limiting, no
authentication, no per-client admission control on any REST endpoint. Separately,
`CORSMiddleware(allow_origins=["*"], allow_credentials=True)` is a spec-invalid combination
(browsers reject the actual credentialed-wildcard case, so it's inert today, but it signals
unreviewed middleware config regardless). Resource governance exists and works well elsewhere in
the system (the intra-tick `WorkerManager` bulkhead, `RedisStreamAdapter`'s severity-aware
backpressure) — the gap is specifically that governance stops at the process boundary between the
engine and the HTTP layer.

## Scope for the eventual `create-tickets` pass

- Fix the CORS `allow_origins`/`allow_credentials` configuration regardless of the broader
  auth decision — a pure config correctness fix.
- Add authentication to the API surface before any deployment beyond a trusted network.
- Add HTTP-layer admission control by extending the observability layer's existing
  NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary
  (`docs/architecture/observability_hot_path_safety_contract.md`) to the HTTP layer, rather than
  inventing a new scheme — full proposed mode design (trigger conditions, per-mode endpoint
  behavior, hysteresis pattern reusing `ResourceGovernor.evaluate()`/`_can_recover()`'s real
  escalation/recovery pattern, `src/engine/governor.py` -- **not** `PhaseBudgetGovernor`, which
  has no hysteresis of its own; the source doc's original text mis-attributed this to
  `PhaseBudgetGovernor`, corrected here by `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`) is
  in `docs/audits/D23_architecture_resilience.md` §L.
- A single in-process token-bucket or sliding-window limiter in the FastAPI middleware stack is
  sufficient at current scale — explicitly not a recommendation to add Kafka, a service mesh, or
  a generic rate-limiting framework (the RabbitMQ/Kafka situation elsewhere in this same repo is
  a live cautionary example of infrastructure added ahead of actual need).

## Out of scope

- Any new message broker, service mesh, or distributed rate-limiting infrastructure.
- Building this before there's an actual deployment plan beyond a trusted network — this epic's
  own priority is explicitly conditional on that.

## Acceptance signal for this epic

**Broken into child tickets as of 2026-08-23:** `TCK-20260823-HTTP-API-KEY-AUTH` (auth,
implementation complete, in the pipeline) and `TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`
(admission control, depends on the first, not yet started — see
`tickets/todos/http-admission-control/`).

- ~~CORS config no longer uses the spec-invalid wildcard+credentials combination.~~ **Resolved**
  (`TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`, 2026-08-20): `allow_credentials=True`
  removed from `src/api/server.py`'s `CORSMiddleware` config. Verified no real caller depends on
  credentialed cross-origin requests — `frontend/`'s `fetch()` calls carry no `credentials`
  option, and dev traffic is proxied same-origin (`frontend/vite.config.ts`); `dashboard-frontend/`
  is a separate app targeting a different backend entirely, not this one.
- ~~At least one auth mechanism gates the API surface.~~ **Resolved**
  (`TCK-20260823-HTTP-API-KEY-AUTH`, 2026-08-23): per-client API-key authentication now gates
  every route in `src/api/server.py::create_v2_app()` except `/health` (documented liveness-probe
  exemption). Keys are hashed-at-rest and compared via `hmac.compare_digest`. See
  `docs/architecture/http_api_key_authentication.md` for the full mechanism and route
  classification, and `docs/parity_ledger/infrastructure.yaml` `INFRA-377` for verification
  evidence. The `ClientIdentity` object this ticket establishes is designed for the next bullet's
  admission-control layer to key off directly.
- ~~HTTP requests are admitted/throttled/shed according to a mode vocabulary consistent with (and
  ideally reusing) the observability layer's existing NORMAL/PRESSURE/DEGRADED/SURVIVAL states.~~
  **Resolved** (`TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL`, 2026-08-23): per-client HTTP
  admission control now gates every protected route in `src/api/server.py::create_v2_app()`,
  extending `ObservabilityMode`'s NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary
  (`src/observability/event_recorder.py`, imported not modified) via a per-client token-bucket
  signal fed through a hysteresis state machine mirroring `ResourceGovernor`'s real
  escalation/recovery pattern. Only `SURVIVAL` rejects (`429`/WebSocket `1013`); `/health` remains
  the sole exemption. See `docs/architecture/http_admission_control.md` for the full mechanism and
  `docs/parity_ledger/infrastructure.yaml` `INFRA-378` for verification evidence.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic F)
- `docs/audits/D23_architecture_resilience.md` (R6, §L full design, Stage 3)
