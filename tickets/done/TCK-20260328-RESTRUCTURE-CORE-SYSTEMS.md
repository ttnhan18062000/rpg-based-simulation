# Restructure Core & Systems into Domain-Based Subfolders

**Goal**: Organize the bloated 'src/core/' (31 files) and 'src/systems/' (22 files) directories into logical subfolders to improve maintainability and follow the architectural trend toward domain-driven features.

## Scope
- Restructure 'src/core/' into 'base/', 'entities/', 'world/', 'gameplay/', 'data/', and 'registry/'.
- Restructure 'src/systems/' into 'infrastructure/', 'world/', 'lifecycle/', 'gameplay/', and 'calamity/'.
- Update project-wide imports in 'src/', 'api/', 'tests/', and 'actions/'.

## Acceptance Criteria
- [ ] No circular dependencies introduced.
- [ ] Project-wide 749 tests passed.
- [ ] FastAPI application starts successfully.
- [ ] Frontend still renders correctly via 'state' API.

## Related Tickets
- RESTRUCTURE-01 (Architectural Vision)

**Tier:** standard
**Type:** chore
**Priority:** P1
