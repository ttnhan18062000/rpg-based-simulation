---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# test_plan — TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT

Normal flow: the rewritten guard passes on the real lock (closure non-empty, no forbidden package); `tests/static` passes with `requirements.txt` gone.
Failure mode: the guard asserts the closure is non-empty so a broken lock walk cannot pass vacuously.
Regression: the PERF/MIG regexes still match `pyproject.toml` and `uv.lock`; the scenario-lane regex still triggers on `uv.lock`.
Out of the run: the known 60 s local failure of the health-snapshot make-target test.

## Proof Plan
- level: static and unit tests over the repo files
- proof kind: automated tests
- oracle source: the real `uv.lock` and `pyproject.toml`; the workflow regexes extracted from test.yml
- expected effect: the guard passes on the default closure; PERF/MIG/scenario-lane regexes still match `pyproject.toml` and `uv.lock`; no test reads `requirements.txt`
- selected commands: `pytest tests/static tests/unit/tools/test_scenario_lane_paths.py` (140 passed) plus the 42 test files referencing the touched files (all pass except the known local 60 s snapshot make-target test)
