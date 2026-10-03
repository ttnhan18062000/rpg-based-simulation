---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TEST-SCOPER-TOOLS-PERF-MAPPING
phase: done
date: 2026-10-03
tags: [testing, performance]
---

# TCK-20261003-TEST-SCOPER-TOOLS-PERF-MAPPING

## Title
test-scoper: route the new `tools/perf/` modules to `tests/tools/`, and stop citing the retired baseline-policy §3 regression gate

## Status
DONE

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
- [x] Every `tools/perf/*.py` module resolves, through the new table, to a directory that actually contains a test importing or invoking it, or is listed as having no test (with the module name)
- [x] `test-scoper.md` no longer cites `PerfRegressionGate` or `perf_baseline_policy.md` §3 as the live regression check
- [x] `pytest tests/tools/test_perf_tag_test_scoper_wiring.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_tools_orphan_check.py -q` passes, plus any other test found in Scope item 4
- [x] `git diff` touches only `.claude/agents/test-scoper.md` (or its generator source and output), tests found in Scope item 4, `agent-working/`, and `docs/REGISTRY.yaml`

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
Owner of each `tools/perf/*.py` module, from `grep -rlw` over `tests/` (importers, plus path invocations):

| Module | Owning test |
|---|---|
| phase_inventory, hash_callsite_inventory, perf_threshold_inventory, wall_clock_inventory | `tests/tools/` (one `test_<name>.py` each) |
| profile_tick, profile_diff, flag_attribution, _profiling_common | `tests/tools/test_profiling_toolkit.py` |
| profile_engine | `tests/unit/perf/test_profiling_harness_modes.py` |
| profile_sweep | `tests/perf/test_profile_sweep.py` |
| profile_memory | `tests/unit/cli/test_profile_memory_script.py` |
| live_map_ws_payload_measure, turbo_run, check_perf_regression, perf_baseline, perf_ci, perf_report, profile_api_payload, run_benchmarks, run_perf_baseline, memory_probe | no dedicated test (only scanning tests mention the first two; `tests/unit/test_memory_probe.py` tests `tests/tools/memory_probe.py`, not this module) |

Default kept as `tests/static/`, not `tests/tools/` as Scope item 2 suggested: `tools/gate_checks/test_scope_coverage_static.py` (`_TOOLS_SUBDIR_EXPLICIT_MAP`, plus an existing `_TOOLS_PERF_BASENAME_MAP` that already has all eight `tests/tools/` overrides) and `tests/tools/test_test_scope_coverage_static.py` pin `tests/static/` for `live_map_ws_payload_measure.py` and `turbo_run.py`. Switching the doc alone would split it from the gate; switching both is a `tools/` edit this ticket excludes. The md now matches the gate and lists every override. No generator source exists for `test-scoper.md` (the role yaml is a five-line stub), so it was edited directly.

Reported, not fixed: `.claude/workflows/implement-ticket.js:1369` and its pin `tests/tools/test_perf_tag_test_scoper_wiring.py:63` still cite `PerfRegressionGate` / `perf_baseline_policy.md` §3.

## Test Summary
`pytest tests/tools/test_perf_tag_test_scoper_wiring.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_tools_orphan_check.py -q`: 50 passed. One test (`test_test_scoper_md_documents_the_same_rule`) pinned the old policy citation in `test-scoper.md`; updated to the tripwire test path, `performance_contract.md`, and absence of `PerfRegressionGate`.

## Files Changed
- .claude/agents/test-scoper.md
- tests/tools/test_perf_tag_test_scoper_wiring.py (one assertion)
- this ticket, docs/REGISTRY.yaml, monitoring shards

## Completion Summary
test-scoper.md now routes each tools/perf module to its real test owner and cites the tripwire and the performance contract instead of the retired gate.
