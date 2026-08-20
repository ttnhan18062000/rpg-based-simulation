---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG
phase: open
date: 2026-08-19
tags: [architecture]
---

# TCK-20260819-HOTFIX-CORS-WILDCARD-CREDENTIALS-MISCONFIG

## Title
Fix spec-invalid CORSMiddleware allow_origins=["*"] + allow_credentials=True combination

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Item 1 of `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC`, extracted into its own standalone ticket:
that epic's broader scope (auth, admission control) stays explicitly deferred per the user's
confirmed decision (2026-08-19) that this API surface stays on a trusted network — but the CORS
fix was always scoped as "regardless of the broader auth decision... a pure config correctness
fix," independent of the deployment question. Live-confirmed still present:
`src/api/server.py:73-78` configures `CORSMiddleware` with `allow_origins=["*"]` and
`allow_credentials=True` simultaneously — a combination the CORS spec disallows (a credentialed
request cannot use a wildcard origin). Browsers already reject the actual credentialed-wildcard
case today, so this is a config-hygiene/correctness fix (the middleware config is misleading about
what it actually permits), not a live exploit — consistent with staying low-priority while the
API remains on a trusted network.

## Scope
- Fix the CORS configuration in `src/api/server.py` to be spec-valid: either drop
  `allow_credentials=True` (if credentialed cross-origin requests aren't actually needed), or
  replace `allow_origins=["*"]` with an explicit, real origin allowlist.
- Confirm which of the two is actually correct by checking whether any real caller depends on
  credentialed cross-origin requests today (check `dashboard-frontend/` and any other real client)
  before picking a fix direction — don't guess.

## Out of Scope
- Authentication, rate limiting, or admission control — remains `TCK-20260817-HTTP-ADMISSION-
  CONTROL-EPIC`'s bundled scope, explicitly deferred pending a future deployment-plan change (this
  API surface is confirmed staying on a trusted network as of 2026-08-19).

## Acceptance Criteria
- [ ] `CORSMiddleware`'s configuration no longer combines a wildcard origin with credentials.
- [ ] Any real, currently-working caller (dashboard frontend or otherwise) is confirmed unaffected
      by the fix — verified, not assumed.

## Related Tickets
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC (item 1 extracted from here; that epic's remaining
  scope — auth, admission control — stays explicitly deferred, not touched by this ticket)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)

## Related Docs
- docs/plans/http_admission_control_epic.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- src/api/server.py

## Assumptions / Open Questions
- Whether to drop credentials or scope origins to an allowlist depends on whether any real caller
  needs credentialed cross-origin requests — left to the implementer to verify first.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
