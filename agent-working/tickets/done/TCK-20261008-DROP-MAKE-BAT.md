---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-DROP-MAKE-BAT
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-DROP-MAKE-BAT

## Title
Delete make.bat; Windows users run make under WSL or Git Bash

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`make.bat` covers 19 of the Makefile's 145 targets and has been touched only incidentally since 2026-03; no other sampled project keeps a Windows duplicate. Owner decision 2026-10-08: keep Make, drop `make.bat` (brief section 3 B2, section 4). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`. Order: after A (batch A merged).

## Scope
- Delete `make.bat`
- Drop it from the scan list in `tests/codebase/test_code_health_install_git_hooks.py`
- README and CONTRIBUTING say Windows runs `make` under WSL or Git Bash

## Out of Scope
- Any change to the Makefile's targets
- Any file under `src/`
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [x] No live reference to `make.bat`
- [x] `tests/codebase/test_code_health_install_git_hooks.py` passes
- [x] `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
- TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
- TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
- TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
- TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Related Docs
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- make.bat
- tests/codebase/test_code_health_install_git_hooks.py
- README.md
- CONTRIBUTING.md

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes
Deleted `make.bat`. The only code reference was the scan list in `tests/codebase/test_code_health_install_git_hooks.py` (the opt-in-hooks needle scan); `make.bat` is removed from it. Neither README nor CONTRIBUTING named `make.bat` or Windows, so the Windows note is new: one sentence in README's Quick Start requirements line and one in CONTRIBUTING's Verification section (run `make` under WSL or Git Bash; there is no `make.bat`).

## Test Summary
`git grep make.bat` finds only history (tickets, stored artifacts, monitoring, plans, archive) and the two new sentences. `tests/codebase/test_code_health_install_git_hooks.py` and `tests/static`: 97 passed. `make knowledge-index-update` not run (times out under the cap).

## Files Changed
- deleted: `make.bat`
- `tests/codebase/test_code_health_install_git_hooks.py`, `README.md`, `CONTRIBUTING.md`

## Completion Summary
`make.bat` is gone, nothing live references it, and the docs say Windows users run `make` under WSL or Git Bash.
