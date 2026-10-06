---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET
artifact_type: investigation
tags: [architecture, hud, testing]
---

# Investigation — TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET

- Store, drawing tools, intake and draft keep are size-agnostic; the frontend draft harness is terrain-specific: a sibling page was built.
- The MCP server runs from the main checkout: submit_candidate writes to the main checkout quarantine; CLI intake from the worktree gives the same content-derived ids.
- decode_png defaults to 128 px; previews of 24x24 sprites are 192 px, so readers must pass MAX_PREVIEW_DIM.
- The draft export also references the 34 adopted slots (the page gets terrain tiles from the same export).
- (Corrected by the adoption ticket: adopting icons-key-v1 does NOT change that export; references skip slots the set holds and slots that are not built. The fixture needed no refresh.)
- Planner review (2026-10-06): the first debuff frame (down chevron and two light dots) read as a smiling face. Redrawn alone as a solid down arrow; a 6-wide head failed I2 against the buff in the prototype (2.8), the 4-then-2 head passes (7.7 deutan). `rule_result.txt` and the fixture are the post-redraw numbers.
