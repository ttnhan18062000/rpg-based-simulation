---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# plan — TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT

1. `git rm requirements.txt`; drop it from `PERF_RE`/`MIG_RE` in test.yml and from `scenario_lane_paths.py`.
2. Repoint every pin found by grep (not only the brief's list): scenario-lane tests, step-summary test, evidence-cache test, triage sample, comments.
3. Rewrite `test_ci_requirements_no_ml_stack.py` to walk `uv.lock` from the default install roots.
4. Update pyproject comments and the human docs.

Scope guard: no `src/`; `requirements-knowledge.txt` stays (proposed to agent-working); history docs and others' tickets untouched.
