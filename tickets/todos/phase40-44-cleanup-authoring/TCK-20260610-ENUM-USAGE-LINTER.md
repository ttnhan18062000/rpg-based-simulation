# TCK-20260610-ENUM-USAGE-LINTER

## Title
Add architecture test enforcing enum usage boundaries with allowlist

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Phase 40.2 requires an architecture test that prevents new direct `Faction`/`EntityRole` enum usage from spreading into clean catalog-driven modules while migration is ongoing. The test scans source files, compares against an explicit allowlist, and fails CI if forbidden enum usage is found.

## Scope
- Add `tests/architecture/test_legacy_enum_usage_boundaries.py`
- Scan source files for direct `Faction.` / `EntityRole.` enum references
- Allowlist (enum usage permitted): compatibility adapters, legacy fallback modules, legacy/compatibility tests, migration map, enum definition files, explicit legacy-mode tests
- Forbidden list (must have zero occurrences): new clean resolvers, catalog-driven systems, world assembly logic, relation projection logic, scenario setup resolver, content pack systems
- Test failure message must name the violating file and suggest the correct adapter/resolver

## Out of Scope
- Fixing existing violations (only detection, no forced migration in this ticket)
- Linting other non-catalog enum patterns (ActionStyle, QuestKind, etc.)

## Acceptance Criteria
- [ ] Architecture test scans source files for `Faction.` and `EntityRole.` references
- [ ] Allowlist is explicit and documented in the test
- [ ] Forbidden modules list is explicit and documented
- [ ] Test passes on current codebase (violations in allowed modules only)
- [ ] Adding a new enum usage in a forbidden module causes test failure
- [ ] Failure message names file, line, and suggests replacement

## Related Tickets
- TCK-20260610-ENUM-REWARD-INFLUENCE (companion cleanup)
- TCK-20260610-ENUM-MIGRATION-REPORT (companion report)

## Related Docs
- `docs/guidelines/design_patterns.md`

## Related Code Areas
- `tests/architecture/` — new test file
- `src/content_semantics/faction.py` — allowlisted adapter
- `src/entities/identity_resolver.py` — correct replacement path

## Assumptions / Open Questions
- Does `tests/architecture/` directory already exist? Check before creating `__init__.py`.

## Implementation Notes
<!-- Fill during implementation -->

## Test Summary
<!-- Fill after implementation -->

## Files Changed
<!-- Fill after implementation -->

## Completion Summary
<!-- Fill after completion -->
