---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-TESTING-TRACEABILITY
phase: done
date: 2026-06-13
tags: [documentation, testing, requirement-traceability, regression-policy, test-taxonomy]
---

# TCK-20260613-DOC-TESTING-TRACEABILITY

## Title
Add Requirement Traceability, Regression Policy, and Test Authoring Guide to docs/testing/

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`docs/testing/` has 11 coverage documents (observability, progression, self-model, world-emergence, etc.) and a `v2_test_taxonomy.md` that classifies test types. However, it is missing three documents that agents and developers need to understand the test system as a whole:

1. **Requirement traceability** — there is no map from simulation behavior requirements to the tests that protect them. An agent investigating "what proves resource conservation works?" has no document to consult — it must grep `tests/` and hope to find the right file.

2. **Regression policy** — there is no document explaining which test groups are gate-level (must pass before merge), what constitutes a regression, and how to triage a failure. The `test_delta_budget.md` covers scope, but not policy.

3. **How to add a requirement test** — there is no authoring guide explaining how to add a test that protects a specific simulation law. Developers can model from existing tests but have no doc explaining the pattern.

These three documents close the gap between the test taxonomy (which classifies what exists) and the test contract (which explains what is required and how to maintain it).

## Scope
Create three new docs in `docs/testing/`:

1. **`docs/testing/requirement_traceability.md`** — A requirement-to-test traceability map. Structure:
   - Table mapping requirement groups to test files/markers
   - Requirement groups: API history, historical search, API security, live observability, resource conservation, performance correctness, combat legality, progression correctness, world determinism
   - For each group: requirement description, example behavior, test file(s), test marker(s) if any, authority level (P0/P1)
   - Must be derived from actual test files in `tests/` — no invented entries
   - Includes a section on how the map is kept current (manual update on behavior change)

2. **`docs/testing/regression_policy.md`** — Defines what a regression is and what to do. Covers:
   - Which test groups are hard gates (block merge on failure)
   - Which test groups are soft monitors (alert but don't block)
   - What constitutes a regression vs expected behavior change
   - How to triage a failing gate test (what to check, what docs to read)
   - When a test can be updated vs when it signals a real regression
   - Who has authority to update a P0 test requirement (must update parity ledger too)
   - How performance regression thresholds are defined (link to `docs/performance/perf_baseline_policy.md`)

3. **`docs/testing/how_to_add_requirement_tests.md`** — Authoring guide for adding tests that protect simulation laws. Covers:
   - The distinction between a behavior test (does it work?) and a requirement test (is the law protected?)
   - The standard pattern: requirement comment block → setup → assert law not violated → assert correct mutation occurred
   - How to name tests for the requirement traceability map
   - How to mark tests with the correct taxonomy marker
   - How to add an entry to `docs/testing/requirement_traceability.md` after adding a new test
   - How to verify parity ledger is updated if the test proves a P0 law
   - A worked example: adding a test for the atomic conservation law (resource transfer)

## Out of Scope
- Modifying `docs/testing/v2_test_taxonomy.md` (established taxonomy — this ticket links to it, doesn't replace it)
- Adding new tests (this is a documentation ticket)
- Modifying existing test files

## Acceptance Criteria
- [ ] `docs/testing/requirement_traceability.md` created. Contains a complete requirement-to-test table covering at minimum: resource conservation, API security, historical search, live observability, combat legality, performance correctness. All test file paths verified to exist in `tests/`. Frontmatter: `status: active`, `layer: testing`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.
- [ ] `docs/testing/regression_policy.md` created. Defines hard gates vs soft monitors. Includes triage checklist. Links to `perf_baseline_policy.md` and parity ledger. Frontmatter: same.
- [ ] `docs/testing/how_to_add_requirement_tests.md` created. Includes worked example using atomic conservation law test. Step-by-step guide is followable without reading source. Frontmatter: same.
- [ ] `docs/testing/v2_test_taxonomy.md` linked from all three new docs.
- [ ] `make knowledge-index-update` and `make docs-registry` run after completion.

## Related Tickets
- TCK-20260613-DOC-HARDENING-EPIC (parent)

## Related Docs
- `docs/testing/v2_test_taxonomy.md` — existing taxonomy (required reading before writing traceability)
- `docs/testing/test_delta_budget.md` — scope/budget for test additions
- `docs/performance/perf_baseline_policy.md` — performance regression thresholds
- `docs/compliance/checklist.md` — compliance gates
- `docs/parity_ledger/` — parity verification entries (linked from traceability where P0)

## Related Stored Artifacts
None

## Related Code Areas
- `tests/api/` — API history and security tests
- `tests/engine/` — engine-level tests
- `tests/integration/` — integration test suites
- `tests/architecture/` — architecture boundary tests
- `tests/perf/` — performance tests
- `tests/scenarios/` — scenario-based tests
- `tests/certification/` — certification suite

## Assumptions / Open Questions
- The requirement traceability map must be built from actual test inspection, not invented. Before writing the table, grep `tests/` for requirement-style comments (e.g., `# REQ:`, `# Law:`, `# REQUIREMENT`, `# fraud-detection`) to find requirement-annotated tests.
- If no requirement annotation convention currently exists, document the recommended convention in `how_to_add_requirement_tests.md` and note that existing tests should be annotated incrementally.

## Implementation Notes
1. Read `docs/testing/v2_test_taxonomy.md` first — understand the existing classification.
2. Grep `tests/` for requirement-style comments to find annotated tests.
3. Check `tests/api/test_cognition_history_api.py`, `tests/api/test_historical_event_search_api.py` — these are cited in the hardening plan as examples.
4. Build the traceability table from findings, then write the doc.
5. Write regression_policy after traceability is clear (it references the gate-level groups).
6. Write how_to_add last (it ties the other two together with a worked example).

**Actual findings (2026-06-13):**
- No uniform `# REQ:` annotation convention exists in the suite. Only `test_combat_legality_matrix.py` uses compliance-ID block comments. Most tests use docstrings or plain inline comments. Traceability map was built from file inspection.
- Registered pytest markers (from `pyproject.toml`): `slow`, `extra_slow`, `world_long_run`, `legacy_characterization`, `v2_contract`, `differential`, `intentional_divergence`, `regression`, `certification`, `perf`, `worldassembly`.
- 13 requirement groups mapped in traceability doc: resource conservation, grouped transfer rollback, API history, historical search, API security, live observability, WebSocket protocol, combat legality, performance correctness, world determinism, progression correctness, authoritative mutation boundary, kernel contract, replay fidelity.
- All test file paths in the traceability table verified via `ls` and file inspection.
- `how_to_add_requirement_tests.md` establishes `# REQ:` as the recommended annotation convention going forward.

## Test Summary
Not applicable — documentation ticket.

## Files Changed
- `docs/testing/requirement_traceability.md` (new)
- `docs/testing/regression_policy.md` (new)
- `docs/testing/how_to_add_requirement_tests.md` (new)

## Completion Summary
Created three new docs in `docs/testing/`:
1. `docs/testing/requirement_traceability.md` — 13-row requirement-to-test traceability table covering resource conservation (P0), API security (P0), combat legality (P0), world determinism (P0), API history, historical search, live observability, WebSocket protocol, performance correctness, progression correctness, authoritative mutation boundary, kernel contract, and replay fidelity. All test file paths verified. Frontmatter valid.
2. `docs/testing/regression_policy.md` — Hard gates vs soft monitors, regression triage checklist (7 steps), authority rules for P0 test updates, links to perf_baseline_policy.md. Frontmatter valid.
3. `docs/testing/how_to_add_requirement_tests.md` — Behavior vs requirement test distinction, standard `# REQ:` pattern, naming convention, taxonomy marker guide, traceability map update steps, parity ledger verification, full worked example (atomic conservation law). Frontmatter valid.

Frontmatter validation: all 3 docs passed `validate_frontmatter.py` with exit 0.
`make docs-registry`: regenerated cleanly — testing layer count 14 → 17.
`make knowledge-index-update`: 16 files indexed (incremental); `sentence-transformers` not installed is a pre-existing environment issue unrelated to this ticket.
`pytest tests/docs/ -v`: 4 passed, 5 failed, 1 skipped — all 5 failures are pre-existing (missing `docs/engine/supported_progression_surface_phase5.md` and other stale manifest entries). No new failures introduced by this ticket.
Staging artifacts moved to `stored_artifacts/TCK-20260613-DOC-TESTING-TRACEABILITY/`.
