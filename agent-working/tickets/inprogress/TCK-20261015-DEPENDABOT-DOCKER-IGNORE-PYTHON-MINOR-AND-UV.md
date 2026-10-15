---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261015-DEPENDABOT-DOCKER-IGNORE-PYTHON-MINOR-AND-UV
phase: inprogress
date: 2026-10-15
tags: [platform]
---

# TCK-20261015-DEPENDABOT-DOCKER-IGNORE-PYTHON-MINOR-AND-UV

## Title
Dependabot docker ecosystem: stop proposing Python minor-line moves and uv bumps for the backend image

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Dependabot #576 ("docker-minor-patch") moved `docker/backend.Dockerfile` from `python:3.13.16-slim` to `python:3.14.8-slim`
and `ghcr.io/astral-sh/uv` from 0.11.2 to 0.13.1. The image check `Image runs the CI Python` failed correctly: CI,
`uv.lock` and `setup-uv python-version` are on 3.13. The uv pin must move together with CI's `setup-uv` `version:` input,
which Dependabot cannot bump. Owner decision 2026-10-15: add ignore rules. Python 3.14 waits for rpg's dependency
window, and uv gets manual bumps that change both pins together.

## Scope
- `.github/dependabot.yml`, docker ecosystem `ignore:` (beside the existing node rule):
  - `python`: `versions: [">=3.14"]`, following the node rule's pattern. Python 3.13.x patch updates still come through.
    Comment: widen it when rpg moves CI and the lockfile to the next line.
  - uv image: ignore all versions, with a comment pointing to the Dockerfile header and test.yml's `setup-uv` `version:`.
    Check the exact `dependency-name` Dependabot uses for a ghcr image, using #576's own update metadata
    (`ghcr.io/astral-sh/uv` vs `astral-sh/uv`).
- PR body: supersedes Dependabot #576; the user closes it.

## Out of Scope
Moving to Python 3.14 (rpg). Bumping uv (separate manual ticket when wanted). Other ecosystems.

## Acceptance Criteria
- dependabot.yml parses, and GitHub's Dependabot config check shows no error after merge (validated).
- The next monthly docker run proposes no python ≥3.14 and no uv bump (observed; append it to the ticket after the run,
  as for TCK-20261014-DEPENDABOT-GROUPED-MAJORS-MONTHLY).

## Related Tickets
TCK-20261014-DEPENDABOT-GROUPED-MAJORS-MONTHLY (same file; still open, waiting on its first grouped run).

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1)

## Related Stored Artifacts
None.

## Related Code Areas
`.github/dependabot.yml`, `docker/backend.Dockerfile` (read only)

## Assumptions / Open Questions
Security updates are not governed by version-update ignores in the same way. If one proposes Python 3.14, it is
handled by hand.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
