---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC
phase: open
date: 2026-10-09
tags: [testing, regression, simulation-quality, planning]
---

# TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC

## Title
Testing-side infrastructure for the rpg regression gate report: harness, baselines, report states, ownership registry, scheduled workflow

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The owner asked for durable regression control on rpg behaviour (2026-10-09). rpg-planner and rpg-designer defined the metric set v1 (`.claude/handover/drafts/rpg-regression-metric-set-v1.md` (rpg-planner + rpg-designer, 2026-10-09)): VALIDITY metrics V1-V7 (exact, can FAIL) and OUTCOME metrics O1-O7 (paired against a baseline over 5 seeds with k*SE plus a floor; a crossing is DRIFT, "trace the cause", never FAIL on its own). The agreed split (rpg-planner and testing-planner, 2026-10-09):
- **rpg**: metric definitions, oracles and Bible citations, k and floors, baseline content, the metric computation from typed records, the SimQ needs/livelihood validity pillar.
- **testing (this epic)**: the harness (a fresh process per world/seed, everything pinned), the baseline file format and staleness, the report states (pass / fail / drift / unstable / stale / no-data), the rerun-same-SHA step, the ownership registry (generalised from the slow-regression known reds) and the rolling issue, and the scheduled plus on-demand workflow (the #464 gate pattern; advisory first).

**Metric contract (shared by every child; rpg implements the computation, testing everything around it).** For each (world, seed) run, the rpg metric module turns that run's typed records into one JSON document:
```
{"schema": "rpg-gate-metrics/v1", "world": "...", "seed": 42, "ticks": 5000, "sha": "<commit>", "harness_hash": "<hash>",
 "metrics": [
   {"id": "V1", "class": "validity", "group": "*", "violations": 0, "examples": [ ... up to 5 ... ]},
   {"id": "O1", "class": "outcome",  "group": "people", "value": 0.12}
 ]}
```
`class` is `validity` (exact or logical: `violations` is an integer, and any non-zero value is a FAIL) or `outcome` (`value` is a number; compared paired against the baseline; a crossing is DRIFT, never FAIL). `group` is a kind group or `*`. Metric ids, groups, oracles, k and the per-metric floors belong to rpg (the metric set v1: V1-V7, O1-O7). testing never hard-codes a metric id.

## Scope
Children, in order (see SEQUENCE.md):
1. TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE: the known-reds schema, matcher and lint move into a shared module; the slow report keeps identical behaviour; a second registry kind for metric ids.
2. TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS: the versioned, immutable baseline format, staleness, the dual reference (last plus milestone-first) and the re-baseline citation check.
3. TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS: the pinned, fresh-process harness that runs the matrix and collects metric JSON documents.
4. TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN: evaluation, report states, the same-SHA rerun that marks UNSTABLE, and JSON plus markdown output.
5. TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW: the scheduled daily job plus `workflow_dispatch` on a ref, the #464-style gate, the rolling issue, advisory only.

## Out of Scope
- Metric definitions, oracles, thresholds, baseline content, the metric computation module and the SimQ pillar scorer (rpg's tickets; rpg-planner cross-links them).
- Making the report a required check (principle 8: a recorded owner decision after the post-pilot review, based on the observed false-positive rate).
- Any authority role: the report cites the Bible and the parity ledger, and never becomes a proof-status record (roadmap principle 3).

## Acceptance Criteria
1. All five children closed.
2. One daily report on main, and one dispatched report on a branch, both produced end to end against a real baseline, with every state the run can reach visible in the summary (at least pass, plus one non-pass state from a seeded fixture in the tests).
3. A same-SHA rerun that disagrees produces UNSTABLE and routes to test infrastructure, not to the feature team.
4. Roadmap §4.1/§4.2 updated: a new broad-simulation evidence layer, "rpg gate report (system health; advisory)".

## Related Tickets
- rpg-side tickets (rpg-planner files them and cross-links): the metric computation module, the SimQ needs/livelihood validity pillar.
- TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN (#464 gate pattern reused)
- TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER (the pin the harness uses)
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (the flapping single-run anchors the pillar replaces)

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §3 (principles 1, 3, 4, 5, 8), §4.1, §4.2, §4.5
- `docs/brainstorm/simulation-rule-taxonomy-evaluation-direction.md` §5 (outcome neutrality)
- `docs/engine/deterministic_execution.md` (audit_mode and wall-clock inputs)
- the metric set v1 draft (see Request Summary)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/test_architecture/` (new modules)
- `tools/test_architecture/slow_known_reds.yaml`, `slow_regression_report.py` (generalised in child 1)
- `tests/helpers/kernel_pinning.py`
- `.github/workflows/` (a new workflow in child 5)

## Assumptions / Open Questions
- Cost: about 15-30 runs of 5000 ticks per report (rpg-planner's estimate). Child 3 measures it; child 5 sizes the CI matrix from that measurement.
- Process-global state leaks between tests in one process (the strict-xfail and CONFLICT-04 findings, 2026-10-09), so a fresh process per (world, seed) is required, not optional.
- Where the config and baselines live: proposed `tests/simulation_quality/rpg_gate/` (rpg-owned content, testing-owned schema). Child 2 confirms the path with rpg-planner.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
