---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL
artifact_type: investigation
tags: [architecture, testing, security]
---

# Investigation: slices in the drawing tool

- Lua bridge had `newTag` and a tag report but no slice code. Aseprite's Lua API makes frame-0 keys only, which the store parser reads as key frame 0, so "one key for all frames" is the only shape the tool can make.
- `ops.lua` is hash-pinned (`LUA_SHA256`, `drawing/pin.py`); the pin is part of NEW artifacts' build fingerprint, but `_build_revision` skips an artifact record that already exists, so committed artifacts and rebuilds of unchanged sources are not touched.
- The Python validator cannot know the canvas (a batch may `resize_canvas`), so the canvas rule is Lua's, checked for EVERY slice after the last op (planner edit 1), which also refuses a pre-existing slice a shrink would strand.
- Found by the tests: `check_no_extra` is for ops (reads `op["op"]`, allows op/layer/frame), so a nested object with an extra key raised KeyError; nested objects now use their own exact-keys check.
- The Lua pivot upper-bound check is unreachable through the tool (Python refuses first); it only guards hand-made sprites. A mutant on it survives for that reason.
