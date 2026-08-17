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
EPIC_SCOPED

## Tier
epic

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
- Scope-only epic: full findings and proposed remediation steps (including a full mode-vocabulary
  design reusing the observability layer's existing NORMAL/PRESSURE/DEGRADED/SURVIVAL states) are
  in `docs/plans/http_admission_control_epic.md`. Detailed, investigated child tickets are not
  created yet.
- When work begins: run `create-tickets` against a proposal document scoped to this epic's items
  (CORS fix, auth, admission-control mode vocabulary), producing investigated child tickets in
  `tickets/todos/http-admission-control/`.

## Out of Scope
- Any new message broker, service mesh, or distributed rate-limiting infrastructure.
- Starting this work before there's an actual deployment plan beyond a trusted network.

## Acceptance Criteria
- [ ] `docs/plans/http_admission_control_epic.md` is reviewed and its scope confirmed accurate.
- [ ] A deployment-plan decision gates when this epic is actually picked up.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

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
- Auth mechanism choice (API key, OAuth, etc.) is an open decision for whoever scopes the child
  ticket.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
