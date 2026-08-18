---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC
phase: open
date: 2026-08-17
tags: [architecture, observability]
---

# TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC

## Title
HTTP-layer auth, rate limiting, and admission control — gate on deployment plans

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`src/api/server.py` registers no rate limiting, no authentication, and no per-client admission
control on any REST endpoint; `CORSMiddleware` is also configured with a spec-invalid
`allow_origins=["*"]` + `allow_credentials=True` combination. Resource governance exists and
works well elsewhere (intra-tick `WorkerManager` bulkhead, `RedisStreamAdapter`'s backpressure) —
the gap is specifically that governance stops at the HTTP process boundary. Both source audits
explicitly gate this epic's priority on actual deployment plans — do not front-load if this
system stays on a trusted network.

## Scope
Full findings, including a full mode-vocabulary design reusing the observability layer's existing
NORMAL/PRESSURE/DEGRADED/SURVIVAL states, are in `docs/plans/http_admission_control_epic.md`.
Concrete scope:
- Fix the CORS `allow_origins`/`allow_credentials` configuration regardless of the broader auth
  decision — a pure config correctness fix.
- Add authentication to the API surface before any deployment beyond a trusted network.
- Add HTTP-layer admission control by extending the existing NORMAL/PRESSURE/DEGRADED/SURVIVAL
  vocabulary to the HTTP layer rather than inventing a new scheme; a single in-process
  token-bucket/sliding-window limiter is sufficient at current scale.

## Out of Scope
- Any new message broker, service mesh, or distributed rate-limiting infrastructure.
- Starting this work before there's an actual deployment plan beyond a trusted network.

## Acceptance Criteria
- [ ] CORS config no longer uses the spec-invalid wildcard+credentials combination.
- [ ] At least one auth mechanism gates the API surface.
- [ ] HTTP requests are admitted/throttled/shed according to a mode vocabulary consistent with
      the observability layer's existing NORMAL/PRESSURE/DEGRADED/SURVIVAL states.
- [ ] A deployment-plan decision gates when this ticket is actually picked up for implementation.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/http_admission_control_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md
- docs/architecture/observability_hot_path_safety_contract.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/api/server.py

## Assumptions / Open Questions
- The actual deployment target (trusted network vs. public exposure) determines urgency — not
  yet decided by the requester.
- Auth mechanism choice (API key, OAuth, etc.) is an open decision for Plan phase.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; the borderline case of the review — bigger than
  the other downgrades (auth is a real subsystem), but CORS+auth+admission-control-vocabulary
  still fit one standard ticket, especially since the mode vocabulary explicitly reuses an
  existing pattern rather than inventing one. `staging_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/` not yet created.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
