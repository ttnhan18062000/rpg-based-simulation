---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS
phase: open
date: 2026-10-02
tags: [schema]
---

# TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS

## Title
M3c: Add craft metrics to the codebase health snapshot and take the first snapshot

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Last part of measuring and baselining code health: the author wants craft metrics added to the existing tools/codebase_health_snapshot.py and the first snapshot taken, rather than a second metrics tool being built (roadmap Section 4 reuse rule). No codebase health snapshot has ever been taken, so this also produces the first trend record. The shared constraints apply: no src/ edits, no simulation behaviour change, tests/ changes limited to tests for the new tooling, no edits to governing files or the agent-working domain.

## Scope
- Decide and record where craft metrics are computed: added to tools/codebase_health_baseline.py::build_report(), or supplied to the snapshot as a second metric source with its documented contract updated
- Add per-dimension craft metric keys (from the tools/code_health/ outputs) to the snapshot record, with no aggregate or combined score
- Update EXPECTED_SNAPSHOT_KEYS, bump SNAPSHOT_SCHEMA_VERSION from 1, and update docs/agent-monitoring/codebase_health_history_schema.md in the same commit
- Add tests for the new metric keys, never targeting the real agent-monitoring/codebase_health_history.jsonl
- Take the first snapshot after the schema bump has landed, producing the history file with one record

## Out of Scope
- A second metrics tool or a combined health score (D24 sections J/M)
- Tool configuration, adapters, ratchet and exceptions registry (the other two M3 tickets)
- Moving the flat tools/codebase_health_*.py scripts into a package
- Backward-compatibility handling for schema v1 history rows (none exist; the history file does not exist yet)
- Changing tools/code_health_impact.py or tools/pr_impact_report.py behaviour
- CI gating of snapshot values (M4)
- Any file under src/, CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/, .claude/skills/

## Acceptance Criteria
- [ ] Craft metrics appear in the snapshot record, and EXPECTED_SNAPSHOT_KEYS, SNAPSHOT_SCHEMA_VERSION (bumped from 1) and docs/agent-monitoring/codebase_health_history_schema.md are updated together in one commit
- [ ] set(build_report().keys()) == EXPECTED_SNAPSHOT_KEYS still holds, or the snapshot's documented contract and module docstring are updated to describe the second metric source; the choice is recorded in the ticket
- [ ] No aggregate or combined score key is added: tests/tools/test_codebase_health_snapshot.py::test_scorecard_output_has_no_aggregate_or_combined_score_field passes
- [ ] pytest tests/tools/test_codebase_health_snapshot.py tests/tools/test_codebase_health_baseline.py passes, and any edit to an existing test in those files is limited to what the schema bump itself requires and is listed in the ticket
- [ ] New tests assert each craft metric key is present with a numeric value on a fixture, and none writes under the real agent-monitoring/ directory (test_no_test_target_path_resolves_under_real_agent_monitoring_dir passes)
- [ ] agent-monitoring/codebase_health_history.jsonl exists with exactly one record (the first snapshot ever taken) containing the new craft metric keys and the bumped schema version
- [ ] The existing snapshot and baseline make targets still exit 0 end to end (test_make_target_runs_successfully_end_to_end and test_make_target_runs_successfully_with_plausible_values pass)
- [ ] 'git diff --stat <base>...HEAD' lists no path under src/, no path under .claude/ and not CLAUDE.md

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- TCK-20261002-CODE-HEALTH-TOOL-CONFIG
- TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
- TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/agent-monitoring/codebase_health_history_schema.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/codebase_health_snapshot.py
- tools/codebase_health_baseline.py
- tools/code_health_impact.py
- tools/pr_impact_report.py
- docs/agent-monitoring/codebase_health_history_schema.md
- Makefile
- docs/plans/codebase_health/python_code_craft_roadmap.md

## Assumptions / Open Questions
- Design conflict to resolve in the plan: tools/codebase_health_snapshot.py states it never computes metrics itself and enforces key equality with build_report(). Adding craft metrics to build_report() makes 'make codebase-health-baseline' depend on external tools; a second metric source changes the documented contract and test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented
- That existing test may need an edit under the second-source option; the shared constraint limits tests/ changes to tests for new tooling, so this needs an owner decision before choosing that option
- Ordering: build_scorecard indexes latest[key] and previous[key] directly, so a v2 record after a v1 record would raise KeyError. The history file does not exist today, so the schema bump must land before the first snapshot is taken
- The snapshot tooling uses sys.path.insert and flat modules while tools/code_health/ uses package imports; importing across the two needs care, and the flat files are not moved
- Runs last in M3: depends on the adopted tool list and outputs from the other two M3 tickets
- The first snapshot record is committed data under agent-monitoring/ and is staged with the ticket's commit
- Layer `observability` was inferred: the snapshot history and its schema doc live under agent-monitoring/ (docs/agent-monitoring/, agent-monitoring/codebase_health_history.jsonl)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
