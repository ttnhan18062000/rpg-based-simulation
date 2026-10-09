---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261009-PYTHON-FLOOR-3-12
phase: done
date: 2026-10-09
tags: [architecture, delivery]
---

# plan — TCK-20261009-PYTHON-FLOOR-3-12

1. pyproject: requires-python >=3.12, mypy python_version 3.12, new [tool.ruff] target-version py312 with a move-together comment.
2. `uv lock` (not --upgrade); prove the 3.13 export is unchanged apart from marker-excluded lines; report resolution-marker counts.
3. Run `make typecheck-py` then `make code-health`, one at a time under the cap; tests/static and tests/codebase.
4. Docs: README, agent_working_environment, roadmap decision 12 amendment, grade_thresholds comment; agent-working handoff.

Scope guard: no src/ (M7 candidates: src/api/schemas.py typing_extensions TypedDict import, src/lab/results.py dead fallback); tools/search/Dockerfile is agent-working's; tests/visual_assets/test_py311_fstrings.py is the asset domain's.
