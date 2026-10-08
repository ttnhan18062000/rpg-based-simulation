---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-PYTHON-FLOOR-3-12
phase: done
date: 2026-10-09
tags: [architecture, delivery]
---

# investigation — TCK-20261009-PYTHON-FLOOR-3-12

Planner evidence (measured on origin/main ee05ffa98): ruff without UP rules gives 8,638 findings at py311 and py313 (0 difference); mypy over src/ gives the same 1,523 errors at 3.11 and 3.13 (empty diff); mypy_baseline filter exits 0 at 3.13 and exits 1 on an injected error. Sources: uv resolution docs (requires-python range drives the forks), uv project config, PyPA writing-pyproject, ruff settings (target-version falls back to requires-python), mypy config docs, devguide versions page. Constraint: .venv-knowledge is 3.12 with this package editable-installed (agent_working_environment.md:37, :52-60, torch index blocked).

Implementer findings: pyproject had no [tool.ruff] table (only [tool.ruff.lint]), so ruff fell back to requires-python; the explicit target-version stops a floor change from retargeting it silently. The lock had 7 top-level resolution markers and 4 packages with their own marker lists; async-timeout (python < 3.11.3, via redis) and the numpy/scipy pre-3.12 forks are the only removals. tests/codebase/test_mypy_gate.py:23 is a synthetic pyproject fixture. On this machine .venv-knowledge reports Python 3.13.7, contradicting the guide's 3.12.3.
