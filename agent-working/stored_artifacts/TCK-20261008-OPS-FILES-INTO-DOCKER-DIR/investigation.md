---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# investigation — TCK-20261008-OPS-FILES-INTO-DOCKER-DIR

Source: brief section 3 B1 and the planner's notes.

`git grep` consumers beyond the brief: `agent-working/reviews/code_exporter.py` (infrastructure file list), `tools/test_architecture/scenario_lane_paths.py` (`grafana/` in IRRELEVANT_RE), docs (`infrastructure_overview.md`, `simulation_watchdog.md`, README). `tests/architecture/test_docker_compose_dependency_hygiene.py` and `tests/logging/test_loki_cardinality.py` used cwd-relative paths.

A1 note: with the runtime `COPY src/` removed, `python -m src serve --help` runs from the installed package, but `git grep 'Path(__file__)'` in `src/` shows modules computing repo-root paths from their own location (`src/content/validator.py:82 parents[2]`, `src/engine/capability.py:8`, agent_ops_dashboard `parents[3]`). From site-packages those resolve wrongly, so the second COPY stays.

Docker builds run in dockerd (not bounded by the cgroup cap); machine load was ~2 of 6 CPUs and no other build was known to be running.
