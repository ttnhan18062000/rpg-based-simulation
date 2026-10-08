---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT
phase: open
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
- [ ] From a worktree-launched server, `submit_candidate` writes to that worktree; tested; root shown in results.

## Related Tickets


## Related Docs


## Related Stored Artifacts


## Related Code Areas
- visual_assets/drawing/server, visual_assets/start_mcp.sh, visual_assets/store/config.py, .mcp.json

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

