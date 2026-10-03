---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2
phase: done
date: 2026-10-01
tags: [testing]
---

# TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2

## Title
Harden scenario-lane routing, add a report-only JUnit cost view, record mutation baseline v2, and write down the post-pilot decisions

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Owner post-pilot decisions (roadmap §6) leave four items for this batch. B4: the scenario-lane irrelevant list assumes `tools/` and similar prefixes are never read by scenario tests, and the summary reports a routing statement as if it were execution. B3: no per-directory cost view exists. B2: the mutation baseline (60/177 killed, 2026-09-29) is stale after 2026-10-30 and its selection no longer matches the tests that exist. B1: record decisions, triggers fired, and the bounded closure of Epic D.

## Scope
- B4: static test enforcing the irrelevant-prefix exclusions (AST scan of src/, tests/mechanic_scenarios/, tests/helpers/, tests/conftest.py); docstring and taxonomy-doc limits; summary reworded to routing-not-execution; five routing fixtures.
- B3: `tools/test_architecture/junit_cost_report.py`, report-only, plus tests and a doc note; roadmap §9 amended to name it.
- B2: mutation baseline v2 as a new record beside v1 with a declared supersedes/current field; report reads that field; `selection-changed` flag.
- B1: text only (roadmap §6/§11, Epic D bounded closure, pilot report dated addendum, `month_basis` wording). Disposition table for external findings in investigation.md.

## Out of Scope
- Any src/ change; calling a mutation survivor a defect; survivor-count thresholds.
- Promotion of the scenario lane to required; domain roll-out; §9 cleanup targets.
- Progression pilot P (separate, needs the user's go-ahead).
- Moving any epic out of tickets/todos/test-architecture/.

## Acceptance Criteria
1. A test fails if scenario-reachable code imports top-level `tools` or names a path under an irrelevant prefix, with a short per-entry allowlist; the chosen option is stated.
2. Summary says "routed to perf-cert-arena; scenario execution is that job's result"; fixtures cover src/progression only, src/domains/progression only, mixed, docs only, unknown.
3. Cost view covers all supplied JUnit directories, labels durations "observed test duration", keeps runs separate, reports absent directories as not-in-supplied-runs, and detects duplicate artifacts and overlapping nodes.
4. Baseline v2 is a real mutmut run on the new selection with full metadata; the report shows v2 current and v1 superseded; no threshold.
5. Roadmap, Epic D and pilot report text carry the limits listed in the investigation; no epic file has `phase: done`.
6. Disposition table recorded; tests pass; graphify updated.

## Related Tickets
TCK-20260930-TEST-DECISIONS-RECORD-AND-SCENARIO-LANE, TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY, TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION, TCK-20260929-EPIC-CORE-RPG-TEST-PILOT

## Related Docs
docs/plans/test_architecture/roadmap.md, docs/testing/test_taxonomy.md, docs/testing/core_rpg_test_pilot_2026-09-30.md, docs/testing/regression_policy.md

## Related Stored Artifacts
stored_artifacts/TCK-20260930-TEST-DECISIONS-RECORD-AND-SCENARIO-LANE/

## Related Code Areas
tools/test_architecture/, tests/unit/tools/, tests/mutation/, .github/workflows/test.yml

## Assumptions / Open Questions
- Route: hand-orchestrated (user choice 2026-10-01); recorded with record_hand_orchestrated_closure.py.
- Reviewer (test-architecture-reviewer) approved the plan 2026-10-01 with five notes (AST scan excluding docstrings; allowlist, switch to narrowing tools/ if it grows past a handful; §9 must name the cost view; real mutmut run; epic files stay phase-open).

## Implementation Notes
- B4: AST scan over the static import closure from scenario code (454 files, zero hits, empty allowlist) instead of all of src/ (9 hits in 6 unreached files); docstrings excluded; limits documented in the module docstring and test_taxonomy.md. Summary now says "routed to ...; scenario execution is that job's result". Fixtures read PERF_RE from the workflow.
- B3: new report-only `junit_cost_report.py`; roadmap §9 names it.
- B2: new `mutation_selection.py` (import-based-one-hop rule); `core_rpg_report` reads a declared `supersedes` link and flags `selection-changed`; v2 record from a real mutmut 2.5.1 run (177 mutants, 152 killed, 25 survived, 460 s) with the positive control reused after three equality checks.
- B1: roadmap §6/§9/§11, Epic D bounded closure (file stays phase: open in todos/), pilot report addendum and v2 update, `month_basis` reworded. Disposition table in investigation.md.
- Route: hand-orchestrated, recorded with record_hand_orchestrated_closure.py.

## Test Summary
`pytest tests/unit/tools tests/docs`: 563 passed, 1 skipped, 1 xfailed. New: test_scenario_lane_exclusions.py (6, incl. positive control), 6 routing fixtures in test_scenario_lane_paths.py, test_junit_cost_report.py (10), test_mutation_selection.py (3), 5 lifecycle tests in test_core_rpg_report.py. `graphify update .` run.

## Files Changed
tools/test_architecture/{scenario_lane_paths,core_rpg_report}.py (edited); tools/test_architecture/{junit_cost_report,mutation_selection}.py (new); tests/unit/tools/{test_scenario_lane_exclusions,test_junit_cost_report,test_mutation_selection}.py (new) and test_scenario_lane_paths.py, test_core_rpg_report.py (extended); tests/mutation/baselines/src_core_conservation_v2.json (new); docs/plans/test_architecture/roadmap.md, docs/testing/{test_taxonomy,core_rpg_test_pilot_2026-09-30}.md; tickets/todos/test-architecture/TCK-20260929-EPIC-CORE-RPG-TEST-PILOT.md; docs/REGISTRY.yaml.

## Completion Summary
B1 to B4 landed in one batch. Limits: v2's selection is a starting point, not proof; v1 and v2 counts are not comparable; the exclusion scan does not follow dynamic imports; the cost view has no failure history and CI uploads JUnit only from api-tools. Epics B, C and D files stay open in todos/.
