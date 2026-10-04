---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-EXEMPLAR-MODULES
phase: inprogress
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-EXEMPLAR-MODULES

## Title
M6a: Exemplar modules in the package registry

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Fill `exemplar_modules` (0 to 3 paths) in `codebase/structure/package_registry.jsonl` for `active` packages by a written, repeatable criterion, so an agent can imitate a clean module.

## Scope
- Criterion measured on main: no row in `code_health_exceptions.jsonl` (any tool), about 60 to 400 lines, has a module docstring, not in any row's `do_not_imitate`; prefer modules other modules in the package import
- A package with no qualifying module gets `[]` (valid)
- Criterion and measurement command written as a new short section of `docs/plans/codebase_health/src_package_structure_audit.md`
- `reviewed` stays `false`; the owner reviews the picks in the PR
- `legacy` and `frozen` packages get no exemplars
- Test: every exemplar has no registry row at the commit (a future row for an exemplar is the signal to re-pick)

## Out of Scope
- Schema change
- `do_not_imitate` additions beyond what the measurement shows

## Acceptance Criteria
- [ ] Every `active` package has `exemplar_modules` set by the criterion (possibly `[]`); `legacy`/`frozen` have none
- [ ] Registry validator passes
- [ ] Criterion and command documented in the audit
- [ ] Pin test added and passes
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC

## Related Docs
- docs/plans/codebase_health/python_code_craft_m6_agent_integration_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/src_package_structure_audit.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/structure/
- docs/plans/codebase_health/
- tests/codebase/

## Assumptions / Open Questions
- Owner decision 8.17 (2026-10-04): codebase implements M6 although `.claude/**` is agent-working's territory; the PR body names agent-working as owner of those paths
- Nothing here blocks a PR or tool call; M4 and M5 soaks are not disturbed

## Implementation Notes
`codebase/structure/exemplars.py` (`measure`, `apply`); importer ranking counts absolute, relative and submodule forms from `src` only; `apply` rewrites only changed rows (byte-stable). 3 of 36 packages got picks (710 of 744 src files carry an exceptions row; the D2 path-banner filter dropped 8 more). The pin test asserts no exceptions row only, never existence (blocking lane).

## Test Summary
`tests/codebase/test_package_exemplars.py` + `test_package_registry.py`: 42 passed. `python3 -m codebase.structure.packages validate`: 0 problems. ruff clean on new files.

## Files Changed
codebase/structure/exemplars.py (new), codebase/structure/package_registry.jsonl, tests/codebase/test_package_exemplars.py (new), docs/plans/codebase_health/src_package_structure_audit.md, ticket and staging artifacts

## Completion Summary
