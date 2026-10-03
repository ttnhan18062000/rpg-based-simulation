---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-TYPE-CHECKER-TRIAL
phase: open
date: 2026-10-03
tags: [benchmarking]
---

# TCK-20261003-TYPE-CHECKER-TRIAL

## Title
M4e: Type-checker trial — basedpyright and Pyrefly against mypy on src/ (report only)

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Roadmap 6.2 keeps mypy + mypy-baseline as primary and names basedpyright (native baseline) and Pyrefly as trials; `ty` is excluded because its only suppression path edits source. Produce a measured comparison and a recommendation. No CI or dependency change.

## Scope
- Run basedpyright and Pyrefly over src/ on one commit, each in a scratch environment, one at a time under a memory cap
- Record per checker: version, wall time, peak memory, error count, baseline support (no source edits), error overlap with mypy 2.1.0 on the same commit
- Decision record in docs/plans/codebase_health/ recommending keep mypy, replace, or add a second checker

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Any change to pyproject.toml, uv.lock, CI or Makefile

## Acceptance Criteria
- [ ] Decision record exists with the measurements above for all three checkers on the same commit, and the commit SHA
- [ ] Measurements reproducible from commands written in the record
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-MYPY-BASELINE-ADVISORY

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md

## Related Stored Artifacts
None.

## Related Code Areas
- pyproject.toml ([tool.mypy], read only)
- src/ (read only)

## Assumptions / Open Questions
- Independent of the other tickets; may run any time

## Implementation Notes
- Decision record: `docs/plans/codebase_health/python_code_craft_type_checker_trial.md` (frontmatter as the M4 brief, per the planner: layer `architecture`, tags `[architecture, planning, benchmarking]`). It holds the commit SHA (`e6b3f97fde4bdce921369e7c5f9190a0c9e379c3`), the measurements table, the baseline findings, the overlap with mypy, the adoption cost, the limits, and copy-pasteable commands.
- Recommendation recorded: **keep mypy + mypy-baseline as primary; do not replace it; do not add basedpyright; consider Pyrefly as a cheap advisory second opinion after the M4 soak (a new ticket), not as a gate.**
- Headline numbers (same commit, same scope: `src/` minus the five excluded V1 packages, Python 3.11, non-strict, missing imports ignored, third-party packages from the project `.venv`; each run alone under `MemoryMax=2G`, none hit the cap): mypy 2.1.0 1,569 errors in 236 files, 30.0 s cold / 0.49 s warm, 406 MB; basedpyright 1.40.1 (`standard`) 711 errors + 1 warning in 160 files, about 70 s, 1,041 MB, plus a Node runtime wheel (200 MB); Pyrefly 1.3.2 817 errors in 151 files, about 2.2 s, 207 MB, a single 33 MB wheel with no dependencies. basedpyright `basic` 684 and `recommended` 1,207 errors (+25,657 warnings) as sensitivity points. (file, line) overlap: 448 flagged by all three; 395 only by mypy, 67 only by basedpyright, 100 only by Pyrefly.
- Planner point, equivalence: basedpyright `typeCheckingMode: "standard"` is treated as the equivalent of non-strict mypy; the other two modes ran once each.
- Planner point, baselines: both alternatives have a baseline file that does not edit source (basedpyright `.basedpyright/baseline.json`, which only baselines files inside the project root, so the config and baseline must sit at the repository root; Pyrefly `--baseline FILE --update-baseline`). Pyrefly **also** has a separate `pyrefly suppress` command that writes inline ignore comments into source; it was not run, and it is the path that conflicts with decision 8.7. All three behave like mypy-baseline: an unrelated edit above existing errors is silent, a new error is reported alone. These tests wrote to the **scratch clone's** `src/` (40 inserted comment lines in one file, then an appended function) and restored the file with `git checkout`; the clone was clean afterwards and the real repository's `src/` was not touched (checked).
- Planner point, adoption cost: includes runtime dependencies. basedpyright pulls in `nodejs-wheel-binaries` (Node 24, 200 MB on disk; 274 MB environment), which matters for CI install time and for the dev/lint groups; Pyrefly is one dependency-free binary wheel.
- Method guard: all runs were done in a clean `git clone --no-hardlinks` created by a script with `set -euo pipefail` that aborts unless the repository root is the trial clone before every step (see memory note on the earlier clone incident in ticket TCK-20261003-PREK-GIT-HOOKS-OPT-IN). Config and scratch environments live outside the repository. No change to `pyproject.toml`, `uv.lock`, CI, the Makefile or `src/`.
- Not done on purpose: the findings only one checker reports were not triaged for true or false positives (stated in the record's limits); the measurements are single runs on one machine.

## Test Summary
Report-only ticket: no code. Evidence is the measurements and their reproducibility. The record's commands were run as scripts (setup, one run per checker, baseline cases) on the pinned clone; counts are exact and repeatable (mypy cold and warm produced identical sorted output; basedpyright's two runs and Pyrefly's two runs gave identical counts), times and memory are single measurements. `tests/docs`, `test_generate_registry`, `validate_frontmatter` and the old-root guard are run before the commit.

## Files Changed
`docs/plans/codebase_health/python_code_craft_type_checker_trial.md` (new), `docs/REGISTRY.yaml` (generated), this ticket and its staging artifacts, the monitoring shard. No existing test edited; nothing under `src/`, `.claude/` or CLAUDE.md.

## Completion Summary
