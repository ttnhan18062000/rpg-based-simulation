---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-INTAKE
artifact_type: investigation
tags: [architecture, mcp, testing, documentation]
---

# Investigation — TCK-20261002-VISUAL-ASSETS-STORE-INTAKE

- `search_docs` and `graphify query` again returned only unrelated material for `visual_assets/`; findings below come from direct reads and experiments.
- Format check: the Aseprite file-format specification (header, frame header, chunk header, layer, cel, tags, new and old palette chunks) was fetched and compared with
  files written by the pinned **Aseprite 1.3.18.6**. Counts of layers, frames, cels and tags agree with Aseprite's own Lua on every file tried.
- **Palette finding.** Aseprite writes an old palette chunk (0x0004) or a new one (0x2019), always with the header colour count equal to the stored entry count. The
  size Aseprite reports after reloading equals the stored count, except that a palette whose entries are all opaque black (the untouched default of a never-edited first
  revision) is rebuilt from the image: size = 1 + distinct opaque colours (blank canvas 1, one red pixel 2, two colours 3). That cannot be derived without decoding
  pixels, so intake reports `PALETTE_UNVERIFIABLE`. A file with no palette chunk reloads as 2 and a header count that disagrees with an old chunk reloads as the header
  count; neither is something Aseprite writes, so both are `SOURCE_MALFORMED`. The all-black *new-style* chunk reloads as 2 (also never written by Aseprite).
- The drawing tools do not know `cel_count` or the Aseprite version (`inspect` returns frames, layers, tags, palette size, width, height). Both are available from the
  pinned build in Lua (`#spr.cels`, `tostring(app.version)`). `ops.lua` is hash-pinned and its edit is a separate reviewed commit (user decision, option (a)).
- Existing tests pin the tool list (`EXPECTED_TOOLS`, 15 tools); no test pins the exact key set of the inspect summary.
- A session permission check blocked the first attempt at the `ops.lua` edit; the user's decision arrived through asset-planner and is not a permission in the implementer session.
