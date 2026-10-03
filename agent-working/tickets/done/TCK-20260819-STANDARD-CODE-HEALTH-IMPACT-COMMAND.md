---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND
phase: done
date: 2026-08-19
tags: [architecture, testing]
---

# TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

## Title
Build the code-health impact <path> command from graphify + tests/architecture + docs/REGISTRY.yaml

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Item 2 of `TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`, the next item in that epic's
own dependency chain, extracted once concretely investigated. Verified all 3 of the epic's claimed
data sources against real, current state (not the epic doc's framing taken on faith): `graphify`'s
CLI has no ready-made "find dependents of path X" verb (needs a custom graph traversal over
`graphify-out/graph.json`, not just wiring); `tests/architecture/`'s 17 current boundary test
files are real and directly usable; `docs/REGISTRY.yaml`'s `related_code_areas` field is only
53.3% filled and sometimes contains bare symbol names rather than resolvable paths, requiring a
resolution step, not a literal path match.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- New script (e.g. `tools/code_health_impact.py`) implementing `code-health impact <path>`.
- Dependents lookup via direct `graphify-out/graph.json` traversal (BFS/DFS over import/use
  edges), with an explicit, documented transitive-depth cap.
- Architecture-rule matching against `tests/architecture/`'s current 17 boundary test files by
  subsystem heuristic.
- Required-test inference combining `docs/REGISTRY.yaml`'s `related_code_areas` (with symbol-name/
  bare-filename resolution, not literal path matching) and the existing `src/`→`tests/` naming
  convention already documented in `.claude/agents/test-scoper.md`'s Test Directory Map.
- Criticality tier from churn × centrality, reusing `TCK-20260819-STANDARD-CODEBASE-HEALTH-
  BASELINE-TARGET`'s churn computation once that ticket lands, cross-referenced with graphify edge
  degree for centrality — not duplicated.
- Verified against D24 §L's `src/engine/pipeline.py` worked example plus at least one additional,
  differently-profiled real path.

## Out of Scope
- Historical snapshots, scorecard, and the PR/AI report generator — remain Epic K's own bundled
  scope, built on top of this command's output shape once it exists.
- Perfect precision on architecture-rule matching or required-test inference — a discovery/triage
  aid, not a certified coverage oracle.

## Acceptance Criteria
- [x] `code-health impact src/engine/pipeline.py` produces the same shape of output as D24 §L's
      worked example, and correctly includes `engine/kernel.py` as a direct dependent.
- [x] The command generalizes to at least one other real path with a different
      churn/centrality profile, not just the one example it was designed against.
- [x] `related_code_areas` entries containing bare symbol names or filenames (not full paths) are
      resolved, not silently mishandled — and the command degrades gracefully (clearly labeled,
      not crashing) when a target path has zero `related_code_areas` hits.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC (item extracted from here; epic remains
  open for its other 2 items — historical snapshots/scorecard, PR report generator)
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET (sibling item from the same epic; this
  ticket's criticality-tier step reuses that ticket's churn computation once it lands — no other
  dependency)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)

## Related Docs
- docs/audits/D24_codebase_health_observatory.md (§L — worked design + example)
- docs/plans/codebase_health_observatory_tooling_epic.md
- .claude/agents/test-scoper.md (reusable src/→tests/ mapping reference)

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND/

## Related Code Areas
- graphify-out/graph.json
- tests/architecture/
- docs/REGISTRY.yaml
- tools/ (new script)

## Assumptions / Open Questions
- Exact transitive-dependent depth cap is left to the implementer — D24 §L's own worked example
  only shows direct dependents, so there's no existing precedent to match exactly.
- Whether this ticket's churn/centrality reuse can proceed before
  `TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET` is actually implemented, or must wait
  for it, is an implementation-order decision for whoever picks these up — not resolved here.

## Implementation Notes
Built `tools/code_health_impact.py` implementing `code-health impact <path>` (invoked as
`python3 tools/code_health_impact.py <path>` or `make codebase-health-impact ARGS=<path>`),
following plan.md's corrected design exactly (reuse `graphify affected`, don't hand-roll a
BFS/DFS).

- **Dependents lookup**: `find_file_node()` looks up the file's own node in `graphify-out/
  graph.json` (matched by `source_file` + `label == basename` + `file_type == "code"`).
  `resolve_defined_symbols()` follows that node's outgoing `contains` edges to get the symbol(s)
  graph.json records as defined in the file (confirmed live: `src/engine/pipeline.py` `contains`
  exactly one symbol, `AuthoritativeApplyPipeline`; `src/core/state.py` `contains` 36). Each
  resolved symbol is passed to `graphify affected "<symbol>" --depth 2` as a subprocess (via an
  injectable `affected_runner` param, so tests don't need the real `graphify` binary), and
  `parse_affected_output()` parses the plain-text `- <label> [<relation>] <path>:L<line>` lines.
  Results are aggregated/deduped per file and the target's own path is excluded from its
  dependents.
  Two independent real degradation modes are both handled: (1) zero `contains`-linked symbols
  (e.g. a constants-only module) — no `affected` calls made at all; (2) a resolved symbol still
  hitting `graphify affected`'s own "No unique node match" (confirmed live and real, not
  hypothetical: `src/core/movement_modes.py` unambiguously `contains` exactly one symbol,
  `MovementMode`, but 5 different node ids elsewhere in the graph share that label, so `affected`
  itself reports no unique match). Both produce a clearly-labeled empty/partial result with a
  reason string, not a crash.
- **Architecture-rule matching**: `match_architecture_rules()` uses a heuristic subsystem-prefix
  table (`ARCHITECTURE_RULE_PATH_PREFIXES`) built by reading each of the 17
  `tests/architecture/*.py` files' own docstring/imports/literal path scans (not guessed blind) —
  matches by `target_path.startswith(prefix)`.
- **Required-tests lookup**: combines (a) `docs/REGISTRY.yaml`'s `related_code_areas`, resolving
  bare symbol names via a `label -> source_file` index built from `graph.json` nodes
  (`build_label_index`) and bare filenames via a `basename -> source_file` index
  (`build_basename_index`) — confirmed live that both shapes occur in real registry data — plus
  (b) the `src/` → `tests/unit/`(`/domains/<x>`)/`tests/integration/` naming convention from
  `.claude/agents/test-scoper.md`'s Test Directory Map (only paths that actually exist on disk are
  returned).
- **Criticality tier**: extended `tools/codebase_health_baseline.py::compute_churn_lines_changed()`
  with an optional `target_pathspec: str = "."` parameter (default preserves the exact prior
  behavior — `build_report()`'s call site is unchanged and its own test suite still passes
  unmodified). Combined with `compute_edge_degree()` (in+out edge count summed across every node
  whose `source_file` is the target path, from `graph.json` directly — a lookup, not a
  traversal) to derive a high/medium/low tier via round-number thresholds grounded in this repo's
  own real observed spread (`pipeline.py`: churn 6323/degree 501 -> high; `kernel.py`: churn
  1681/degree 1410 -> high; `movement_modes.py`: churn 15/degree 251 -> medium; `reporter.py`:
  churn 20/degree 12 -> low).
- Added `make codebase-health-impact` (`ARGS=<path>`), matching `codebase-health-baseline`'s
  on-demand-only style and the existing `tag-report`/`ticket-stats-report` `ARGS=` convention.

No deviations from plan.md's steps — the plan's own two review-round corrections (reuse
`graphify affected`; extend `compute_churn_lines_changed` with `target_pathspec` rather than
duplicating it) are exactly what was implemented.

**Real bug found and fixed during independent Test-phase verification** (not caught by the
implementer's own 22 tests, all of which passed both before and after this fix): AC1 requires
`code-health impact src/engine/pipeline.py` to correctly include `engine/kernel.py` as a direct
dependent. `report["dependents"]` (the internal data structure) did contain it — the existing test
`test_real_path_pipeline_includes_kernel_as_dependent` passed — but the actual printed CLI output
never showed it. `pipeline.py` has 622 total / 68 same-src/engine/-subsystem dependents (it is the
central orchestrator most of `src/engine/` depends on), and a plain alphabetical sort of `"src/..."`
+ `"tests/..."` mixed together put `kernel.py` past position 100 in the printed, truncated
"Direct dependents" summary line — invisible in normal use even though internally correct. Fixed
with a new `sort_dependents_src_first()` helper (same-subsystem-first, then other `src/`, then
everything else, alphabetical within each tier) plus widening `format_impact_report`'s truncation
from 25 to 40 items (kernel.py sits at same-subsystem-tier index 25 — 40 gives real headroom, not a
value tuned to that exact boundary). Verified live: `src/engine/apply.py` now appears first
(matching D24 §L's exact 2-item example order), `src/engine/kernel.py` is now visibly present.
Added 2 new regression tests: one asserting `kernel.py` appears in `format_impact_report()`'s
actual formatted text (not just internal data — closing the exact gap that let this ship
unnoticed), one unit-testing `sort_dependents_src_first()`'s tiering directly.

## Test Summary
Added `tests/tools/test_code_health_impact.py` (24 tests, all passing — 22 from initial
Implement plus 2 more added during Test-phase verification, see Implementation Notes for the
real bug those 2 caught): path→symbol-node
resolution (2), multi-symbol contains-edge resolution (2), multi-symbol aggregation/dedup +
target-path exclusion (2), zero-resolvable-symbols degradation (1), "no unique node match"
degradation including the partial-degradation case (2), `parse_affected_output` line parsing (1),
mixed-shape `related_code_areas` resolution — bare symbol name and bare filename (4),
`normalize_registry_value` symbol/line-suffix stripping (1), empty `related_code_areas`
degradation at both the registry-function and full-report level (2), real-path smoke test against
`src/engine/pipeline.py` confirming `engine/kernel.py` and `engine/apply.py` appear as dependents
(1), a second real-path test against the low-centrality/low-churn `src/observability/reporter.py`
(1), `make codebase-health-impact` end-to-end (1), and a direct unit test for
`compute_churn_lines_changed()`'s new `target_pathspec` parameter proving path-scoped churn is
smaller than the repo-wide aggregate, plus a backward-compatibility test proving the default
matches the old hardcoded `"."` behavior exactly (2).

Ran `tests/tools/test_codebase_health_baseline.py` (13 tests) unmodified — all still pass,
confirming `build_report()`'s existing `compute_churn_lines_changed(repo_root)` call site is
unaffected by the new optional parameter. Also ran the full `tests/tools/` directory per
`.claude/agents/test-scoper.md`'s rule for flat `tools/*.py` changes.

## Files Changed
- `tools/code_health_impact.py` (new)
- `tests/tools/test_code_health_impact.py` (new)
- `tools/codebase_health_baseline.py` (extended `compute_churn_lines_changed()` with
  `target_pathspec` parameter)
- `Makefile` (added `codebase-health-impact` target)
- `staging_artifacts/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND/investigation.md` (modified
  during this run's own Review round, prior to Implement)
- `staging_artifacts/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND/plan.md` (modified during
  this run's own Review round, prior to Implement)
- `staging_artifacts/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND/test_plan.md` (modified
  during this run's own Review round, prior to Implement)
- `tickets/inprogress/TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND.md` (this file; moved from
  `tickets/todos/` during Scope, filled in during Implement)
- `docs/plans/codebase_health_observatory_tooling_epic.md` (Document-Update phase: struck through
  Epic K's code-health-impact-command scope item and marked it Resolved, citing this ticket ID,
  the design summary, and the real display bug found and fixed during Test-phase verification)

## Completion Summary
Implemented `tools/code_health_impact.py` (`code-health impact <path>`), which resolves a target
source path to its `graphify`-recorded symbol(s), aggregates their `graphify affected --depth 2`
dependents into a deduped file-level list, matches plausibly-relevant `tests/architecture/`
boundary tests by subsystem-prefix heuristic, infers required tests from `docs/REGISTRY.yaml`'s
`related_code_areas` (resolving bare symbol/filename entries via the graph's own node index) plus
the `src/`→`tests/unit/` naming convention, and derives a high/medium/low criticality tier from
per-path churn (extending, not duplicating, `codebase_health_baseline.py`'s churn function) and
graph edge-degree. Verified against D24 §L's `src/engine/pipeline.py` worked example (confirms
`engine/kernel.py` and `engine/apply.py` as dependents) and a second, differently-profiled real
path (`src/observability/reporter.py`, low churn/centrality); both real degradation modes
(zero-symbol files, ambiguous-label symbols) were confirmed live against real repo paths, not just
synthetic fixtures. All 22 new tests plus the unmodified 13-test `codebase_health_baseline` suite
pass.
