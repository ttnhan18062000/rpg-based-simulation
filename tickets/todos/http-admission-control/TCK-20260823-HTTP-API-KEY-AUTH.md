---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260823-HTTP-API-KEY-AUTH
phase: open
date: 2026-08-23
tags: [architecture, security, api-design]
---

# TCK-20260823-HTTP-API-KEY-AUTH

## Title
Per-client API-key authentication for `src/api/server.py`

## Status
OPEN

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
- [ ] Every route in `src/api/server.py` requires a valid per-client API key, except any
      explicitly-justified exemption (e.g. a liveness probe) documented in Implementation Notes.
- [ ] An invalid, missing, or malformed key returns a proper 401/403 response, not a 500 or an
      unauthenticated pass-through.
- [ ] Keys are stored hashed-at-rest, never in plaintext, loaded through the existing
      `ConfigLoader` precedence chain.
- [ ] Key comparison uses constant-time comparison (`hmac.compare_digest`), not `==`.
- [ ] The resulting client-identity object is reusable by a future admission-control layer without
      rework (confirmed by this ticket's own design, verified by the sibling ticket's own
      Investigate phase when it starts).
- [ ] `tests/api/` gains real, in-process `TestClient`-based tests (following
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

## Test Summary

## Files Changed

## Completion Summary
