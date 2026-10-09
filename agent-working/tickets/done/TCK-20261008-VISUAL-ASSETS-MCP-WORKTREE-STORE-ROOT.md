---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT
phase: done
date: 2026-10-08
tags: [architecture, mcp, testing]
---

# TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT

## Title
The drawing MCP server writes intakes to the checkout it serves, not always the main checkout

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Child 2 of `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING`. Every asset batch worked around `submit_candidate` writing intakes into the main checkout's quarantine (memory + review docs; 16+ stray intakes there).

## Scope
- Find how the server resolves the store/catalog root (`visual_assets/store/config.py` `_VISUAL_ASSETS`, `start_mcp.sh`
  `REPO_ROOT`, the MCP registration in `.mcp.json`) and why it lands in the main checkout.
- Make the root explicit and worktree-correct (e.g. an env var or launch argument, defaulting to the checkout the server
  was started from), refuse a root that is not a store checkout, and print the root at startup and in `store_*` tool
  results so a wrong root is visible.
- Docs: drawing_tools.md, the asset worktree tooling notes. Tests for root resolution.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art. Deleting the stray intakes in the main checkout (owner's retention rule).

## Acceptance Criteria
- [x] From a worktree-launched server, `submit_candidate` writes to that worktree; tested; root shown in results.

## Related Tickets


## Related Docs


## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT/ (plan, investigation, test_plan, mutant_proof)

## Related Code Areas
- visual_assets/drawing/server, visual_assets/start_mcp.sh, visual_assets/store/config.py, .mcp.json

## Assumptions / Open Questions


## Implementation Notes
- `store/config.py`: `VISUAL_ASSETS_CHECKOUT`, `resolve_visual_assets_dir`, `StoreRootError`, `describe_root`; roots derive from the selected checkout. Server prints the root on stderr; `store_root` label in `submit_candidate`, `store_list`, `store_show`. `.mcp.json` passes the variable (`${VISUAL_ASSETS_CHECKOUT:-}`). Docs in store_contract.md and drawing_tools.md.
- The variable selects data only; the running code is the launching checkout's. Folded in: child 1 follow-up (explicit raise in derive()).

## Test Summary
- 12 new tests (7 unit, 5 real stdio); mutants A-G caught; a mutant run polluted the real gitignored quarantine with one stray intake, removed. Scoped suites: see the commit report.

## Files Changed
- visual_assets/store/config.py, visual_assets/drawing/server/{__main__,store_readonly_tools}.py, visual_assets/start_mcp.sh, .mcp.json, tests/visual_assets/{test_store_root,derived_runtime}.py, tests/visual_assets/drawing/{test_store_root_stdio,stdio_support}.py, docs/assets/{store_contract,drawing_tools}.md, ticket and artifacts.

## Completion Summary
A drawing server started with `VISUAL_ASSETS_CHECKOUT` set to a worktree stages intakes there, refuses a value that is not a store checkout, and shows the root at startup and in every store tool result; the default is unchanged.
