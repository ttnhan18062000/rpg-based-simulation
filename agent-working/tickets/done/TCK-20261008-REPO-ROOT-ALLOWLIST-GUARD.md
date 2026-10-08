---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Title
Pin the tracked repo-root entries to an allowlist with a guard test

## Status
DONE

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
- [x] The new test passes on a root matching the allowlist and fails, naming the guideline, on an extra tracked root entry
- [x] The guideline section lists the allowlist
- [x] `git diff --stat` lists no path under `src/`

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
- New "Repo root" section in `docs/guidelines/repo_tooling_layout.md`: the rule (a new root entry needs an owner decision, like a domain root), the allowlist between `<!-- repo-root-allowlist:begin/end -->` markers (20 directories, 20 files, built from `git ls-files` at the top level after B1 to B3), and the note that `perf_baselines.json` (perf-planner asked to keep it at the root; they will say before moving it) and `skills-lock.json` (the external CLI's file) are kept on purpose.
- `tests/codebase/test_repo_root_allowlist.py` parses the allowlist from the guideline (single source, so test and doc cannot drift) and compares it with the first path components of `git ls-files -z`. The failure message names `docs/guidelines/repo_tooling_layout.md`, section "Repo root", and lists entries not on the list and entries on the list but no longer tracked.
- Only root entries count: first path components, so a new file under `src/`, `tools/`, `codebase/`, `agent-working/` or any existing directory never trips it (pinned by a synthetic test).

## Test Summary
- `tests/codebase/test_repo_root_allowlist.py`: 4 tests pass: real tracked root equals the allowlist; the parse is not vacuous (expected entries present, `requirements.txt`, `make.bat`, `package.json`, `backend.Dockerfile`, `grafana`, `scripts` absent); new files under `src/` or a domain root leave the root set unchanged; a new root file or directory is caught and the message names the guideline.
- Mutation proof: with `zz_extra.txt` added to the index, the real test failed with `Not on the allowlist ... ['zz_extra.txt']`; the file was then removed again.
- `make knowledge-index-update` not run (times out under the cap).

## Files Changed
- `docs/guidelines/repo_tooling_layout.md` (new "Repo root" section)
- new `tests/codebase/test_repo_root_allowlist.py`

## Completion Summary
The tracked repo root is pinned to an allowlist that lives in the tooling-layout guideline, with a guard test that fails on any new root entry, names the guideline, and ignores everything below the root.
