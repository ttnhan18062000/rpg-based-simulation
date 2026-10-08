---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD
phase: open
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Title
Pin the tracked repo-root entries to an allowlist with a guard test

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
After batches A and B the root holds only entries that belong there. A guard keeps it that way: a new root entry needs an owner decision, like a domain root (brief section 3 B4). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`. Order: after B1, B2 and B3 (last).

## Scope
- New "Repo root" section in `docs/guidelines/repo_tooling_layout.md`: the tracked root allowlist after A and B, and the rule that a new root entry needs an owner decision
- `tests/codebase/test_repo_root_allowlist.py`: the tracked root entries (`git ls-files` top level) equal the allowlist; the failure message names the guideline

## Out of Scope
- Local, untracked clutter (`uvicorn.log`, `tmp/`, `scratch/`, `reports/`): ignored, not tracked (brief section 5)
- `perf_baselines.json` and `skills-lock.json` decisions (other owners)
- Any file under `src/`
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [ ] The new test passes on a root matching the allowlist and fails, naming the guideline, on an extra tracked root entry
- [ ] The guideline section lists the allowlist
- [ ] `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
- TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
- TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
- TCK-20261008-DROP-MAKE-BAT
- TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL

## Related Docs
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/guidelines/repo_tooling_layout.md
- tests/codebase/

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
