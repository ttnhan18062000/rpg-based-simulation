---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT
phase: open
date: 2026-08-20
tags: [architecture]
---

# TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT

## Title
Verify whether frontend/ (2+ months stale, the actual dockerized game UI) still builds cleanly

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P3

## Request Summary
Live session investigation into the repo root beyond `src/`/`tests/` found 3 frontend-shaped
directories. Two are confirmed healthy and intentional: `dashboard-frontend/` (agent-ops
dashboard) has its own dedicated, documented Makefile lifecycle
(`dashboard-install`/`dashboard-build`/`dashboard-dev`/`dashboard-serve`), separate from
docker-compose by design, not a gap; `website/` (Docusaurus docs site) deploys via its own GitHub
Pages CI workflow, also intentional. The one real open question: `frontend/` — the actual
docker-composed game UI (`frontend.Dockerfile` explicitly builds `COPY frontend/ .`) — is 2+
months stale (last commit 2026-06-12) with no `node_modules` installed locally, unlike
`dashboard-frontend/`. Whether that staleness reflects a stable, feature-complete component or
silent drift/breakage wasn't determined by this investigation — a cheap, decisive test
(`npm install && npm run build`) was identified but not run.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- Run `npm install && npm run build` in `frontend/` — the decisive test.
- If it builds cleanly: document the finding (no fix needed, staleness is healthy) so this doesn't
  get re-flagged as a false alarm in a future audit.
- If it fails: triage and fix the actual breakage.
- Either way, confirm the containerized build path (`frontend.Dockerfile`) also succeeds, not just
  the bare npm build.

## Out of Scope
- `dashboard-frontend/`'s or `website/`'s deployment posture — both confirmed intentional and
  healthy, not touched by this ticket.
- Adding a `docker-compose.yml` service for `dashboard-frontend/` — explicitly not warranted.

## Acceptance Criteria
- [ ] `frontend/`'s current build health is verified, not assumed.
- [ ] Any real breakage found is fixed, not just documented.
- [ ] The containerized build path (`frontend.Dockerfile`) is confirmed working too.

## Related Tickets
None — this ticket originates from live session investigation, not the D23/D24 audit tree.

## Related Docs
None beyond this ticket's own staging artifacts.

## Related Stored Artifacts
staging_artifacts/TCK-20260820-STANDARD-FRONTEND-DEPLOYMENT-POSTURE-AUDIT/

## Related Code Areas
- frontend/
- frontend.Dockerfile
- docker-compose.yml (frontend service)

## Assumptions / Open Questions
- Whether `frontend/`'s staleness is healthy-stable or actual drift is exactly what this ticket's
  Step 1 resolves — genuinely not known in advance, not pre-judged either way.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
