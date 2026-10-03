---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TEST-SCOPER-TOOLS-PERF-MAPPING
phase: open
date: 2026-10-03
tags: [testing, performance]
---

# TCK-20261003-TEST-SCOPER-TOOLS-PERF-MAPPING

## Title
test-scoper: route the new `tools/perf/` modules to `tests/tools/`, and stop citing the retired baseline-policy §3 regression gate

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
`.claude/agents/test-scoper.md` maps `tools/perf/*.py` to `tests/static/` by default, with three named exceptions. The perf batches of 2026-10-03 added modules whose tests live in `tests/tools/`: `phase_inventory.py` (`tests/tools/test_phase_inventory.py`), `hash_callsite_inventory.py` (`tests/tools/test_hash_callsite_inventory.py`), and the profiling toolkit (`profile_diff.py`, `flag_attribution.py`, `_profiling_common.py`, and others, `tests/tools/test_profiling_toolkit.py`). A change to any of them is scoped to `tests/static/`, which does not test them.

Separately, the `performance` tag rule (line ~136) justifies itself by "the real regression-gate check (`PerfRegressionGate`, `docs/performance/perf_baseline_policy.md` §3)". That section has said since 2026-08-08 that `PerfRegressionGate` has no consumer. After PERF-D4 (applied by `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT`), `docs/engine/performance_contract.md` is the clause authority, and the running check is the tripwire in `tests/perf/test_perf_regression_baseline.py`.

## Scope
1. Derive the real owner of each `tools/perf/*.py` module from its importers. Run `grep -rlE "tools[./]perf[./]<module>" tests/` per module; also follow `importlib`/subprocess invocations by path. Record the full module → test-directory table in Implementation Notes
2. Rewrite the `tools/perf/*.py` entry in the `tools/` Test Directory table to match. Choose the default from the table (the directory that owns most modules), and list every module whose owner differs. Keep the existing warning that `tests/unit/perf/` tests `src/perf/`, not `tools/perf/`
3. In the `performance` tag rule, replace the `PerfRegressionGate` / `perf_baseline_policy.md` §3 citation with the tripwire (`tests/perf/test_perf_regression_baseline.py`) and `docs/engine/performance_contract.md` §5. Keep the rule's behavior (always include `tests/unit/perf/` and `tests/perf/` with `-m "not slow"`)
4. Check whether a test pins the mapping text: `tests/tools/test_perf_tag_test_scoper_wiring.py`, `tests/tools/test_test_scope_coverage_static.py`, and any test that reads `.claude/agents/test-scoper.md`. If one pins the old text or the old default, update it to the new mapping in the same commit and say so in Test Summary. If a test enforces a property the new mapping breaks, stop and report it
5. If `agent-working/agent-orchestration/` holds a source copy of this agent definition that a generator renders, edit the source and regenerate, never the generated file

## Out of Scope
- Any other row of the `tools/` table, or any other part of `test-scoper.md`
- Editing `docs/performance/perf_baseline_policy.md` or any test under `tests/perf/`
- Any edit under `src/`

## Acceptance Criteria
- [ ] Every `tools/perf/*.py` module resolves, through the new table, to a directory that actually contains a test importing or invoking it, or is listed as having no test (with the module name)
- [ ] `test-scoper.md` no longer cites `PerfRegressionGate` or `perf_baseline_policy.md` §3 as the live regression check
- [ ] `pytest tests/tools/test_perf_tag_test_scoper_wiring.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_tools_orphan_check.py -q` passes, plus any other test found in Scope item 4
- [ ] `git diff` touches only `.claude/agents/test-scoper.md` (or its generator source and output), tests found in Scope item 4, `agent-working/`, and `docs/REGISTRY.yaml`

## Related Tickets
- TCK-20261003-PERF-PROFILING-TOOLKIT, TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT, TCK-20261003-PERF-HASH-CALLSITE-INVENTORY (added the modules)
- TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT (moved clause authority to the performance contract)
- TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION (the 2026-08-08 correction)

## Related Docs
- `docs/engine/performance_contract.md` §5
- `docs/performance/perf_baseline_policy.md` §3

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/agents/test-scoper.md`
- `tools/perf/`, `tests/tools/`, `tests/static/`, `tests/unit/perf/`, `tests/perf/`

## Assumptions / Open Questions
- `.claude/agents/` belongs to the agent-working domain. The owner approved this batch on 2026-10-03, which covers this edit; the codebase-planner is told when the PR opens.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

