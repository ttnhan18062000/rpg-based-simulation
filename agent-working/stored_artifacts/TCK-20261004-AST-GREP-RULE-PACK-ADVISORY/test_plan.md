---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
artifact_type: test_plan
tags: [architecture, planning]
---

# Test plan — TCK-20261004-AST-GREP-RULE-PACK-ADVISORY

- Rule tests (`ast-grep test`): invalid snippet fires, valid snippet does not, per rule, plus the false-positive guards listed in the plan; run from `tests/codebase/test_ast_grep_rules.py`.
- Adapter (`tests/codebase/test_code_health_adapters.py` extended or a new file with a captured ast-grep stream under `tests/fixtures/code_health/`): key shape, enclosing symbol for method, nested function and module level, aggregation per (file, symbol, rule), no line in the key.
- Seed `--tool`: other tools' rows byte-identical; ast_grep rows keep `reviewed`/`added_date` on reseed; unknown tool rejected.
- Scan/collect: missing binary gives `ToolUnavailableError`; `check` on a scratch repo exits 1 on a new ast_grep violation and 0 after seeding.
- Regression: existing `tests/codebase` files and the CI-pinning static tests, in two chunks under the 2 GB cap.

## Proof Plan
level: unit + integration; proof kind: positive/negative rule tests and a registry-diff check; oracle source: the standard's N3, N4, E3 text; expected effect: rules fire only on violations, the registry diff touches ast_grep rows only; selected commands: `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0 .venv/bin/python3 -m pytest tests/codebase/test_ast_grep_rules.py tests/codebase/test_code_health_adapters.py tests/codebase/test_code_health_ratchet_registry.py`.
