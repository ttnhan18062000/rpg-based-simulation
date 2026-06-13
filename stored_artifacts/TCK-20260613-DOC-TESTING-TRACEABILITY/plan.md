---
ticket_id: TCK-20260613-DOC-TESTING-TRACEABILITY
artifact: plan
date: 2026-06-13
---

# Plan: TCK-20260613-DOC-TESTING-TRACEABILITY

## Objective

Create three new docs in `docs/testing/` that complete the testing contract system:
1. `docs/testing/requirement_traceability.md`
2. `docs/testing/regression_policy.md`
3. `docs/testing/how_to_add_requirement_tests.md`

## Authoring Order

Write in this order so each doc can reference the previous:
1. **requirement_traceability.md** — establishes the map (ground truth)
2. **regression_policy.md** — defines gates and triage (references traceability groups)
3. **how_to_add_requirement_tests.md** — authoring guide (references both prior docs)

## Doc 1: docs/testing/requirement_traceability.md

### Purpose
A living map from simulation laws and requirement groups to the concrete test files that protect them.

### Required Content
- Frontmatter: `status: active`, `layer: testing`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`
- Introduction: why traceability matters (agent navigation, regression investigation)
- Master traceability table with columns: Requirement Group | Example Behavior | Test File(s) | Markers | Authority
- Rows covering: resource conservation, API security, API history, live observability, combat legality, performance correctness, world determinism, progression correctness
- All test file paths must be verified real files (confirmed in investigation)
- Section: "How to keep this map current" — manual update obligation when behavior changes
- Link to `docs/testing/v2_test_taxonomy.md` for marker definitions
- Link to `docs/parity_ledger/` for P0 law parity evidence

### Source data (from investigation)
All test paths confirmed via `ls` and file inspection. See investigation.md §3-§9.

## Doc 2: docs/testing/regression_policy.md

### Purpose
Defines what a regression is, which test groups are hard gates vs soft monitors, and how to triage a failing gate test.

### Required Content
- Frontmatter: same as doc 1
- Hard gates section: test groups that block merge on failure (certification/, integration/kernel/ determinism, integration/pipeline/ mutation/conservation, perf/ thresholds)
- Soft monitors section: test groups that alert but don't block (observability flow tests, slow scenario tests)
- Definition of regression vs expected behavior change
- Triage checklist for a failing gate test (5–7 concrete steps)
- When a test can be updated vs when it signals a real regression
- Authority rule for P0 test updates (must update parity ledger in same session)
- Link to `docs/performance/perf_baseline_policy.md` for numeric thresholds
- Link to `docs/testing/requirement_traceability.md` for requirement group definitions
- Link to `docs/testing/v2_test_taxonomy.md`

## Doc 3: docs/testing/how_to_add_requirement_tests.md

### Purpose
Step-by-step authoring guide for adding a test that protects a specific simulation law.

### Required Content
- Frontmatter: same as doc 1
- Behavior test vs requirement test distinction (with examples)
- Standard pattern: `# REQ:` comment block → setup → assert law not violated → assert correct mutation
- Naming convention for requirement tests (for traceability map lookup)
- How to mark tests with correct taxonomy marker from `docs/testing/v2_test_taxonomy.md`
- How to add an entry to `docs/testing/requirement_traceability.md` after adding a test
- How to verify parity ledger is updated for P0 laws
- Worked example: adding a test for the atomic conservation law (resource transfer)
  - Uses `tests/integration/pipeline/test_transaction_completion.py` as model
  - Shows full pattern: docstring citing law, setup, resolver call, assertion on atomicity
- Links to all three related docs

## Implementation Constraints

- All test file paths cited must exist (verified in investigation.md)
- No existing docs modified (out of scope per ticket)
- No test files created (doc-only ticket, 0 test budget)
- `docs/testing/v2_test_taxonomy.md` linked from all three docs

## Post-Implementation Steps

1. Run `python3 tools/validate_frontmatter.py` on each new doc
2. Run `make docs-registry`
3. Run `pytest tests/docs/ -v`
4. Run `make knowledge-index-update`
5. Move ticket to `tickets/done/`
6. Append to `tickets/working_log.csv`
7. Move staging artifacts to `stored_artifacts/`
