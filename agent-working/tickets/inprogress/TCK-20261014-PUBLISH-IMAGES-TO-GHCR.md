---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-PUBLISH-IMAGES-TO-GHCR
phase: open
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-PUBLISH-IMAGES-TO-GHCR

## Title
New workflow `publish-images.yml`: build the backend and frontend images and publish them to GHCR

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
DevOps step 1, T2 (rebuilt here). No image is published today: the images exist only as local compose builds.

## Scope
- `.github/workflows/publish-images.yml`:
  - Triggers: `push` to `main`, tags `v*`, `workflow_dispatch`, and `pull_request` limited by `paths` to
    `docker/**`, `compose.yaml`, `pyproject.toml`, `uv.lock`, `src/**`, `frontend/**` and the workflow itself.
    Pull requests **build only, never push**.
  - Matrix over `backend` (`docker/backend.Dockerfile`) and `frontend` (`docker/frontend.Dockerfile`), context `.`.
  - `docker/setup-buildx-action` + `docker/build-push-action` with the GHA cache (`cache-from/to: type=gha`).
  - Images: `ghcr.io/${{ github.repository }}/backend` and `/frontend`. Tags come from `docker/metadata-action`:
    short sha, `main` on main, semver on `v*` tags. OCI labels (source, revision) too.
  - `permissions:` at least `contents: read`, plus `packages: write` only on the publishing job.
  - Third-party actions are pinned by full commit SHA with a version comment (Dependabot bumps them; child 4).
  - `concurrency` per ref, so a newer push cancels an older build.
- The job outputs each image's digest, which child 3 uses.

## Out of Scope
SBOM, scan and signing (child 3). Multi-arch builds (amd64 only for now). Changing `test.yml`.

## Acceptance Criteria
- A PR run builds both images and pushes nothing (**validated**).
- After merge, both images are visible in GHCR with sha and `main` tags, and `docker pull` of each works (**published**).
- The workflow passes `actionlint` (run locally or as a step).

## Related Tickets
Epic `TCK-20261014-EPIC-DEVOPS-STEP1-CONTAINERS-DELIVERY`; child 3 builds on this workflow.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1)

## Related Stored Artifacts
None.

## Related Code Areas
`.github/workflows/publish-images.yml` (new), `docker/*.Dockerfile`

## Assumptions / Open Questions
- The repo is public. A GHCR package created by `GITHUB_TOKEN` may start out **private**. Making it public is a
  one-time package-settings click for the **user**: report it in the PR rather than working around it.
- The "published" evidence can exist only after the user merges. Before that, the PR claims "validated".

## Implementation Notes
`.github/workflows/publish-images.yml`: push to main, `v*` tags, `workflow_dispatch`, and path-filtered pull requests. Matrix over backend/frontend, GHA cache, metadata-action tags (sha, branch, semver), OCI labels, actions pinned by full SHA with version comments, per-ref `concurrency`, `contents: read` top-level and `packages: write` on the job only. Digest is exposed as job outputs and as `steps.build.outputs.digest`.
## Test Summary
- **validated:** actionlint passes (rhysd/actionlint docker image); YAML parses.
- Matrix job-level `outputs` were removed (the last matrix leg to finish would overwrite them and nothing read them); the digest is used within the job via `steps.build.outputs.digest`. `cancel-in-progress` is PR-only.
- PR run builds without push (`push: false`, `load: true`): to be confirmed on this PR's Actions run (**validated** once green).
- **published:** to be confirmed after merge (images in GHCR with sha + `main` tags, `docker pull`). The package visibility click is needed by the user after the first publish.
## Files Changed
## Completion Summary
