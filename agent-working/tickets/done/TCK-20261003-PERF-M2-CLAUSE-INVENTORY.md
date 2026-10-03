---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-M2-CLAUSE-INVENTORY
phase: done
date: 2026-10-03
tags: [performance, documentation]
---

# TCK-20261003-PERF-M2-CLAUSE-INVENTORY

## Title
Clause-level inventory of the performance contract, certification contract, baseline policy, gate code, tests, and CI selectors (PERF-M2-T01; documents and read-only)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
PERF-D4 (owner-approved 2026-10-03) makes `docs/engine/performance_contract.md` the single clause-level authority for how performance is measured, compared, and claimed; makes `docs/engine/contracts/certification_contract.md` §3 the single hardware-class definition; reduces `docs/performance/perf_baseline_policy.md` to a calibration procedure; and defines two projections (tripwire and capacity run) with the outcomes `PASS` / `REGRESSION` / `INCONCLUSIVE` / `NOT_APPLICABLE`. Its stated uncertainty: "the clause-by-clause inventory (`PERF-M2-T01`) has not been done; this decision selects the authority and the shape, and the inventory may add clauses". PERF-D4 releases this ticket now. `PERF-M0-T09` applies the P1 edits after it, so the edits are driven by the inventory instead of by re-reading the documents.

## Scope
- Write `docs/performance/performance_clause_inventory.md` with valid frontmatter. One row per normative clause (a requirement, threshold, sample size, percentile, hardware class, outcome rule, or claim) found in:
  - `docs/engine/performance_contract.md`
  - `docs/engine/contracts/certification_contract.md` (§3 and any performance clause elsewhere)
  - `docs/performance/perf_baseline_policy.md`
  - `docs/performance/optimization_architecture.md` and `docs/performance/optimization_invariants.md` (C-15: classify each statement as verified current behavior, target architecture, or obsolete)
  - `docs/engine/runtime_profiles.md` and `docs/engine/contracts/resource_governor_contract.md`, only for clauses that set a performance budget or threshold
- Columns per clause: source document and line; clause text (short quote); clause kind; the code that enforces it, if any (file and line: `src/perf/regression_gate.py`, `tests/perf/test_perf_regression_baseline.py`, `assert_perf_threshold` call sites, `tools/perf/check_perf_regression.py`, `tools/perf/perf_ci.py`, and others found); the tests that exercise it; the CI job and selector that run those tests (`.github/workflows/test.yml`, including `perf-cert-arena` and the changed-files gate, plus pytest markers); whether the check is hard or soft (`hard=True` or warn-only); and a status: `enforced as written`, `enforced differently` (say how), `not enforced`, `contradicted by another clause` (name it)
- A reverse table: every live performance check in tests and CI that enforces no documented clause, with file and line
- A PERF-D4 mapping section: for each clause, its destination under PERF-D4 (stays in the contract; moves from the baseline policy into the contract as a capacity-run target; deleted as describing a mechanism that does not run; replaced by the certification-contract hardware classes; becomes a tripwire clause; becomes a capacity-run clause). Flag every clause that the PERF-D4 shape cannot express, which is PERF-D4's revisit condition
- An `assert_perf_threshold` table: every call site, its threshold, and `hard` value, so the planner's "12 of 53 pass `hard=True`" figure is reproducible. A small read-only `ast` helper is allowed for this table if it is simpler than hand counting; if added, it goes in `tools/perf/` with a test in `tests/tools/` and a test-scope map line, same conventions as the sibling inventories
- Record each disagreement between the documents with lines on both sides. Do not edit any of the documents

## Out of Scope
- Editing any document listed above, or any authority-P1 document (`PERF-M0-T09` applies the edits)
- Any change to gate behavior, thresholds, CI jobs, baselines, or `hard` flags
- Any edit under `src/`
- Running benchmarks or measuring anything
- Designing the benchmark identity schema (`PERF-M2-T02`) or the projections (`T03`, `T04`)
- Setting Gate A materiality thresholds

## Acceptance Criteria
- [x] Every normative clause in the five named documents (and the two partial ones) has a row with source line, kind, enforcing code, tests, CI selector, hard/soft, and status; the test plan records how completeness was checked (for example, every number with a unit and every "must"/"shall"/"required" in each document is either a row or listed as non-normative with a reason)
- [x] The reverse table lists every live performance check with no documented clause
- [x] Every clause has a PERF-D4 destination, and any clause the PERF-D4 shape cannot express is flagged in its own section
- [x] The `assert_perf_threshold` table matches the current tree; if a helper script was added, two runs are byte-identical and its tests pass
- [x] No document listed in Scope is edited; `git diff` touches only `docs/performance/performance_clause_inventory.md`, `docs/REGISTRY.yaml`, `agent-working/tickets/`, `agent-working/stored_artifacts/`, `agent-working/agent-monitoring/`, and (only if the helper is added) `tools/perf/`, `tests/tools/`, `tools/gate_checks/test_scope_coverage_static.py`

## Related Tickets
- TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC (parent program)
- TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT (open; reference only, do not close or re-scope)
- TCK-20260518-PERF-REGRESSION-GATE, TCK-20260624-PERF-GUARD-INFRA (origin of the gate and guard)
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (parked; reference only)
- TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT (consumes this inventory)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D4, PERF-D2, C-13, C-15)
- `docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md` (PERF-M2-T01, required contract dimensions, regression-signal policy)
- `docs/plans/design_enhancement/performance_optimization/performance_stack_survey.md` (section A)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260913-PERF-M0-SOURCE-AUDIT/source_inventory.md`

## Related Code Areas
- `src/perf/regression_gate.py`, `tests/perf/`, `tests/unit/perf/`, `tools/perf/check_perf_regression.py`, `tools/perf/perf_ci.py`, `.github/workflows/test.yml` (all read only)

## Assumptions / Open Questions
- Released by PERF-D4 itself ("releases `PERF-M2-T01` now"); evidence only, so the RPG-core entry gate does not block it
- `PERF-M2-T01` keeps its program ID in the title; the ticket ID follows the repository's ticket naming rule
- Where a clause is ambiguous between two kinds, pick one, say why in the row, and move on; the planner settles ambiguities when drafting T09
- perf-planner reviews the inventory before this ticket closes

## Implementation Notes
- Inventory: `docs/performance/performance_clause_inventory.md` (76 clause rows, reverse table, 15 disagreements, PERF-D4 mapping with codes STAY/CERT/CAP/CAPRUN/TRIP/HW/DEL/N/A/FLAG, call-site table).
- Helper `tools/perf/perf_threshold_inventory.py` (stdlib `ast`, deterministic) with a test and a test-scope map line.
- Headline findings: 0 of 55 call sites pass literal `hard=True`; `PerfRegressionGate` has no production caller; 12 of 15 baselines are 20-tick samples; calibration steps cite a missing module and directory; one cited test is missing.
- perf-planner review: approved with three fixes (CERT code and single-count totals, phase counts by unit from `phase_inventory.md`, neutral wording for the "12 of 53" figure); all applied.

## Test Summary
- `tests/tools/test_perf_threshold_inventory.py`: 8 passed. `tests/tools/test_test_scope_coverage_static.py` and `tests/tools/test_hash_callsite_inventory.py`: 48 passed. Two helper runs byte-identical. `validate_frontmatter.py` OK on the document, ticket and artifacts.

## Files Changed
- docs/performance/performance_clause_inventory.md (new)
- tools/perf/perf_threshold_inventory.py (new)
- tests/tools/test_perf_threshold_inventory.py (new)
- tools/gate_checks/test_scope_coverage_static.py (one map line)

## Completion Summary
Clause inventory delivered; no listed document, threshold, `hard` flag, baseline, CI job or `src/` file was edited and nothing was measured. T09 consumes sections 3, 4 and 6. Sections 6.2 items 4 and 5 are left for T09 to decide.
