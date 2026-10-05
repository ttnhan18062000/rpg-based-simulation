---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-ADOPTION
artifact_type: investigation
tags: [architecture, planning]
---

# Investigation — TCK-20261004-IMPORT-LINTER-ADOPTION

Written at closure (2026-10-05) from the planner's brief (`docs/plans/codebase_health/import_linter_adoption_ticket_brief.md`), the ticket's Implementation Notes and the measurements made while implementing; the batch was run from the brief and the ticket, so these artifacts were not written before the work.

- Evaluation (`docs/plans/codebase_health/import_linter_evaluation.md`): import-linter 2.15 / grimp 3.17; `src` plus the 20 `src.<pkg>` roots; contracts c01 to c13; 2 x 2 flag matrix; injected-violation table; the 50 rules classified (8 class E).
- Pattern reused: `codebase/structure/packages.py` (registry loader, CLI shape, `--summary-out`/`--annotate`), the package-registry CI step, `tests/codebase/test_package_registry.py`.
- Measured on `898c6f35a`: `layers` baseline 135 module pairs (170 lines), all direct; at the evaluation's commit the same config gives 134 pairs; the evaluation's own 113 is not reproducible (its layers config was not kept).
- `src` must stay a root (`Missing layer 'src.lab'` without it); `.toml` via `--config` works on 2.15; `mypy`-style output wraps at terminal width and carries ANSI codes, so the parser unwraps and strips.
- Tests: only the belief test skips TYPE_CHECKING (fame, fidelity, admission, campaign state, visual_assets count it); the `visual_assets` test encodes about ten more rules than the two boundaries.
- Conflicts with PR #329: `.github/workflows/test.yml`, roadmap, `agent_working_environment.md`, `tests/static/test_ci_uv_install.py`, the ticket file, `pyproject.toml` (one pin line).

## Docs Requiring Update

- `docs/guidelines/agent_working_environment.md`: how to read the `Import contracts` step and run it locally
- `docs/plans/codebase_health/import_linter_evaluation.md`: Section 7 answered
- `docs/plans/codebase_health/python_code_craft_roadmap.md`: M5 row and decision 20
- `docs/plans/codebase_health/handoffs/handoff_to_testing.md`: Update (contracts added, no test retired, flip ticket filed)
- `docs/plans/codebase_health/handoffs/handoff_to_rpg.md`: Update (kernel.py imports allowlisted, rpg decision open)
