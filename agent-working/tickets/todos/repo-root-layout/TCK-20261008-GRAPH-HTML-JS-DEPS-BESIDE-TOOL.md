---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
phase: open
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL

## Title
Move the graph-html JS dependencies next to the tool that uses them

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
`package.json` and `package-lock.json` at the root are used only by `tools/graphify_to_html.py:33-34`, which reads `node_modules/` relative to the working directory. No Makefile target, no CI, no root `npm install` exists (brief section 1, 3 B3). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`. Order: after A (batch A merged).

## Scope
- Move `package.json` and `package-lock.json` next to the tool (directory name per `docs/guidelines/repo_tooling_layout.md`)
- `graphify_to_html.py` resolves `node_modules/` relative to that directory, not the working directory, with a clear error if it is missing; update its usage line and the two docs that mention it

## Out of Scope
- Adding an npm install step to CI or the Makefile
- A JS workspace (the three JS apps are unrelated, brief section 2)
- Any file under `src/`
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [ ] A test pins the resolution path (no network, no npm in CI)
- [ ] No `package.json` at the repo root
- [ ] `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
- TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
- TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
- TCK-20261008-DROP-MAKE-BAT
- TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Related Docs
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/graphify_to_html.py
- package.json
- package-lock.json
- docs/guidelines/repo_tooling_layout.md

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
