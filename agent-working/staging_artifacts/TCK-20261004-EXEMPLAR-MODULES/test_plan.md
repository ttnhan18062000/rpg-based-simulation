---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-EXEMPLAR-MODULES
artifact_type: test_plan
tags: [architecture, planning]
---

# Test plan — TCK-20261004-EXEMPLAR-MODULES

- Unit (`tests/codebase/test_package_exemplars.py`, scratch repo fixtures): qualifies a 60-400 line module with a docstring; rejects 59/401 lines, no docstring, `__init__.py`, a file with an exceptions row (any tool), a `do_not_imitate` path; ranks by importer count then path; caps at 3; package with no qualifier gives `[]`; `legacy` gets `[]`; `apply` changes only `exemplar_modules` and leaves other bytes/fields intact; deterministic on two runs.
- Pin: real registry exemplars have no exceptions row and each exists.
- Regression: `tests/codebase/test_package_registry.py` and `python3 -m codebase.structure.packages` still pass.
- Run under the 2 GB cap, own `--basetemp`, venv python.
