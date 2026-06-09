# Test Delta Budget

**Status:** Active  
**Last updated:** 2026-06-09  
**Relates to:** docs/testing/no_duplication_test_policy.md, docs/testing/content_migration_test_ownership.md

This document sets hard budgets for how many new tests each task type may add. The goal
is to keep the test suite proportional to the behaviors it protects, not proportional to
the amount of code written.

---

## Budget Table

| Task type | Test budget | Notes |
|---|---|---|
| **New small resolver** (single-class, isolated) | 3–6 unit tests | In the owning unit suite. See resolver rules in no_duplication_test_policy.md |
| **New YAML schema / authoring form** | 3–8 unit tests | Extend existing schema test file; no new file per field |
| **New registry adapter** | 3–5 unit tests | In `tests/unit/core/` or `tests/unit/content/`; not one test per heuristic |
| **New medium integration feature** (resolver + adapter + pipeline) | 1–2 integration tests | One happy-path, one failure-mode. Matrix pattern if N configs |
| **New strict matrix scenario** (new module set) | 1 parametrized matrix row | Add to `tests/integration/content/test_strict_world_matrix.py` |
| **New content pack** (new world module YAML) | 3 total: 1 manifest + 1 validation + 1 strict matrix row | No per-record tests |
| **New architecture guard** | 1–3 architecture tests | 1 gate test + up to 2 smoke tests. In `tests/architecture/` |
| **Bug fix** | 1 regression test | Reproduces the failure; added alongside the fix |
| **Refactor with no behavior change** | 0 new tests | Existing tests cover behavior. Update if API changes |
| **Doc-only ticket** | 0 tests | Docs do not require test coverage |

---

## Budget by Phase (29–34 Reference)

These are the totals actually added in Phases 29–34 for reference:

| Phase group | Tickets | Tests added | Within budget? |
|---|---|---|---|
| Schema & scenario models (tck 1–7) | 7 | ~50 | Yes — averaged 7/ticket; larger tickets had integration coverage |
| Test markers & taxonomy (tck 8–10) | 3 | ~80 | Yes — strict matrix adds parametrized rows, not individual tests |
| Compat & migration (tck 11–13) | 3 | ~24 | Yes — 10 schema, 9 bootstrap, 5 architecture |
| Docs & policy (tck 14–18) | 5 | 0 | Yes — doc-only |

---

## Justification Process for Budget Overruns

A task may exceed its budget **only if all three conditions are met**:

1. **Unique behavior**: The additional tests cover a behavior not protected by any
   existing test. Name the specific behavior gap.

2. **Cannot be data-driven**: The additional tests cannot be collapsed into a
   parametrized assertion over existing test infrastructure.

3. **Not duplicate of existing coverage**: Verify against the ownership map
   (`content_migration_test_ownership.md`) that no other file already owns this behavior.

Document the justification in the ticket's `## Implementation Notes` section before
committing. A reviewer must acknowledge it.

---

## What Counts as "One Test"

For budget accounting:
- One `def test_*` function = one test.
- A `@pytest.mark.parametrize` with N cases = one test (with N parametrized runs). The parametrize decorator is **encouraged** to stay within budget.
- An `xfail` test counts as one test against the budget.
- Tests in `conftest.py` fixtures do not count toward budget.

---

## Budget Enforcement

This budget is enforced by code review, not programmatically. The reviewer checks:
1. Count new `def test_` lines in the PR diff.
2. Divide by the task type budget.
3. If overrun: ask for justification per the process above or request consolidation.

---

## Cross-Reference

- **Duplication rules:** `docs/testing/no_duplication_test_policy.md`
- **Suite ownership:** `docs/testing/content_migration_test_ownership.md`
- **Test classification:** `docs/testing/v2_test_taxonomy.md`
