---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-EXEMPLAR-MODULES
artifact_type: investigation
tags: [architecture, planning]
---

# Investigation — TCK-20261004-EXEMPLAR-MODULES

- Registry: 36 rows (34 active, 2 legacy), all `exemplar_modules: []`; validator `codebase/structure/packages.py::_path_problems` already enforces at most `MAX_EXEMPLARS` and that cited paths exist, so no schema change.
- Exceptions baseline `codebase/baselines/code_health_exceptions.jsonl`: rows keyed by `file` (e.g. `src/__init__.py`), tools ruff, complexipy, line_count, ast_grep, jscpd; any row for a file disqualifies it.
- Existing tests: `tests/codebase/test_package_registry.py` covers the validator; the pin test is new.
- Related docs: audit `docs/plans/codebase_health/src_package_structure_audit.md` (Method, Package decisions, Findings, Handoff); roadmap 6.4.
