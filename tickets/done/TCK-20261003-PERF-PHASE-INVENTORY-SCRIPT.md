---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT
phase: done
date: 2026-10-03
tags: [performance, architecture, engine]
---

# TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT

## Title
Re-runnable inventory of the authoritative pipeline's phase calls, with a drift check against the documented counts (PA-05A, evidence only)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The repository states four different phase counts for the authoritative refinement pipeline: 37 (`subphase_domain_contracts_epic.md`), 38 (`docs/audits/D19_domain_phase_inventory.md`), 39 (`docs/engine/authoritative_pipeline.md`, generated `AGENTS.md`, `CLAUDE.md`), and 44 static `run_phase()` calls in `AuthoritativeApplyPipeline.refine` on 2026-10-02 (it was 43 on 2026-09-08). Nobody has shown whether these are the same counted unit. PERF-D6 (phase-catalog authority) cannot be drafted without that evidence, and RPG-core work keeps adding phases, so a written table goes stale within weeks.

Build a read-only script that derives the inventory from source every time it runs, and one committed report produced by it. This is PA-05A of the performance prerequisite plan: evidence only. It changes no engine code, promotes no catalog, and edits no authority-P1 document.

## Scope
- Add `tools/perf/phase_inventory.py`: parse `src/engine/pipeline.py` with `ast` (no import of engine code, no execution) and emit, for every `run_phase()` call inside `AuthoritativeApplyPipeline.refine`, in source order: ordinal, phase name literal, source line, feature flag argument if any, the callable it dispatches to (method or function name as written), and whether the call sits inside a conditional or loop
- Also list phase-like operations in `refine` that do not go through `run_phase()` (direct calls that transform `update` between phases), flagged as a separate category, so the counted units can be told apart
- Extract the documented phase lists from `docs/engine/authoritative_pipeline.md` and `docs/audits/D19_domain_phase_inventory.md`, and the count stated in `tools/agent_orchestration_codex_adapter/generator.py::_AUTHORITATIVE_PIPELINE_NOTE` and `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`; report, per source, the count it states and which executable phase names it has no entry for, and which of its entries match no executable phase
- Cross-reference each executable phase name against `src/engine/phase_domain_permissions.py` and `src/domains/optimization/` phase-dependency declarations (wherever `PhaseDependencyGraph` keeps its phase names): report names known to one and not the other
- Output formats: `--format json` (stable key order, no timestamps, so two runs on the same tree are byte-identical) and `--format md`
- `--check <path-to-committed-json>` mode: exit 0 when the live inventory equals the committed one, exit 1 with a readable diff of added/removed/reordered phases otherwise. Report-only: it is not wired into CI or any gate by this ticket
- Commit one generated report, `docs/performance/phase_inventory.json` plus `docs/performance/phase_inventory.md`, with valid frontmatter on the markdown file and a header stating the commit it was generated from and the command that regenerates it
- Tests under `tests/tools/` covering: a synthetic pipeline source with conditional, flagged, and direct phase-like calls; deterministic output; `--check` pass and fail; and one test that runs the script against the real `src/engine/pipeline.py` and asserts only that it parses and returns a non-empty, duplicate-free ordinal sequence (not a fixed count)
- Add the new tool and test to the test-scope map the same way `tools/perf` siblings are mapped (`TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES` is the precedent)

## Out of Scope
- Any edit under `src/`
- Editing `docs/engine/authoritative_pipeline.md`, `AGENTS.md`, `CLAUDE.md`, the generator note, or any other authority-P1 or generated document — the report states the discrepancy; it does not repair it
- Deciding which count is right, proposing a catalog schema, or choosing a catalog authority — that is PERF-D6, drafted by the planner session from this ticket's output
- Wiring `--check` into CI, pre-commit, or `done-checker`
- Asserting a fixed phase count in any test; RPG-core changes the count on purpose
- Timing or cost measurement of any phase

## Acceptance Criteria
- [x] `python3 tools/perf/phase_inventory.py --format json` runs from the repository root without importing `src`, and two consecutive runs produce byte-identical output
- [x] The report lists every `run_phase()` call in `refine` in source order with name, line, flag, dispatch target, and conditional/loop context, and separately lists direct phase-like operations
- [x] For each of the four documented sources the report gives the stated count, the executable phases it does not list, and its entries that match no executable phase, so the difference between 37, 38, 39, and the live count is explained by named phases and counted unit, not asserted
- [x] The report lists phase names present in the pipeline but absent from phase-domain or phase-dependency declarations, and the reverse
- [x] `--check` exits 0 against the committed JSON on an unchanged tree and exits 1 with a named-phase diff when a phase is added, removed, or reordered in a synthetic fixture
- [x] `docs/performance/phase_inventory.json` and `.md` are committed, generated by the script, and state their source commit and regeneration command
- [x] Tests pass; none asserts a fixed real-pipeline phase count
- [x] `git diff` touches only `tools/`, `tests/tools/`, `docs/performance/`, `docs/REGISTRY.yaml`, `tickets/`, `stored_artifacts/`, `agent-monitoring/`, and the test-scope map file

## Related Tickets
- TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC (this is its `PERF-M0-T08` evidence half)
- TCK-20260913-PERF-M0-OWNER-TRIAGE (C-02 disposition, finding F-07)
- TCK-20260627-P1E-DOMAIN-INVENTORY (prior one-off inventory, D19; reused as a comparison source, superseded as a method)
- TCK-20260518-PHASE-DEPENDENCY-GRAPH
- TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (C-02, PERF-D6 stub)
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_prerequisite_execution_plan.md` (PA-05A)
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` ("Plan review, 2026-10-02")
- `docs/engine/authoritative_pipeline.md`
- `docs/audits/D19_domain_phase_inventory.md`
- `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260913-PERF-M0-SOURCE-AUDIT/source_inventory.md`
- `stored_artifacts/TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT/` (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- `src/engine/pipeline.py` (read only)
- `src/engine/phase_domain_permissions.py` (read only)
- `src/domains/optimization/` (read only)
- `tools/agent_orchestration_codex_adapter/generator.py` (read only)
- `tools/perf/`, `tests/tools/`

## Assumptions / Open Questions
- Evidence-only release: the prerequisite plan lets PA-05A start before PERF-D6 when the P1 owner records a no-behavior-change disposition. The repository owner approved starting the foundation slice, which lists this item, on 2026-10-02; the ownership model is in the roadmap's "Plan review, 2026-10-02"
- The owner's technology direction (prefer established tooling) does not change this ticket: `ast` from the standard library is the established way to do this, and no third-party dependency is needed
- If the documented phase lists are prose and cannot be extracted reliably, report that for the affected source with the lines examined, and extract what is unambiguous; do not hand-type a list into the script to make the comparison look complete
- If `run_phase` is called with a non-literal name anywhere, list the call with its expression text and mark the name as dynamic
- The planner session reviews the report before this ticket closes

## Implementation Notes
Hand-orchestrated by perf-implementer in the shared worktree. Stdlib `ast` only; the dispatch target is the first call in a phase lambda that is not a method of the lambda's own argument. Added a third category beyond the ticket text: direct `ClassName.method(...)` calls outside `run_phase()` (heuristic, labelled as such), because `FactionDecisionPhase.execute` is wired in without assigning to `update`. `--check` ignores source line numbers; exit 2 means an unreadable committed report. The markdown header names the commit the report was generated from (the parent of the commit that adds it).

## Test Summary
`python3 -m pytest tests/tools/test_phase_inventory.py tests/tools/test_test_scope_coverage_static.py -q` -> 59 passed. 30 new tests (synthetic pipeline with conditional, loop, flagged, dynamic-name, direct operation and direct call; extractors; deterministic output; `--check` pass and fail for added, removed, reordered; unreadable committed file; a subprocess check that `src` is never imported; the real pipeline parses with non-empty duplicate-free ordinals). No test asserts a real phase count. `phase_inventory.py --check docs/performance/phase_inventory.json` exits 0; two JSON runs are byte-identical. perf-planner reviewed the report with no changes.

## Files Changed
- tools/perf/phase_inventory.py (new)
- tests/tools/test_phase_inventory.py (new)
- tools/gate_checks/test_scope_coverage_static.py (one line in `_TOOLS_PERF_BASENAME_MAP`)
- docs/performance/phase_inventory.json, docs/performance/phase_inventory.md (generated)
- tickets/todos/perf-evidence-inventories/ -> tickets/done/ (this file); stored_artifacts/; tickets/working_log.csv, docs/REGISTRY.yaml, agent-monitoring/ (closure bookkeeping)

## Completion Summary
Re-runnable phase inventory delivered. On this tree: 44 `run_phase()` calls, 9 direct `update` assignments, 5 direct class-method calls; `authoritative_pipeline.md` states 39 and lists 39 names (6 live phases missing, 1 entry matching nothing); D19 states 38 and lists 36; the generator note says 39 and the subphase epic says 37 (counts only); 14 pipeline phases are absent from `PhaseDependencyGraph.PHASES`; `phase_domain_permissions.py` keys are the 7 kernel `TickPhase` members. No `src/` or P1/generated doc edit.

Known follow-up (not done here): `.claude/agents/test-scoper.md` carries a copy of the test-scope map and was not updated for `tools/perf/phase_inventory.py`, because agent files belong to the agent-working domain and are outside this ticket's allowed paths; perf-planner raises it with the user.
