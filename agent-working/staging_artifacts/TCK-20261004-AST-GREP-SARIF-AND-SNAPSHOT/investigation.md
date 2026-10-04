---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT
artifact_type: investigation
tags: [architecture, delivery]
---

# Investigation — TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT

- `sarif_feedback._tool_sarif` runs ruff and complexipy only; filters per ratchet unit; `run()` maps `SarifError` to exit 2 with a warning.
- `ast-grep scan --config codebase/rules/sgconfig.yml <file> --format sarif` works with the pinned ast-grep-cli; exit 0 with findings; `ruleId` is the rule id (`e3-silent-except`); result has `region.startLine`; no enclosing symbol.
- Registry key for ast_grep: `(file, enclosing symbol or <module>, "ast_grep", rule id)`, value = findings count (`adapters.adapt_ast_grep`; symbol from stdlib `ast` spans).
- `scan.OFFLINE_TOOLS` excludes `ast_grep`; the snapshot's `compute_craft_metrics` has no ast-grep dimension.
- Snapshot history: `EXPECTED_SNAPSHOT_KEYS` is exact; schema doc requires a version bump and a paired doc update for any key change; tests pin version 2 (`test_codebase_health_snapshot_craft.py`).
