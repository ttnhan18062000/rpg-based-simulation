---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Plan (from the ticket Scope and the dispatch)
1. `docker/backend.Dockerfile`, final stage: `ARG APP_UID=1000` / `APP_GID=1000`, create group and user `app` (no home, nologin shell), compile `/app/src` as root, `chown -R app:app /app/data`, `USER app`.
2. `compose.yaml`: pass `APP_UID`/`APP_GID` as build args on backend, ai_worker and watchdog; document in the header comment.
3. Check that nothing in the image needs root at runtime (port 8000, writes to `/app`, Python cache); report any `src/` write outside `/app/data` to platform-planner.
4. Note that `publish-images.yml` builds the same Dockerfile, so published images also run as uid 1000 (intended; no workflow change).

Commits: ef58585ff (static change), 90fba3ee3 (build and run proof).
