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

**(2026-08-19)** Deployment-plan decision confirmed by the requester: this API surface **stays on
a trusted network**, no public/untrusted exposure planned. Per this ticket's own gating criterion,
auth and admission control stay explicitly deferred — not investigated further, not scoped into
child tickets, until that decision changes. The one item that was always independent of the
deployment question — the CORS config fix — was extracted into
`TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`.

Remaining scope (deferred, not actionable until the deployment decision changes):
- Add authentication to the API surface before any deployment beyond a trusted network.
- Add HTTP-layer admission control by extending the existing NORMAL/PRESSURE/DEGRADED/SURVIVAL
  vocabulary to the HTTP layer rather than inventing a new scheme; a single in-process
  token-bucket/sliding-window limiter is sufficient at current scale.

## Out of Scope
- Any new message broker, service mesh, or distributed rate-limiting infrastructure.
- Starting this work before there's an actual deployment plan beyond a trusted network.

## Acceptance Criteria
- [x] CORS config item extracted — see `TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG`.
- [ ] At least one auth mechanism gates the API surface — deferred, not actionable until the
      deployment decision changes.
- [ ] HTTP requests are admitted/throttled/shed according to a mode vocabulary consistent with
      the observability layer's existing NORMAL/PRESSURE/DEGRADED/SURVIVAL states — deferred.
- [x] Deployment-plan decision confirmed (2026-08-19): trusted network only. This epic stays open
      but dormant until that changes.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG (item 1 extracted from here, 2026-08-19)

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
- **(2026-08-19) Resolved:** deployment target confirmed as trusted-network-only by the requester.
  Re-open auth/admission-control investigation only if that changes.
- Auth mechanism choice (API key, OAuth, etc.) remains an open decision for whenever this epic is
  actually picked up.
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
