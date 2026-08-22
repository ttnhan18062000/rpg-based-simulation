---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR
phase: open
date: 2026-08-22
tags: []
---

# TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR

## Title
PR / AI change-impact report generator

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a report generator that produces PR- or AI-change-facing impact reports, built on top of the output shape of the already-delivered code-health impact command (tools/code_health_impact.py::build_impact_report()). This is explicitly the last item in the epic's sequence because it depends on everything built before it — the LoC/churn baseline and the impact command — and, per the epic's own documented dependency chain, on the historical snapshot mechanism as well.

## Scope
- New report-generator entrypoint that accepts one or more target paths, calls tools/code_health_impact.py::build_impact_report() per path, and produces a rendered Markdown or JSON artifact.
- Report content fully traceable to build_impact_report()'s existing fields only (subsystem, direct dependents, required tests, relevant invariants, architecture rules, criticality tier, degradation caveat) — no new impact-computation logic duplicated outside tools/code_health_impact.py.
- Preserve and surface degradation signals verbatim: dependents_degraded, dependents_degradation_reason, unresolved_symbols.
- Preserve the 'discovery/triage aid, not a certified coverage oracle' framing from code_health_impact.py's module docstring in the report's own output/framing.
- If design confirms a real dependency on C1's (TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD) snapshot history for trend context, integrate it with graceful, clearly-labeled degradation when no snapshot history exists yet for a path; if design does not require it, state explicitly that this iteration renders from build_impact_report() output alone.
- Multi-path batching support (e.g. for a PR diff spanning multiple files) where one degraded path does not silently fail the whole report.
- New tests under tests/tools/ for the report-generator layer (none exist yet).

## Out of Scope
- New CLI/git-diff-parsing logic to auto-enumerate changed paths from a PR diff — this ticket accepts explicit target paths as input; diff-parsing is separate, unscoped surface area.
- Any new impact-computation logic — this ticket only renders build_impact_report()'s existing output.
- A single aggregate/combined numeric health score in any form.
- Choosing the final scorecard dimension set — that decision belongs to TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD; this ticket only consumes that ticket's output shape once available.

## Acceptance Criteria
- [ ] The report-generator entrypoint accepts one or more target paths, calls build_impact_report() per path, and produces a rendered Markdown or JSON artifact whose content is fully traceable back to build_impact_report()'s existing fields, with no impact-computation logic duplicated outside tools/code_health_impact.py.
- [ ] Generated report output preserves and surfaces dependents_degraded, dependents_degradation_reason, and unresolved_symbols verbatim rather than silently dropping them.
- [ ] Generated report output never renders a single aggregate numeric 'health score' — only existing tiered/qualitative fields (criticality_tier, architecture_rules, required_tests) are surfaced.
- [ ] If (and only if) design confirms a real dependency on C1's historical-snapshot data, the report generator degrades gracefully (clearly-labeled absence, not a crash or fabricated trend) when no snapshot history exists yet for a given path.

## Related Tickets
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC
- TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD

## Related Docs
- docs/audits/D24_codebase_health_observatory.md
- docs/plans/codebase_health_observatory_tooling_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/code_health_impact.py
- tests/tools/test_code_health_impact.py
- tools/codebase_health_baseline.py
- Makefile
- docs/audits/D24_codebase_health_observatory.md
- expected: tools/pr_impact_report.py
- expected: tests/tools/test_pr_impact_report.py

## Assumptions / Open Questions
- Depends on C1's ticket (TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD, historical snapshot mechanism) landing first — this ticket's report generator consumes C1's snapshot data/output shape per the epic's own documented dependency chain ('impact command → historical snapshots → PR report generator', stored_artifacts/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND/investigation.md lines 14-15, 61-64).
- The scorecard dimension set (C1's output shape) is decided as part of C1's ticket; if C1 lands without a snapshot-integration need being confirmed, this ticket's AC4 (graceful degradation) may be satisfied trivially by having no snapshot dependency at all, rather than requiring rework.
- No CLI/git-diff-parsing precedent exists for enumerating changed paths from a PR diff; this ticket accepts explicit paths and treats diff-parsing as out of scope, to be scoped separately if needed.
- The report generator must not let one degraded path (graphify ambiguity/failure) silently fail an entire multi-path PR report.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
