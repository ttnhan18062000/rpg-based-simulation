---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1
artifact_type: investigation
phase: done
date: 2026-10-24
tags: [testing, regression, simulation-quality]
---

# Investigation

- Measured sha: 341f700d0b54ab00deab0f9b84f87321f101ca48 (#725 merge). Pinned worktree (scratchpad, detached): `/tmp/claude-1000/-mnt-data-Working-rpg-based-simulation--claude-worktrees-testing/51e0e698-5db4-400a-b86c-cd8d36be8005/scratchpad/v1`; `git -C <that path> rev-parse HEAD` = 341f700d0b54ab00deab0f9b84f87321f101ca48. `git diff e8df8b96d 341f700d0` touches no src/, content/ or config/ file.
- The runs import the pinned tree's src: the children are `sys.executable -m tools.calibrate_simq` with the pinned worktree as cwd and no PYTHONPATH (checked on a live child via /proc), and the main-checkout venv has no editable install (only a1_coverage.pth and _virtualenv.pth). `run_manifest.json` records no commit, so the cwd proof stands in. Python: the main checkout's `.venv/bin/python` (the worktree has no pydantic).
- Neither `simq_audit_rows`, `simq_run_record`, `simq_reanchor` nor `calibrate_simq` imports tests/helpers/world_build.py (changed in #725).
- Result: 162 runs (81 keys x 2), 0 failed, every pair identical on every pillar and overall, all audit_mode and signals_zeroed true (`audit_rows.jsonl`).
- 536 of 810 rows moved against the committed anchors (the #531 values, measured at b396080cc). rpg-planner: the only src/simulation_quality change in b396080cc..341f700d0 is #645's min_events gate; no scorer, weight or SimQ config changed.
- `simq_reanchor --prior-rows` refuses the #531 rows (no audit_mode field recorded), so there is no tool-made changed-since-ruling split; the committed-vs-v1 comparison in ruling_table.tsv is the evidence.
