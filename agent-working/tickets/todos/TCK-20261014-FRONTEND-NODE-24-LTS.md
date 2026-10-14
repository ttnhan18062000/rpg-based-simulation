---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-FRONTEND-NODE-24-LTS
phase: open
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-FRONTEND-NODE-24-LTS

## Title
Frontend build image: Node 20 → Node 24 LTS

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Node 20 is past end of life. The owner chose Node 24 LTS over Dependabot's #577 (Node 26, newly in LTS) on 2026-10-14.

## Scope
- `docker/frontend.Dockerfile`: `node:24.<x>.<y>-alpine<z>@sha256:...` (exact tag plus digest, current style).
- Check `frontend/package.json` `engines` and any `.nvmrc`/`.node-version`, and report mismatches to rpg (frontend/** is rpg's). Don't edit them.

## Out of Scope
Bumping frontend packages. Node in other workflows (owners' call).

## Acceptance Criteria
- The frontend image builds in publish-images CI (validated); `npm ci && npm run build` succeeds in the image.
- Default `docker compose up` frontend reaches healthy (running locally).

## Related Tickets
Dependabot #577 (superseded); sibling `TCK-20261014-DEPENDABOT-GROUPED-MAJORS-MONTHLY` (Node >=25 ignore).

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1, step 2)

## Related Stored Artifacts
None.

## Related Code Areas
`docker/frontend.Dockerfile`

## Assumptions / Open Questions
None.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
