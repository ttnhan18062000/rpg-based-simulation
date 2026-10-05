---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-ADOPTION
phase: open
date: 2026-10-04
tags: [architecture, delivery]
---

# TCK-20261004-IMPORT-LINTER-ADOPTION

## Title
Adopt import-linter (advisory): layer contract from the package registry, loophole and class E contracts, registry sync, one advisory CI step

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`docs/plans/codebase_health/import_linter_evaluation.md` recommends ADD with a narrow replace. Rescoped 2026-10-05 from the planner's brief `docs/plans/codebase_health/import_linter_adoption_ticket_brief.md`. Owner decision 2026-10-04: yes, advisory first, and accept the 20 `src.<pkg>` root entries (no `__init__.py` is added to `src/`). Testing condition 1 (#322) overrides the evaluation's "retire the tests in the same change": this ticket retires NO test; the contracts and the tests both run during the advisory soak (an accepted, time-boxed double copy). The flip and the retirement are `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` (BLOCKED).

## Scope
- Exact-pin `import-linter` in the `lint` group, `uv.lock`, and the `requirements.txt` export if the lane requires it; re-run `tests/static` after the pin
- `[tool.importlinter]` in `pyproject.toml`: root packages = the 20 `src.<pkg>` namespace roots (plus `src` if the evaluation's reproduction needs it), `include_external_packages = true`; one global `exclude_type_checking_imports` value, with the contracts whose semantics change listed and the reason stated
- A `layers` contract generated from `codebase/structure/package_registry.jsonl`; the 99 or 113 current violations (matching the TC choice) in `ignore_imports`, `unmatched_ignore_imports_alerting` so a fixed import shows as stale
- Contracts for the 8 class E rules and the loopholes (plain `import`, `from pkg import module`); the stale phase18 allowlist entry; phase19's 5 `kernel.py` function-local imports (lines 149, 304, 305, 316, 1241) in `ignore_imports` with the reason "pending rpg decision, handoff_to_rpg.md"; `visual_assets` only if a root for it needs no file in `src/`
- Registry sync: a test in `tests/codebase/` (every `src.<pkg>` root in the registry is a root package in the config; the generated `layers` contract matches the registry) and a generator `python3 -m codebase.structure.<module>` that rewrites the contract, with a `--check` mode
- CI: one advisory step (step summary, one `::warning::` on a broken contract, never a failing exit) as the last step of the job that runs the package-registry validator, `continue-on-error` if that job may be blocking; the YAML diff is that one step (PR #329 edits the same file). The scenario lane `PERF_RE` pin and the `tests/static/` job-set pins stay green
- Docs: `docs/guidelines/agent_working_environment.md`, roadmap M5 row and Section 8 note (decision 8.20), `import_linter_evaluation.md` Section 7 answered; an `infrastructure.yaml` parity entry only if the other codebase gates have one
- Handoffs: a short Update in `handoff_to_testing.md` (contracts added, no test retired, flip ticket filed), a line in `handoff_to_rpg.md` (condition 3 open, five imports allowlisted)
- File ticket 2 BLOCKED and add it to `SEQUENCE.md`

## Out of Scope
- Any file under `src/` (including `__init__.py`)
- Retiring or editing any test in `tests/architecture/` (testing condition 1; the phase19 test and the `or True` assert at `tests/unit/observability/test_decision_trace.py:376` are not touched)
- The 42 rules the evaluation says stay tests
- Making the step blocking or a required check (ticket 2)

## Acceptance Criteria
- [ ] Contracts run locally and in an advisory CI step with a step summary and one warning annotation on a broken contract; the step can never fail the job (tested explicitly, also for the `Code health` job after #329)
- [ ] Parity table for all 8 class E rules (injected violation, test result, contract result), made in a scratch copy, in Test Summary
- [ ] Registry-sync test and generator `--check` pass; `tests/static` green after the pin
- [ ] No test retired or edited; `git diff --stat origin/main...HEAD` lists no path under `src/`
- [ ] Ticket 2 filed BLOCKED and in `SEQUENCE.md`; handoffs updated; `docs/REGISTRY.yaml` regenerated

## Related Tickets
- TCK-20261004-IMPORT-LINTER-EVALUATION
- TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC
- TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT

## Related Docs
- docs/plans/codebase_health/import_linter_adoption_ticket_brief.md
- docs/plans/codebase_health/import_linter_evaluation.md
- docs/plans/codebase_health/src_package_structure_audit.md

## Related Stored Artifacts
None.

## Related Code Areas
- pyproject.toml, uv.lock
- tests/architecture/ (read only)
- codebase/structure/

## Assumptions / Open Questions
- The `exclude_type_checking_imports` option is global, while the tests differ on `TYPE_CHECKING`: decide the single setting and accept the changed semantics for the rules that disagree (decision recorded in Implementation Notes)
- `src/engine/intent` has no `__init__.py` inside a regular package and stays uncovered (accepted by the owner, 2026-10-04)
- Conflicts with PR #329 (merge 2026-10-18): `.github/workflows/test.yml`, roadmap, `agent_working_environment.md`, possibly `pyproject.toml`, and this ticket file; the planner is told which files conflict before any resolution

## Implementation Notes
### Decision: `exclude_type_checking_imports = false` (global, 2026-10-05)
import-linter has one global TYPE_CHECKING switch; the tests disagree (evaluation Section 3). Options measured there:
- **false (chosen):** a `TYPE_CHECKING` import counts. No contract is looser than the test it will replace: the four whose tests count TC (`c09` admission, `c11` rendering, `c12` entities, `c13` campaign state) stay exact; `c06` is unchanged. Layers baseline is 113 import lines.
- true: layers baseline 99, and `c01/c04/c08` need no pins, but `c09/c11/c12/c13` would miss a TC injection (the evaluation's "missed" rows), so retiring those tests in ticket 2 would lose coverage.

Per-contract semantic change (tests that skip TC today; the contract flags a NEW `TYPE_CHECKING` import in these where the test would not):
- `c01_core_not_domains`: 4 existing TC imports pinned in `ignore_imports`
- `c04_domains_not_obs_pinned`: 2 pinned
- `c08_domain_models_pure` (belief/fame/fidelity): 1 pinned
- `c02`, `c03`, `c05` (phase18) and `c07` (api guard): baseline 0 with TC counted, no pin; same change for new TC imports
Unchanged semantics: `c06`, `c09`, `c11`, `c12`, `c13`. The exact pinned lines are written with the contracts, and `unmatched_ignore_imports_alerting` makes a fixed one show as stale.

### Pin and config (first implementation commit)
`import-linter==2.15` (grimp 3.17) added to the `lint` group; `uv.lock` re-locked (adds only those two packages). The `requirements.txt` export is unchanged: it is built from the default dependency set without `lint`. `tests/static/test_ci_uv_install.py` (lint group membership) updated to include `import-linter`; `tests/static` plus the scenario-lane pin pass (82 passed). Local runs: `uvx --from import-linter==2.15 lint-imports --config codebase/structure/importlinter.toml`, or `lint-imports` from the `lint` group after `uv sync`.

### Placement (planner review of 37b317e87, 2026-10-05)
The whole config lives in `codebase/structure/importlinter.toml` (codebase domain root), not in `pyproject.toml`: a generator must not rewrite a hand-edited pyproject, and the pyproject conflict with #329 drops to the one pin line. Verified on 2.15: `--config` reads a `.toml` file with `[tool.importlinter]` tables. `[tool.importlinter]` was removed from pyproject in this commit; the pin stays there.

### Roots: `src` and the 20 `src.<pkg>` together (checked 2026-10-05)
`src` is needed: a config without it fails with `Missing layer 'src.lab': module src.lab does not exist.` (the 16 regular packages are only reachable through `src`). With `src` plus the 20 roots listed together (overlapping roots) the graph builds: `Analyzed 849 files, 4555 dependencies.`

### Layers contract and baseline
`python3 -m codebase.structure.import_contracts` writes the generated block (layer order from the registry's `layer` column; siblings in one layer joined with `:` so they may import each other; order consumer, simulation-systems, engine, domain, content-pipeline, foundation); `--check` exits 1 if it is stale; `seed-baseline` reruns lint-imports with an empty baseline and rewrites `codebase/structure/import_layers_baseline.txt`. On `898c6f35a` the contract reports **135 module pairs** (170 import lines, all direct, TYPE_CHECKING counted). Reconciliation with the evaluation's 113 lines (99 with TC excluded), measured 2026-10-05 with this same config: at the evaluation's commit `c4304a7a3` it reports 134 pairs / 169 lines (151 lines with TC excluded), so the 6 `src/` commits since then add 1 pair and 1 line; the remaining gap (169 vs 113) is not `src/` drift. The evaluation's own layers config is not preserved (its Appendix A omits it), so its 113 is not reproducible; it must have used a different layer or root set. This ticket's number is the one reproduced by `import_contracts --check` and `seed-baseline`. `unmatched_ignore_imports_alerting = "warn"` marks a fixed import as stale. `tests/codebase/test_import_contracts.py` pins: block up to date, roots equal `{src}` plus every registry package without an `__init__.py` (a 21st namespace package fails), every registry package in the contract. The sync test never looks for an unregistered package in `src/` (the registry validator reports those), so it cannot fail another domain's PR.

## Test Summary

## Files Changed

## Completion Summary
