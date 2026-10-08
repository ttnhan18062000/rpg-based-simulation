---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# investigation — TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT

Source: brief section 1 and 3 A2.

The brief named test.yml:789-790, `test_ci_narrow_path_filtered_jobs.py`, `test_ci_requirements_no_ml_stack.py` and three docs. `git grep requirements.txt` found more live consumers: `tools/test_architecture/scenario_lane_paths.py:40` plus `tests/unit/tools/test_scenario_lane_paths.py:22,152`, `tests/static/test_ci_step_summary_reporting.py:19`, `tests/tools/test_evidence_cache_identity_contract.py:390`, an inline sample in `tests/tools/test_delivery_ci_triage_classifier.py:39`, and comments.

`uv.lock` contains torch, sentence-transformers, sqlite-vec and rank-bm25 behind the `knowledge` and `search-mcp` optional extras, so the ML-stack guard must walk the lock from the default roots (project dependencies + `default-groups` dev and lint); a whole-lock check would fail. Verified: the closure is 68 packages and contains none of the four.

The docs said other worktrees and `.venv-knowledge` use `pip install -r requirements.txt`: that workflow needs the on-demand export, raised in the agent-working handoff. The in-progress ticket `TCK-20261008-PERF-LANE-PATH-GATE-MISSES-SIMULATION-SRC-DIRS` edits the same test.yml regex area.
