---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-WORK-DEBT-RETIRE-STEP1-DOCS
phase: done
date: 2026-10-04
tags: [performance, engine]
---

# TCK-20261004-WORK-DEBT-RETIRE-STEP1-DOCS

## Title
Work-debt retirement step 1: correct the P1 contracts that say work debt counts postponed items

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION` confirmed that nothing ever produces
`state.work_debt`. Its test `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`
guards this. In 363 commits, only the drain half of the Milestone 4 design was built. The owner chose
**retire, in two steps** on 2026-10-04. This is step 1: docs only, ungated. Step 2, removing the code,
is `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE` and waits for the gate.

The P1 docs still describe a producer that does not exist:
- `docs/engine/contracts/resource_governor_contract.md:31`: "`work_debt`: Total count of postponed
  authoritative items."
- `docs/engine/matrices/scheduler_work_model_matrix.md`: the `DEFERRED` / "Work debt" row and its
  section say the debt accumulates when work overflows.

## Scope
- Correct both P1 docs to state current behaviour. `work_debt` is never increased in production:
  only `DRAIN_DEBT` consumes it, and `PressureInjector.inject_work_debt` has no caller. Every reader
  therefore sees 0. The field is scheduled for retirement (owner decision 2026-10-04; step 2 ticket).
  Cite the guard test
- PERF-D3 in `docs/architecture/performance_optimization_decisions.md`: add a dated note. The
  aggregate counter it ratified has no producer, and the owner chose retirement
- `docs/guidelines/intentional_divergences.md`: not needed, because no behaviour changes in this step
- Parity ledger: if an entry claims debt accumulation (search `work_debt` in
  `docs/parity_ledger/*.yaml`), set it to the true status with the guard test as evidence
- `make knowledge-index-update`; regenerate the registry

## Out of Scope
- Any `src/` edit (step 2, gated)
- The archived matrix under `docs/archive/` (historical)

## Acceptance Criteria
1. No active P1 doc says that work debt counts postponed or overflowed work
2. Each corrected statement cites the guard test and the step 2 ticket
3. The parity ledger is consistent (schema check: 0 rose)

## Related Tickets
- `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION` (evidence)
- `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`

## Related Docs
- `docs/engine/contracts/resource_governor_contract.md`, `docs/engine/matrices/scheduler_work_model_matrix.md`
- `docs/architecture/performance_optimization_decisions.md` (PERF-D3, PERF-D1 A1)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION/`

## Related Code Areas
- none edited

## Assumptions / Open Questions
- The owner approved the retirement on 2026-10-04, and these P1 edits only make the docs state
  current behaviour

## Implementation Notes
Docs only; no `src/` file. Every correction uses one standard statement: as of 2026-10-04 `work_debt` is never increased in production (nothing turns overflowed or dropped work into debt, `DRAIN_DEBT` only consumes existing debt, `PressureInjector.inject_work_debt` has no caller), so every reader sees 0; guard `tests/integration/kernel/test_work_debt_stays_empty_in_production.py`; retirement is `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE` (waits for the gate).

Corrected (all P1, found with `search_docs` then a `git grep` of `docs/` minus `docs/archive/`):
- `docs/engine/contracts/resource_governor_contract.md` (named in the ticket): the `work_debt` signal definition.
- `docs/engine/matrices/scheduler_work_model_matrix.md` (named): the `DEFERRED` row and section now say only the drain half exists; the REJECT overflow policy is marked "design, not implemented".
- Found beyond the two named, because AC1 covers every active P1 doc:
  - `docs/architecture/kernel_concurrency_design_philosophy.md`: said "Dropped work becomes an entry in `state.work_debt[subsystem_id]`", which is false. Rewritten, plus a one-line note under the mode-transition diagram that its two `work_debt` thresholds never fire.
  - `docs/engine/matrices/scheduler_test_matrix.md` section 3: named overflow tests that were never written (`test_debt_overflow_reject` is not in `tests/`); status note added and the "Hidden Backlogs" line qualified.
  - `docs/engine/architecture.md`: the SCHEDULING row said work is selected "based on the Work Debt budget"; now says readiness, cadence and governor policy.
- `docs/architecture/performance_optimization_decisions.md` PERF-D3: dated 2026-10-04 note (the aggregate counter it ratified has no producer; producer rejected under PERF-D1 A1; owner chose retirement in two steps).
- Parity ledger: no entry claims debt accumulation (searched `work_debt`, `postponed`, `deferred`, `DEFERRED`, `drain`, `overflow`; the hits are stamina and hazard "drain"); `INFRA-420` already states debt is seeded in tests. No ledger edit; `make parity-ledger-schema-check`: 0 rose, 0 new.
- `docs/guidelines/intentional_divergences.md`: not touched (no behaviour change).

Left alone (planner decisions: (a) perf-planner adds a dated note to the PERF-D1 A1 decision record itself; (b) the P2 proposal stays as a historical proposal):
- `docs/architecture/performance_optimization_decisions.md` PERF-D1 amendment A1 (an owner-approved decision text) still says "salience keeps the work-debt term"; that term is constant 0. The retirement decision supersedes it, but it is decision text, so I did not edit it.
- `docs/plans/kernel_concurrency_design_review_proposal.md:351` (P2 plan proposal, outside the P1 scope) still says "Dropped work becomes an entry in `state.work_debt`".
- `substrate_baseline_contract.md` ("DEFERRED (Debt Draining) third") and `signal_truth_contract.md` (`work_debt_total` source) describe ordering and a signal source, not accumulation, so they are accurate as written.

## Test Summary
- `tests/docs`: 69 passed, 2 skipped, 1 xfailed.
- `validate_frontmatter.py` on each of the six edited docs: no violations.
- `make parity-ledger-schema-check`: OK, 0 rose, 0 new.
- Re-scan of `docs/` (minus archive) for the old claims: only the P2 proposal above remains, plus the contract's own sentence that names the old design.

## Files Changed
- `docs/engine/contracts/resource_governor_contract.md`, `docs/engine/matrices/scheduler_work_model_matrix.md`, `docs/engine/matrices/scheduler_test_matrix.md`, `docs/architecture/kernel_concurrency_design_philosophy.md`, `docs/engine/architecture.md`, `docs/architecture/performance_optimization_decisions.md`
- `docs/REGISTRY.yaml` (regenerated at close)

## Completion Summary
Six active P1 docs now state that `work_debt` is never produced in production, with the guard test and the step-2 ticket cited, and PERF-D3 carries the dated owner-decision note. No ledger entry needed a change. Step 2 (code retirement) waits for the RPG-core entry gate.
