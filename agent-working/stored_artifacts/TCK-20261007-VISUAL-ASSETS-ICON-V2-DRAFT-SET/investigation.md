---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET
artifact_type: investigation
tags: [architecture, testing, hud]
---

# Investigation — TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET

- The Aseprite MCP tools are wrappers over `visual_assets.drawing.api`; drawing 22 icons by pasting ops would be ~200 KB of tool input, so the script calls the API directly (planner accepted; the handoff `limitations` text says so; no field claims an MCP call).
- The preview manifest's `width / scale` is the native icon size, so the page no longer needs a hard-coded size list (ICON_SIZES stays only as a fallback for the key set).
- The v2 export carries the same 34 adopted terrain and border references as the key-set export, so the fixture holds 56 PNGs (22 icons plus those 34); the isolation guard's pin moves from 95 to 151 on purpose.
- The rule on the real art: PASS; no redraw was needed, so no FAIL was reported.
