# Implementation Sequence — repo-root-layout

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. Filed 2026-10-08 by codebase-implementer from
`docs/plans/codebase_health/repo_root_layout_ticket_brief.md` (codebase-planner; owner decisions 2026-10-08).
Two batches, one PR each. Batch B starts only after batch A has merged.

## Batch A: defects

1. TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK  (A1; heavy docker build, foreground under the memory cap)
2. TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT  (A2; edits CI-pinning tests, notice to testing in the PR handoff)
3. TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC  (A3; hotfix)

## Batch B: layout (after batch A merges)

4. TCK-20261008-OPS-FILES-INTO-DOCKER-DIR  (B1; after A1)
5. TCK-20261008-DROP-MAKE-BAT  (B2; hotfix)
6. TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL  (B3)
7. TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD  (B4; last, its allowlist is the root after A and B)

Every ticket: no `src/` diff. Tests that pin CI or the Makefile may be edited under owner decision 8.11.
