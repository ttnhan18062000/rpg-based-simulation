---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-DEPENDABOT-AND-BASE-IMAGE-PINS
phase: done
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-DEPENDABOT-AND-BASE-IMAGE-PINS

## Title
Add Dependabot, pin every container image by digest, and make the frontend build use `npm ci`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
DevOps step 1, Dependabot. Today only `redis` is pinned by digest. `node:20-alpine`, `nginx:alpine`,
`python:3.13-slim`, and the prometheus/grafana/loki/promtail tags can all change with no diff, and the frontend
image runs `npm install`, which ignores the lockfile.

## Scope
- **Pins:** every `FROM` in `docker/*.Dockerfile` and every `image:` in `compose.yaml` becomes `name:exact-tag@sha256:...`,
  with a one-line comment in the `redis` style. `ghcr.io/astral-sh/uv:0.11.2` keeps its version, which stays in step with
  `test.yml`, and gains a digest.
- `docker/frontend.Dockerfile`: `npm install` becomes `npm ci` (`frontend/package-lock.json` exists).
- **`.github/dependabot.yml`**, weekly, with grouped minor/patch updates and `open-pull-requests-limit` of 5 per ecosystem:
  - `docker` (directory `/docker`), `docker-compose` (`/`), `github-actions` (`/`), `npm` (`/frontend`), `uv` (`/`).
  - PR labels allow routing: a Dependabot PR is reviewed by the owner of the file it changes (`uv.lock` and
    `frontend/**` → rpg; `test.yml` actions → testing; everything else → platform).

## Out of Scope
Auto-merge of Dependabot PRs. Renovate. Bumping any version now (pin what is current, no upgrades).

## Acceptance Criteria
- No unpinned image reference is left (shown with a grep in the Test Summary).
- `docker compose config -q` passes, and the CI build from child 2 still builds both images.
- GitHub's Dependabot config check accepts the file (after merge, the Insights → Dependency graph → Dependabot page shows
  no errors). Before merge, the PR claims "validated (schema)".

## Related Tickets
Epic `TCK-20261014-EPIC-DEVOPS-STEP1-CONTAINERS-DELIVERY`. Do it after child 1, because both edit `compose.yaml`.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1, Dependabot)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/*.Dockerfile`, `.github/dependabot.yml` (new)

## Assumptions / Open Questions
- Dependabot PRs for `test.yml` and `uv.lock` touch other domains' files. Send testing-planner and rpg-planner an fyi
  when this lands. No action is asked of them now.

## Implementation Notes
All `FROM` lines and `image:` entries pinned `tag@sha256` (multi-arch index digests current 2026-10-14, no version bumps); `npm install` -> `npm ci`; `.github/dependabot.yml` with docker (/docker), docker-compose (/), github-actions (/), npm (/frontend), uv (/): weekly, minor/patch grouped, limit 5. Labels `dependencies`, `platform`, `rpg` do not exist in the repo yet (checked with `gh label list`): Dependabot will skip them with a warning until they are created.
- Base images pin the exact tag behind the current digest: `python:3.13.16-slim`, `node:20.20-alpine3.23`, `nginx:1.31.6-alpine3.24` (tags checked against Docker Hub digests), so Dependabot PRs show a real version change. The user chose (via platform-planner) to create the labels: `dependencies`, `platform` and `rpg` now exist (`gh label create`, 2026-10-14); `dependabot.yml` is unchanged.
## Test Summary
- **validated (schema):** YAML parses; Dependabot's own check runs after merge.
- Unpinned-reference grep (`grep -E '^\s*(image:|FROM) ' compose.yaml docker/*.Dockerfile | grep -v @sha256`) returns nothing.
- **running locally:** the full stack above was built from these Dockerfiles (including `npm ci`) and started.
- CI build via `publish-images.yml` on this PR to confirm (**validated** once green).
- **validated (Dependabot):** GitHub parsed the file and opened 21 PRs on its first run, so the config is accepted. The first run exceeded the PR limit, and most were semver-major bumps; follow-up `TCK-20261014-DEPENDABOT-IGNORE-MAJOR-BUMPS` ignores majors and moves to monthly.

## Files Changed
- `docker/backend.Dockerfile`, `docker/frontend.Dockerfile`, `compose.yaml`, `.github/dependabot.yml`
## Completion Summary
Every base image is pinned by exact tag and digest, the frontend installs with `npm ci`, and Dependabot is configured. Merged in #561.
