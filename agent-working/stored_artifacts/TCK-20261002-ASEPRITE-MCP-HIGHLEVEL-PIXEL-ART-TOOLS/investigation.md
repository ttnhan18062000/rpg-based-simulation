---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS
artifact_type: investigation
tags: [mcp, testing, rendering]
---

# Investigation — TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS

## Context scan
`search_docs` and `graphify query` for aseprite / pixel art / ART-W experiments returned nothing relevant;
the art plans were read directly (`docs/plans/render-and-art/07_manual_art_experiment_execution_plan.md`,
proposal sections 9 and 13). No existing ticket or code covers palette/shading technique.

## Web research (2026-10-02)
Readable sources: Slynyrd Pixelblog 1 (ramp method: 9 swatches, +20 degrees hue per swatch, brightness rising,
saturation peaking mid-ramp and falling at the bright end), sprite-ai.art 16x16 guide (3-8 colours; 3 hard
shade levels; top-left light; full / selective / no outline), sprite-ai.art fundamentals (palette size by
sprite size; pillow shading; "every edge outlined or none"), Wikipedia Ordered dithering (exact 2/4/8 Bayer
matrices and threshold formula), Aseprite API Image page. Two pixel-editor.com pages returned no readable
body; nothing numeric is attributed to them.

Conflict recorded, not resolved: selective outlines (one source) vs all-or-nothing (another). Tools support
both; lint reports it as info.

## Design constraints found
- The adapter's readback is a flattened 32x32 region; tiling it covers up to 128x128 but there is no per-layer
  readback. High-level readers therefore work on the flattened frame.
- `lua/ops.lua` and `adapter.py` are being edited under the hardening ticket in the same worktree, so this
  work is additive-only: new files, composing `adapter.apply_ops`.
- All maths must be deterministic (no randomness) so the same request gives the same pixels.

## Findings from building it
See the ticket's Implementation Notes (three real defects found by tests/visual check) and
`TECHNIQUE_GUIDE.md` "Lessons from using the tools".
