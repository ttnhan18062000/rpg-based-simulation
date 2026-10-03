---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TYPE-CHECKER-TRIAL
artifact_type: plan
tags: [delivery]
---

# Plan — TCK-20261003-TYPE-CHECKER-TRIAL

Same branch (`python-code-craft-gates`). Report only: **no change** to `src/`, `pyproject.toml`, `uv.lock`, CI, Makefile, `.claude/` or CLAUDE.md. The single deliverable is a decision record.

1. **Pin the commit**: record `git rev-parse HEAD` of the measured tree (the ticket-4 follow-on or later). All three checkers run on a clean `git clone --no-hardlinks` of that commit, created by a guarded script (`set -euo pipefail`, abort unless the repo root is the clone before each step), so the numbers cannot be affected by uncommitted or ignored files.
2. **Scratch environments** (outside the repo): `uv venv` for basedpyright 1.40.1 and for pyrefly 1.3.2, each installed alone; mypy 2.1.0 is the locked one in the main environment. Configs in the scratch directory only.
3. **Measure, one checker at a time under `MemoryMax=2G`**, each cold then warm (cache cleared / reused), with `/usr/bin/time -v`: wall time, peak RSS, exit status, error and warning counts, output in machine-readable form (mypy text, basedpyright `--outputjson`, pyrefly JSON output). If a checker exceeds the cap, record the OOM kill and the cap, do not raise it.
4. **Baseline support**: create a baseline with each tool's own mechanism on the clone, edit nothing under `src/`, and show the unrelated-edit-above-an-existing-error case (shift lines) and a new-error case for each, as was done for mypy-baseline.
5. **Overlap with mypy**: (file, line) intersection and per-checker unique counts; files-with-errors intersection; top 10 rule families per checker; a few concrete examples of errors only one checker reports (to judge noise vs real signal).
6. **Decision record** `docs/plans/codebase_health/python_code_craft_type_checker_trial.md` (frontmatter valid, registered layer/tags): the commit SHA, exact commands (copy-pasteable, so the measurements are reproducible), a table of the measurements for the three checkers, baseline findings, overlap, a recommendation among keep mypy / replace / add a second checker with the reasons, and what it would cost (CI time, memory, new dependency, baseline churn) if adopted. A script `tools/code_health/` is NOT added; the commands are in the record.
7. **Verify** the record's commands once more from the record text on the same clone (a second warm run within the stated variance); docs tests and registry; no src/.claude/CLAUDE.md in the diff.
8. **Close** in the batch closure commit after the green PR run.

## Scope guards
No pyproject/lock/CI/Makefile change, no installation into the main environment, no source edit, no suppression comments. The recommendation is advice; adopting anything would be a new ticket.

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| Decision record with measurements for all three on the same commit, SHA recorded | 1, 3, 6 |
| Measurements reproducible from the commands in the record | 6, 7 |
| No src/.claude/CLAUDE.md in diff | scope guards |

## Questions for the planner
- Which docs layer and tags should the decision record carry? I would use layer `testing` and tag `delivery` like the other M4 docs unless you prefer `architecture`.
