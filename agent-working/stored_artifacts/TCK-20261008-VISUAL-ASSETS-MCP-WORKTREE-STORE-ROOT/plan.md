---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT
artifact_type: plan
date: 2026-10-09
tags: [architecture, testing]
---

# Plan

1. Root cause: `store/config.py` derives every root from `__file__`; the server runs the code of the checkout the Claude session started in (`.mcp.json` relative path), so intakes landed in the main checkout while work was in a worktree.
2. `VISUAL_ASSETS_CHECKOUT` (absolute path of a git checkout/worktree; empty = unset) selects the checkout; invalid values stop the process (`StoreRootError`); `.mcp.json` passes the variable through.
3. Print the root on stderr at startup; add `store_root` (path-free label) to `submit_candidate`, `store_list`, `store_show` results.
4. Tests (unit + real stdio) and mutants; docs (`store_contract.md`, `drawing_tools.md`, launcher comment).
5. Folded in: planner's follow-up on child 1 (`derive()` raises explicitly instead of a bare `assert`).
