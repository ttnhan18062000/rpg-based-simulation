---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL
artifact_type: plan
tags: [architecture, testing, security]
---

# Plan (op shape approved by asset-planner with three edits)

`set_slice {name,x,y,w,h,center?,pivot?}`: Python pre-checks (names, int ranges, centre/pivot inside slice, <=16 per batch), Lua per-op check and replace-by-name, Lua final-canvas check of every slice before saving, `inspect` slices, handoff `slice_count` (always when >=1, omitted when 0), intake `SLICE_COUNT_MISMATCH` (absent = unchecked), `MAX_SLICES` parity with the store, Lua re-pinned, docs.
