# TCK-20260618-AUDIT-EPIC — Audit Plan

## Sequencing Rationale

Dimensions are audited in priority order (Impact + Interest), with two ordering
constraints:

1. **D09 before D03/D05/D06** — System Wiring must confirm that `[E]` features are live
   before run-sim dimensions interpret what the simulation does.
2. **D03 before D04/D05/D08** — Behavioral Emergence Quality establishes baseline of
   what "good output" looks like; the other run-sim dimensions calibrate against it.

## Recommended Order

| Order | ID | Dimension | Method | Prerequisite |
|---|---|---|---|---|
| 1 | D01 | RPG Feature Impact | code-read | done ✓ |
| 2 | D02 | Foundation Feature Inventory | code-read | done ✓ |
| 3 | D09 | System Wiring & Integration | code-read | D02 done |
| 4 | D17 | Documentation Currency | review | none |
| 5 | D03 | Behavioral Emergence Quality | run-sim | D09 done |
| 6 | D15 | Entity Decision Inspection Tooling | review | D03 done |
| 7 | D06 | Long-Run Simulation Health | run-sim | D03 done |
| 8 | D10 | Test Coverage & Regression Risk | measure | D09 done |
| 9 | D05 | Entity Differentiation | run-sim | D03 done |
| 10 | D14 | Coupling Depth | code-read | D09 done |
| 11 | D07 | Content Depth & Variety | count | none |
| 12 | D04 | Balance & Tuning | run-sim | D03 done |
| 13 | D16 | Scenario & Content Authoring DX | review | none |
| 14 | D12 | Pattern Consistency | code-read | D09 done |
| 15 | D08 | Multi-Scenario Consistency | run-sim | D03 done |
| 16 | D13 | Type Safety & Validation Boundary | measure | none |
| 17 | D18 | CI / Release Pipeline Completeness | review | none |
| 18 | D11 | Dead Code & Orphaned Modules | measure | D09 done |

## Per-Method Approach

### code-read
Use mandatory context scan: `search_docs` → `graphify query` → targeted file reads.
Output: feature table with status (`none/partial/exists/verified`) and notes.
No grep-first investigation.

### run-sim
Run a standard 500-tick world using the procedural generator with seed=42.
Observe entity behavior directly via event log and metrics service output.
For D06 (long-run), extend to 2000+ ticks.

### measure
Use `pytest --co` for test inventory, `coverage.py` for coverage, `grep` for dead
symbol detection (after semantic tools return). Produce count-based tables.

### count
Enumerate content catalog entries by type. Count world modules, item types, recipe
chains, entity classes, quest kinds. Compare against "minimum interesting variety"
thresholds defined in D07 detail file.

### review
Apply a documented checklist specific to the dimension. Record pass/fail per item
and note evidence. Reviewer is the investigating agent for the relevant child ticket.

## Artifacts per Dimension

Each dimension child ticket produces:
- Detail file: `docs/audits/D{NN}_{slug}.md`
- Update to `docs/audits/audit_dimensions.md`: state → `done`
- Update to child ticket: moved to `tickets/done/`
- Working log entry

## Completion Criteria

All 18 dimensions in state `done` and `audit_dimensions.md` Key Insights section
updated with material findings from each group.
