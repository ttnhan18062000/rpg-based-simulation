---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT
artifact_type: test_plan
tags: [architecture, delivery]
---

# Test plan — TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT

- `adapters.symbol_resolver`: method, nested def, class, module-level, unparseable file -> `<module>`; `adapt_ast_grep` tests unchanged.
- SARIF (`test_code_health_sarif_feedback.py`, real ast-grep in a scratch project plus hand-written SARIF for the filter): a new ast-grep finding is kept; a grandfathered one (count <= ceiling) is dropped; an over-ceiling group is kept whole; missing binary (monkeypatched `_find`) -> exit 2, summary line, warning, no SARIF written; summary text names ast-grep.
- Snapshot: metrics with and without ast-grep findings (n3/n4/e3 values); the existing 14 values identical on the same fixture before and after; `OFFLINE_TOOLS` includes `ast_grep`; schema version 3 and exact key set; history schema doc has the version-3 row (doc test if one exists for earlier versions); old-record scorecard tolerance test still passes.
- Run under the 2 GB cap, venv python, own `--basetemp`; heavy `tests/codebase` files in two chunks.
