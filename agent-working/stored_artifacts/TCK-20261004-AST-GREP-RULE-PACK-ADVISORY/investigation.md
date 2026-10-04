---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
artifact_type: investigation
tags: [architecture, planning]
---

# Investigation — TCK-20261004-AST-GREP-RULE-PACK-ADVISORY

See the prototype findings in plan.md. Facts: ast-grep scan over `src/` 0.25 s; tree-sitter Python `except_clause` has no field names (use `has: kind: block` with `stopBy: neighbor`); a rule with `field: body` silently matched nothing (0 findings) until corrected, so each rule gets a positive test. `codebase/health/scan.py` runs tools beside the interpreter; the registry seed rewrites the whole file today (needs `--tool`). The SARIF gate only knows ruff and complexipy.
