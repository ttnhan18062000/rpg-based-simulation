---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
phase: open
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT

## Title
Delete the unused requirements.txt export and repoint what pinned it

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`requirements.txt` is a `uv export` that no installer consumes: every CI job runs `uv sync --locked`. uv recommends against keeping both a `uv.lock` and a `requirements.txt` (brief section 1 and 2). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`. Order: after A1 (independent; ordered after it only to keep one PR's edits to `test.yml` readable).

## Scope
- Delete `requirements.txt`
- Remove it from the PERF/MIG path regexes in `.github/workflows/test.yml` (make sure `pyproject.toml` and `uv.lock` are in them) and the pin in `tests/static/test_ci_narrow_path_filtered_jobs.py`
- Keep the intent of `tests/static/test_ci_requirements_no_ml_stack.py` (the ML stack never reaches CI installs) by asserting it on the default dependency groups of `pyproject.toml` / `uv.lock`; fix its stale `pip install -r` comment
- Update the export comments in `pyproject.toml` and the human docs that say to use `requirements.txt` (`agent_working_environment.md`, `migration_ci_lanes.md`, `performance_profiling.md`)

## Out of Scope
- `requirements-knowledge.txt` (proposed to agent-working in the batch A handoff, not ticketed)
- Any file under `src/`
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [ ] No live reference to `requirements.txt` outside history (done tickets, stored artifacts, monitoring data)
- [ ] `tests/static` and `tests/tools` pass
- [ ] `make knowledge-index-update` is run, or its skip is noted
- [ ] `git diff --stat` lists no path under `src/`
- [ ] The testing notice (owner decision 8.11) is in the batch PR's handoff

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
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
- requirements.txt
- .github/workflows/test.yml
- tests/static/
- pyproject.toml
- docs/guidelines/

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
