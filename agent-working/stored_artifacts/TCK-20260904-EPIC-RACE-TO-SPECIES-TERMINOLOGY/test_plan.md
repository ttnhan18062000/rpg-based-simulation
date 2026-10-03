---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY
artifact_type: test_plan
tags: [content, schema]
---

# Test Plan — TCK-20260904-EPIC-RACE-TO-SPECIES-TERMINOLOGY

Not applicable at the epic level — no code changes here. Each child ticket owns its own test coverage
for the files it renames:

- Child 1 (core schema): existing `tests/unit/content/{test_catalog,test_layered_catalog,
  test_resolvers}.py`, `tests/unit/core/{test_catalog_fallback,test_hardening_e5,
  test_registry_bridge}.py`, `tests/unit/worldassembly/test_archetype_preservation.py`,
  `tests/unit/worldbuilding/test_world_compiler.py` must pass unchanged after the rename (a pure
  rename must not change any test's observed behavior, only the identifiers it asserts against).
- Child 2 (race-relations subsystem): the 6 dedicated test files must pass unchanged; each file's own
  name should be renamed to match (e.g. `test_race_relations_catalog.py` ->
  `test_species_relations_catalog.py`), per this repo's no-process-labels-in-identifiers convention
  extended to naming generally — a stale old-terminology filename would be exactly the kind of drift
  this epic exists to close.
- Child 3 (cross-cutting consumers): remaining consumer test files pass unchanged.
- Child 4 (docs/mechanics/parity sweep): `validate_frontmatter.py` and any parity-index build/health
  check pass after edits; no test file changes expected (docs-only).

No new tests are needed anywhere in this migration — it changes names, not behavior. A pure rename
that changes test outcomes would indicate the rename touched semantics it shouldn't have.
