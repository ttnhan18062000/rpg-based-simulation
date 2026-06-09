# No-Duplication Test Policy

**Status:** Active  
**Last updated:** 2026-06-09  
**Relates to:** docs/testing/v2_test_taxonomy.md, docs/testing/content_migration_test_ownership.md

This document codifies rules that prevent test explosion as the Phase 29–34 resolver,
schema, adapter, and pipeline work continues. Violation of these rules results in
redundant test maintenance burden and obscures real coverage gaps.

---

## Core Rule

**Do not add a test that already has an owner.**

Before writing a new test, check `content_migration_test_ownership.md`. If the behavior
already has an owning file, extend that file rather than creating a new one.

---

## Rules by Scenario

### New resolver

When adding a new resolver class (e.g., `ScenarioSetupResolver`, `WorldAssemblyResolver`):

- Write **3–6 focused unit tests** covering:
  1. Happy path with minimal valid input
  2. Invalid input → specific error with ID context
  3. Edge case (empty collections, boundary value)
  4. Frozen/immutable output model
  5. No import of observability or side-effect modules (isolation)
- Do **not** write one test per field or one test per possible input value.
- Do **not** write a duplicate "resolver produces a result" test if the happy path already exists.

### New authoring form (new YAML schema or catalog record type)

When a new YAML schema is introduced (e.g., `migration_map.yaml`, world compositions):

- Extend the **existing schema test file** in `tests/unit/content/` rather than creating a new file.
- If no schema test file exists for that domain, create one — but include all rules for that schema type in the single file.
- Do **not** write a separate test file per field. Use parametrized or loop-based assertions.
- One schema test file per catalog family is the maximum; additional files require justification.

### New registry adapter

When adding a new `CatalogToXxxRegistryAdapter`:

- Unit tests go in `tests/unit/core/` or `tests/unit/content/` (depending on domain).
- Cover: happy-path adapt, missing-field heuristic, strict-mode rejection.
- Do **not** duplicate "catalog loads" behavior — that is owned by `tests/integration/worldassembly/`.
- Integration tests for adapter output go in `tests/integration/content/` or `tests/integration/worldassembly/`.

### New full pipeline (new bootstrap flow or authoritative mutation path)

When adding a new end-to-end pipeline (e.g., registry bootstrap, scenario setup, world assembly):

- Add **one data-driven matrix test** in the relevant `tests/integration/` suite.
- The matrix should parametrize across modes/configurations rather than adding one test per configuration.
- Do **not** duplicate "basic assembly works" in the matrix — that is owned by `tests/integration/worldassembly/test_real_content_world_modules.py`.
- See `tests/integration/content/test_strict_world_matrix.py` for the approved pattern.

### New content record

When new content records are added to the catalog (YAML):

- The **active-data-consumer gate** (`tests/integration/content/test_active_data_consumer.py`) covers all records automatically via reference graph scan.
- Do **not** write one test per new record or one test per new content family.
- If a record needs special validation (custom field constraint), add a parametrized assertion to the relevant schema test file.

### Legacy behavior preservation

When modifying a compatibility adapter or migration path:

- The existing registry bootstrap tests in `tests/unit/runtime/` cover mode routing.
- The architecture guard in `tests/architecture/test_no_new_hardcoded_gameplay_truth.py` covers new IDs.
- Do **not** add new per-ID tests. Update `KNOWN_HARDCODED_BASELINE` or `migration_map.yaml` instead.

---

## Explicit Prohibitions

| Prohibited pattern | Reason |
|---|---|
| Multiple "basic catalog loads" tests across files | Already owned by `tests/integration/worldassembly/test_real_content_world_modules.py` |
| Multiple "basic assembly works" tests across files | Already owned by `tests/integration/worldassembly/test_real_content_world_compositions.py` |
| One test file per content record | Use the reference graph gate instead |
| One test file per catalog family | Extend existing schema validation files |
| Architecture tests that load catalog or run simulation | Architecture tests must be static (file scan, regex, YAML parse only) |
| Integration tests in `tests/unit/` directories | Unit tests must not load real catalog, real simulation, or network |
| Separate test files for adapter heuristic inference | Extend the existing adapter test in `tests/unit/core/` |

---

## Data-Driven Coverage — Preferred Pattern

For content record testing, the matrix pattern is strongly preferred over individual tests:

```python
# PREFERRED: data-driven matrix
@pytest.mark.parametrize("module_id", KNOWN_MODULES)
def test_module_loads(module_id):
    ...

# PROHIBITED: one test per record
def test_frontier_module_loads():   ...
def test_goblin_camp_loads():       ...
def test_moon_cult_loads():         ...
```

When the same assertion applies to N records, use parametrize. When different assertions
apply to different records, that is a sign the records have different schemas — fix the
schema, not the tests.

---

## Cross-Reference

- **What goes where:** `docs/testing/content_migration_test_ownership.md`
- **Marker conventions:** `docs/testing/v2_test_taxonomy.md`
- **Per-phase budget for new tests:** `docs/testing/test_delta_budget.md`
