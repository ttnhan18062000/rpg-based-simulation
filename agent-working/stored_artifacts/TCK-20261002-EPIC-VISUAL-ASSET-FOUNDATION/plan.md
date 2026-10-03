---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION
artifact_type: plan
tags: [mcp, architecture, documentation]
---

# Plan (as built) — TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION

The epic tracks six child tickets in `agent-working/tickets/done/visual-asset-foundation/SEQUENCE.md`; it has no implementation of its own. The structure it implemented is `docs/plans/visual-asset-foundation/README.md`, whose
"As built: deviations from this proposal" section lists every place the build differs.

| # | Child | Built |
|---|---|---|
| 1 | `TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT` | drawing tools moved into `visual_assets/drawing/`, boundary test, CI step, `.mcp.json`, skeletons (merged in PR #286) |
| 2 | `TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS` | strict typed records, identities, canonical JSON, registry loader |
| 3 | `TCK-20261002-VISUAL-ASSETS-STORE-INTAKE` | handoff builder, quarantine, independent validator checked against real Aseprite, review, CLI; `ops.lua` summary gains `cels` and `aseprite_version` |
| 4 | `TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION` | human-gated `adopt` / `revoke`, all-or-nothing tracked publish, hash-linked provenance, `audit_chain` |
| 5 | `TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE` | `pixels-v1`, bounded PNG reader, the store's own render check, sandboxed build, release candidates, `verify`, `gc` |
| 6 | `TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS` | `submit_candidate`, `store_list`, `store_show`; store contract rewritten to built; epic close-out |

Order was strictly sequential on one branch (`visual-assets-store`) with a planner review after every ticket commit; planner follow-ups R1-R4, H1 and B1 were their own commits.
