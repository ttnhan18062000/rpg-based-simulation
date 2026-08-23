---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, testing]
---

# Epic Plan — Codebase Health Observatory Tooling

**Tracking ticket:** `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`
**Source:** `docs/audits/D24_codebase_health_observatory.md` §J, §L, §M Phase 3-4
**Priority:** P3, deliberately built last — most of its own inputs come from other epics' outputs (e.g. hardened boundary tests from Epic G) or from tooling that already exists.

## Problem

Most of what a "codebase health observatory" needs already exists in some form in this repo — the
gap is wiring it together and adding two genuinely missing pieces, not building from scratch:
`graphify-out/` already provides dependency-graph data (though its corpus mixes code, docs, and
tickets rather than being pure code); a churn script is cheap to make permanent but must exclude
known append-only bookkeeping files (`agent-monitoring/*.jsonl`, `tickets/working_log.csv`,
`docs/REGISTRY.yaml`) or every report drowns in expected noise; and no mechanism persists metrics
over time today.

## Scope for the eventual `create-tickets` pass

- ~~**(2026-08-19) Extracted to `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`.**
  `make codebase-health-baseline`: a permanent target producing the LoC/churn snapshot this
  session ran ad hoc, with the append-only-file exclusions baked in from the start.~~ **Resolved**
  (`TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`, 2026-08-19): built
  `tools/codebase_health_baseline.py` + `make codebase-health-baseline`, computing the LoC/churn/
  dependency table fresh from `git ls-files`/`git log`/the live filesystem on every run, with the
  `agent-monitoring/*.jsonl`/`tickets/working_log.csv`/`docs/REGISTRY.yaml` churn exclusion
  implemented as a real git pathspec (not a post-hoc filter) and verified by a synthetic-noise
  fixture test. On-demand only, not CI-wired, matching the `status-drift-check`/
  `agent-monitoring-epic-staleness` precedent this epic's Problem section already cites. Extracted
  once confirmed self-contained (no dependency on the rest of this epic's scope) — this epic's own
  prerequisite (Epic G) was also confirmed done at the same time, unblocking the epic as a whole.
- ~~**(2026-08-19) Extracted to `TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`.**
  `code-health impact <path>` command: composable from `graphify-out/`'s existing edge data,
  `tests/architecture/`'s boundary tests (post Epic G hardening), and `docs/REGISTRY.yaml`'s
  existing `related_code_areas` field — full worked design and example (`src/engine/pipeline.py`)
  in `docs/audits/D24_codebase_health_observatory.md` §L. Extracted once each of the 3 data
  sources was individually verified against real, current state — found `graphify` has no
  ready-made "dependents of path X" CLI verb (needs a custom traversal), and
  `related_code_areas` is only 53.3% filled with sometimes-mixed path/symbol-name shapes.~~
  **Resolved** (`TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`, 2026-08-19): built
  `tools/code_health_impact.py` + `make codebase-health-impact` (`code-health impact <path>`).
  Dependents lookup reuses `graphify affected "<symbol>" --depth 2` (not a hand-rolled
  BFS/DFS) after resolving the target file to its `graph.json`-recorded symbol(s);
  architecture-rule matching against `tests/architecture/`'s 17 boundary test files by
  subsystem-prefix heuristic; required-test inference combines `docs/REGISTRY.yaml`'s
  `related_code_areas` (with bare symbol-name/filename resolution via the graph's node
  index) and the `src/`→`tests/` naming convention from `.claude/agents/test-scoper.md`'s
  Test Directory Map; criticality tier from churn (extending
  `codebase_health_baseline.py::compute_churn_lines_changed()` with a new `target_pathspec`
  parameter, not duplicating it) × graphify edge-degree. Verified against D24 §L's
  `src/engine/pipeline.py` worked example (confirms `engine/kernel.py` and `engine/apply.py`
  as dependents) plus a second, differently-profiled real path
  (`src/observability/reporter.py`). On-demand only, not CI-wired, matching the sibling
  baseline target's precedent. Independent Test-phase verification also caught and fixed a
  real display bug: `kernel.py` was present in the internal dependents data but invisible in
  the truncated CLI output due to plain alphabetical sort — fixed with same-subsystem-first
  sorting and a widened truncation limit. **(2026-08-23 correction, see
  `TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT`):** `engine/apply.py` is
  no longer a real dependent of `engine/pipeline.py` in the current codebase — there is no
  import edge between them in either direction. `engine/kernel.py` (which does import
  `apply.py`) remains a correct, still-verified dependent. This does not indicate a bug in
  `tools/code_health_impact.py`'s dependents resolution; the underlying import graph drifted
  after this verification note was originally written. The test suite's second-dependent
  worked example was updated to `engine/scenario_checkpoint.py`, the current real second
  dependent, in `tests/tools/test_code_health_impact.py`.
- ~~Historical metric snapshots: an append-only file following the same pattern
  `agent-monitoring/runs.jsonl` already uses, plus a multi-dimension scorecard (trend arrows, not
  a single aggregate score, per the source audit's own explicit guidance against turning this
  into a single number).~~ **Resolved** (`TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD`,
  2026-08-23): built `tools/codebase_health_snapshot.py` + two new on-demand Makefile targets,
  `codebase-health-snapshot` (appends one `build_report()` snapshot to the new append-only
  `agent-monitoring/codebase_health_history.jsonl`, reusing `tools/agent-monitoring/writer.py::write_line`
  rather than a plain unlocked append) and `codebase-health-scorecard` (reads the history file and
  renders a per-dimension trend view). A frozen `EXPECTED_SNAPSHOT_KEYS` allowlist plus a
  `snapshot_schema_version` field (`build_snapshot_record`) make any future `build_report()` shape
  change a loud `RuntimeError` at write time instead of silent drift. The scorecard trends 11
  scalar dimensions with `↑`/`↓`/`→` + Δ (mirroring `personality_audit.py`'s own convention),
  folds `registry_size_bytes`/`registry_size_lines` into one rendered row, and shows
  `unused_core_dependencies` as a raw value/count rather than forcing it through the arrow logic
  since it's a list, not a scalar — always comparing only the two most recent snapshots. Zero- and
  one-snapshot reads degrade gracefully (an explicit "no snapshots yet" message, and an explicit
  "no trend data yet" label per dimension, respectively) rather than crashing or fabricating a
  trend. Per this epic's own "Out of scope" bullet below, no aggregate/combined score field exists
  anywhere in either the structured scorecard dict or its printed text — enforced by a dedicated
  test (`test_scorecard_output_has_no_aggregate_or_combined_score_field`) that audits both. Full
  field/schema documentation: `docs/agent-monitoring/codebase_health_history_schema.md`.
- ~~PR/AI change-impact report generator, built on top of the impact-model command above — the
  last item in sequence, since it depends on everything before it.~~ **Resolved**
  (`TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR`, 2026-08-23): built `tools/pr_impact_report.py`
  (`build_pr_impact_report()` / `format_pr_impact_report()` / `main()`) + one new on-demand
  Makefile target, `codebase-health-pr-impact`. Corrects this bullet's own "built on top of the
  impact-model command above" phrasing: this ticket is built specifically on top of the Phase 3
  impact command (`tools/code_health_impact.py::build_impact_report()`), matching D24 §M item
  11's own literal wording ("built on top of Phase 3's impact model") — not on top of the Phase 4
  historical-snapshot mechanism (`tools/codebase_health_snapshot.py`). No snapshot-history
  dependency was required or built; the investigation confirmed no real per-path join key exists
  between a single-path impact report and the snapshot mechanism's repo-wide aggregates. All 13
  real `build_impact_report()` fields are rendered per target path, batched across one or more
  paths with per-path failure isolation (one degraded or failing path never aborts the whole
  batch); `dependents_degraded`, `dependents_degradation_reason`, and `unresolved_symbols` are
  preserved verbatim in both Markdown and JSON output modes; and no aggregate/combined score
  field exists anywhere in either output mode — enforced by
  `test_report_output_has_no_aggregate_or_combined_score_field` and the standing architecture
  guard `test_report_generator_has_no_import_of_codebase_health_snapshot_module`.

## Out of scope

- A single aggregate "health score" — the source audit explicitly recommends trend arrows across
  multiple dimensions instead.

**(2026-08-19)** Epic G's boundary-test hardening is confirmed done
(`tickets/done/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC.md`) — the prerequisite that
previously gated this epic's remaining scope is cleared.

## Acceptance signal for this epic (not yet broken into child tickets)

- (LoC/churn baseline: see `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET`. Impact
  command: see `TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND`. Neither tracked here anymore.)
- Metrics persist across at least two runs in an append-only history file.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic K)
- `docs/audits/D24_codebase_health_observatory.md` (§J, §L, §M Phase 3-4)
