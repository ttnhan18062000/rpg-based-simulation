---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
phase: open
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC

## Title
Move .nojekyll from the repo root into the docs site static folder

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`.nojekyll` at the root is inert: Pages deploys `website/build` through Actions. Docusaurus guidance puts it in `static/` (brief section 1 and 2). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`.

## Scope
- `git mv .nojekyll website/static/.nojekyll`

## Out of Scope
- Changing the Pages workflow (`deploy-docs.yml`)
- Any file under `src/`
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [ ] The docs site build still copies the file into `website/build/` (check locally if cheap, else state that it was not checked)
- [ ] No `.nojekyll` at the repo root

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
- TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
- TCK-20261008-DROP-MAKE-BAT
- TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
- TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Related Docs
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- website/static/
- .github/workflows/deploy-docs.yml

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
