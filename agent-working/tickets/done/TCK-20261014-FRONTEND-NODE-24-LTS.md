---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-FRONTEND-NODE-24-LTS
phase: done
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-FRONTEND-NODE-24-LTS

## Title
Frontend build image: Node 20 → Node 24 LTS

## Status
DONE

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
`docker/frontend.Dockerfile`: builder is `node:24.21.0-alpine3.24@sha256:ebfe2f90...` (exact tag behind the digest; confirmed with imagetools). `frontend/package.json` has no `engines` field and there is no `.nvmrc`/`.node-version`, so nothing mismatches and nothing was reported to rpg.
## Test Summary
- **running locally:** the image built with `npm ci && npm run build` on Node 24.21.0 and the frontend container reached `healthy` in the full stack (host under heavy load from other sessions).
- CI build of the image via `publish-images.yml` on the PR: to confirm (**validated** once green).
- **validated (CI):** publish-images on main at 5324afafe (run 38682866242) built `images (frontend, docker/frontend.Dockerfile)` on Node 24.21.0: success; the #586 PR run was green too.

## Files Changed
- `docker/frontend.Dockerfile`
## Completion Summary
The frontend image builds on Node 24 LTS.
