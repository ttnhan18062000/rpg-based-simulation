---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-IMPLEMENT-TICKET-PERF-REMINDER-CITATION
phase: open
date: 2026-10-03
tags: [testing, performance]
---

# TCK-20261003-IMPLEMENT-TICKET-PERF-REMINDER-CITATION

## Title
implement-ticket.js: cite the tripwire and the performance contract in the `performance`-tag test-scoper reminder, not the retired PerfRegressionGate

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
`TCK-20261003-TEST-SCOPER-TOOLS-PERF-MAPPING` replaced the stale citation in `.claude/agents/test-scoper.md`. Its review found the same stale text in the prompt that `.claude/workflows/implement-ticket.js` (around line 1369) sends to test-scoper for `performance`-tagged tickets: "the real regression-gate check (PerfRegressionGate, docs/performance/perf_baseline_policy.md §3)". `PerfRegressionGate` has no consumer (`perf_baseline_policy.md` §3, 2026-08-08 correction). The live check is the tripwire in `tests/perf/test_perf_regression_baseline.py`, and clause authority is `docs/engine/performance_contract.md` §5 (PERF-D4). `tests/tools/test_perf_tag_test_scoper_wiring.py::test_performance_tag_reminder_cites_the_real_regression_gate_doc` (around line 63) pins the old path.

## Scope
1. In the `performance`-tag reminder in `implement-ticket.js`, replace the parenthetical with the same wording `test-scoper.md` now uses (the tripwire test path and `docs/engine/performance_contract.md` §5). Change nothing else in the template, including the conditional and the two test directories
2. Update that one test so it asserts both new references and that `PerfRegressionGate` is absent from the reminder window. Keep every other assertion in the file
3. Check that the other places that render or mirror this prompt don't also pin the old text: any copy under `agent-working/agent-orchestration/`, and the Codex adapter output if it renders this workflow. Update a copy only if it is generated from this source; report any hand-maintained copy

## Out of Scope
- Any other change to `implement-ticket.js` or other workflows
- `docs/performance/perf_baseline_policy.md`, `src/perf/regression_gate.py`

## Acceptance Criteria
- [ ] `grep -n "PerfRegressionGate" .claude/workflows/implement-ticket.js` returns nothing
- [ ] `pytest tests/tools/test_perf_tag_test_scoper_wiring.py -q` passes, plus any test that loads or snapshot-checks `implement-ticket.js` (find them with `grep -rl implement-ticket.js tests/`)
- [ ] `git diff` touches only `.claude/workflows/implement-ticket.js`, the test(s) above, any generated copy from Scope item 3, `agent-working/`, and `docs/REGISTRY.yaml`

## Related Tickets
- TCK-20261003-TEST-SCOPER-TOOLS-PERF-MAPPING (found this)
- TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT (PERF-D4 applied)

## Related Docs
- `docs/engine/performance_contract.md` §5, `docs/performance/perf_baseline_policy.md` §3

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/workflows/implement-ticket.js`, `tests/tools/test_perf_tag_test_scoper_wiring.py`

## Assumptions / Open Questions
- Added to the batch by perf-planner during review on 2026-10-03, as the same kind of edit as the test-scoper ticket that the owner approved.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

