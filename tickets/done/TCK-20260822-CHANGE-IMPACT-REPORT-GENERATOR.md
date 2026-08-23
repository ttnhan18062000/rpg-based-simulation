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
INPROGRESS

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
- [x] The report-generator entrypoint accepts one or more target paths, calls build_impact_report() per path, and produces a rendered Markdown or JSON artifact whose content is fully traceable back to build_impact_report()'s existing fields, with no impact-computation logic duplicated outside tools/code_health_impact.py.
- [x] Generated report output preserves and surfaces dependents_degraded, dependents_degradation_reason, and unresolved_symbols verbatim rather than silently dropping them.
- [x] Generated report output never renders a single aggregate numeric 'health score' — only existing tiered/qualitative fields (criticality_tier, architecture_rules, required_tests) are surfaced.
- [x] If (and only if) design confirms a real dependency on C1's historical-snapshot data, the report generator degrades gracefully (clearly-labeled absence, not a crash or fabricated trend) when no snapshot history exists yet for a given path. (Resolved as not applicable: investigation.md confirmed no real per-path dependency exists between this report generator and C1's repo-wide-aggregate snapshot mechanism — enforced by the standing architecture-guard test `test_report_generator_has_no_import_of_codebase_health_snapshot_module`.)

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

Implemented `staging_artifacts/TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR/plan.md` exactly, all
10 steps in order:

- **`tools/pr_impact_report.py`** (new): standard sibling skeleton (`_TOOLS_DIR`/`_REPO_ROOT`
  sys.path guard, `import code_health_impact as chi`), module docstring carrying the verbatim
  triage-aid framing quote plus an explicit no-snapshot-dependency design note, and the
  `FRAMING_NOTE` constant (byte-identical to `chi.format_impact_report()`'s own closing-note
  wording).
- `build_pr_impact_report(repo_root, target_paths, depth=..., graph=None, graph_path=...,
  registry_entries=None, affected_runner=...)`: loads `graph`/`registry_entries` once for the
  whole batch, calls `chi.build_impact_report()` once per target path inside a
  `try/except Exception`, isolates per-path failures into `{"target_path", "status", "report",
  "error"}` entries without aborting the loop, returns `{"target_paths", "entries",
  "framing_note"}`.
- `format_pr_impact_report(report, max_dependents_shown=40)`: Markdown renderer over all 13 real
  `build_impact_report()` fields per entry, in the same key order as the real return dict.
  Reproduces `format_impact_report()`'s exact degradation-vs-unresolved-symbols conditional for
  the "dependents" summary line, plus always-present, separately labeled raw field lines for
  `dependents_degraded`/`dependents_degradation_reason`/`unresolved_symbols` (with clean `(none)`
  placeholders instead of a literal `None`) so no field value is ever silently dropped from the
  output — see "Deviations" in `plan.md` for why this needed two rendering layers rather than one.
  Closing line carries `report["framing_note"]` verbatim.
- JSON mode: no new function — `build_pr_impact_report()`'s dict is directly
  `json.dumps`-serializable, wired into `main()`.
- `main(argv=None) -> int`: argparse with `target_paths` (`nargs="+"`), `--repo-root`, `--depth`,
  `--graph`, `--format {markdown,json}`.
- `tests/tools/test_pr_impact_report.py` (new): all 14 planned tests, mirroring
  `tests/tools/test_code_health_impact.py`'s fixture-graph/injected-`affected_runner`/
  `_requires_graphify` conventions.
- `Makefile`: new `codebase-health-pr-impact` target (on-demand only, `$(ARGS)` passthrough) added
  immediately after `codebase-health-scorecard`, and added to the `.PHONY:` line.
- `docs/plans/codebase_health_observatory_tooling_epic.md`: struck through the 4th Scope bullet
  and added a `**Resolved**` paragraph correcting the "built on top of" phrasing to name the
  Phase 3 impact command specifically and stating explicitly that no snapshot-history dependency
  was needed.
- No parity ledger entry — confirmed correctly out of scope (no `src/` simulation path, Mechanics
  Bible chapter, or engine contract touched).

`tools/code_health_impact.py`, `tools/codebase_health_snapshot.py`, and
`chi.format_impact_report()` were not touched, per the plan's Scope Guards — directly enforced by
the new architecture-guard test `test_report_generator_has_no_import_of_codebase_health_snapshot_module`.

One deviation from the plan's literal Step 3 text was needed and is recorded in full in
`staging_artifacts/TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR/plan.md`'s new "Deviations
(recorded during Implement)" section: the plan's single degradation-conditional description
conflicts with AC #2's never-silently-drop requirement for the
`dependents_degraded=True` + non-empty `unresolved_symbols` case, resolved by rendering in two
layers (a faithful `format_impact_report()`-style summary line, plus always-present raw field
lines for full traceability).

## Test Summary

- `pytest tests/tools/test_pr_impact_report.py -v` — 13 passed, 1 skipped (the
  `@_requires_graphify`-marked Makefile end-to-end test; skips because `graphify-out/graph.json`
  is not built in this worktree — confirmed the identical, pre-existing skip behavior for
  `tests/tools/test_code_health_impact.py`'s own `@_requires_graphify` tests in this same
  environment, not a new gap).
- `pytest tests/tools/ -k "pr_impact_report or code_health_impact or codebase_health" -v` — this
  count is now stale relative to the current worktree state: it read 59 passed/5 skipped/0 failed
  at the moment it was first written, before `graphify-out/graph.json` existed in this worktree
  (so the `@_requires_graphify`-marked tests were skipped, not run). After `graphify update .`
  built a real graph later the same session, re-running this command gives **62 passed, 2 failed**.
  Both failures are in the untouched, forbidden-to-edit `tests/tools/test_code_health_impact.py`
  (`test_real_path_pipeline_includes_kernel_as_dependent`,
  `test_real_path_pipeline_kernel_visible_in_formatted_output_not_just_internal_data`) and were
  discovered during this ticket's own Test phase. Confirmed pre-existing and unrelated to this
  ticket's changes (no `src/` path touched by this ticket; independently verified via git history
  and direct import-graph inspection that `src/engine/apply.py` genuinely has no current import
  relationship to `src/engine/pipeline.py`, so the tests' `apply.py`-as-dependent assumption is
  stale, predating this session). Filed as
  `TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT` rather than editing the
  forbidden test file to route around the failure.
- `pytest tests/docs/test_doc_integrity.py -v` — 10 passed, 1 skipped (pre-existing unrelated
  skip: `test_scoped_reporting_compliance`), 0 failed.

## Files Changed

- `tools/pr_impact_report.py` (new)
- `tests/tools/test_pr_impact_report.py` (new)
- `Makefile` (new `codebase-health-pr-impact` target + `.PHONY` entry)
- `docs/plans/codebase_health_observatory_tooling_epic.md` (4th Scope bullet struck through and
  resolved)
- `staging_artifacts/TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR/plan.md` (Deviations section
  appended during this Implement run)
- `staging_artifacts/TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR/investigation.md` (new — the
  standard Investigate-phase artifact for this standard-tier ticket)
- `staging_artifacts/TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR/test_plan.md` (new — the
  standard Investigate-phase artifact for this standard-tier ticket)
- `docs/plans/architecture_resilience_remediation_roadmap.md` (Document-Update phase: Epic K's
  status-line cell updated from "3 of 4 items resolved/extracted" to "all 4 items
  resolved/extracted; awaits final child ticket ... reaching `tickets/done/`", and the matching
  "PR/AI change-impact report generator" bullet in its own detail section resolved.)
- `tickets/todos/codebase-health-resilience/TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC.md`
  (Document-Update phase: same Epic K status-line update one level up the epic-tracking chain,
  plus a dated narrative paragraph recording this ticket's resolution and this ticket added to
  Related Tickets.)
- `tickets/todos/codebase-health-observatory-tooling/TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC.md`
  (Document-Update phase: this epic ticket's own Scope/Acceptance-Criteria sections updated to
  reflect all 4 child items now having tickets, with item 4 correctly noted as still in
  `tickets/inprogress/` rather than falsely marked done.)
- `tickets/inprogress/TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR.md` (this file — Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary

Built `tools/pr_impact_report.py` — a batched Markdown/JSON PR/AI change-impact report generator
over one or more target paths, rendering all 13 real `chi.build_impact_report()` fields per path
with per-path failure isolation (one degraded or failing path never aborts the whole batch) and
verbatim preservation of the three degradation signals. Confirmed and enforced (via a dedicated
architecture-guard test) the investigation's resolved design decision that this module has no
dependency on `tools/codebase_health_snapshot.py`'s repo-wide snapshot mechanism — it is built
directly on top of the Phase 3 impact command only, matching the source audit's own literal
wording. New on-demand `make codebase-health-pr-impact` target added; no aggregate/combined score
field exists anywhere in either output mode, and no parity ledger entry was needed.

Document-Update found and resolved a real gap the Implement phase's own epic-doc edit didn't
reach: this ticket completes item 4 of 4 under Epic K, and two further upstream docs
(`docs/plans/architecture_resilience_remediation_roadmap.md` and the resilience epic's own
parent tracking ticket) mirror Epic K's status/item list independently of the epic doc — both
updated to reflect all 4 items now resolved, while correctly keeping the epic itself "open"
until this ticket actually reaches `tickets/done/`. Test phase also surfaced a real, pre-existing,
unrelated regression (2 failing tests in `tests/tools/test_code_health_impact.py` whose
`apply.py`-as-dependent-of-`pipeline.py` assumption has gone stale) — filed as
`TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT` rather than silently absorbed
or routed around, since fixing the forbidden test file was out of this ticket's own scope.
