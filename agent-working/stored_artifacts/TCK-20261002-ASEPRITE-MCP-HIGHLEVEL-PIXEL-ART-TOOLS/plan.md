---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS
artifact_type: plan
tags: [mcp, testing, rendering]
---

# Plan — TCK-20261002-ASEPRITE-MCP-HIGHLEVEL-PIXEL-ART-TOOLS

Done by asset-planner: `highlevel.py`, `highlevel_tools.py`, `test_highlevel.py`, `TECHNIQUE_GUIDE.md`.

## Remaining steps (asset-implementer), after the hardening ticket's Lua pin is coherent
1. `server.py`: after the existing tool definitions add
   `import highlevel_tools` (next to `import adapter`) and `highlevel_tools.register(mcp)` before
   `if __name__ == "__main__":`. No other change.
2. Stdio test: expected tool set gains `make_ramp, shade, dither, stroke, auto_outline, remap_palette,
   lint_sprite, ascii_view`; add one call through the protocol for `make_ramp` (pure) and `lint_sprite`.
3. README: add a "High-level tools" row group and link `TECHNIQUE_GUIDE.md`.
4. Independent review of the three new files against the ticket's acceptance criteria. Apply a mutation and
   see the test fail for at least: shading direction (swap the light sign), dither coverage (change the
   threshold formula), selout reuse (always return the darkened colour). Record results in the ticket.
5. Run the whole `experiments/aseprite_mcp/` suite in the worktree; report counts.

## Scope guards
No edits to `highlevel*.py` behaviour without telling asset-planner (report defects; fix only if trivial and
say so). No `src/`, `.mcp.json`, dependencies, CI. No push/PR without the user.

## Follow-up candidates (not this ticket)
Per-layer readback and cel offset in Lua; polygon fill; a `shade` mode limited to 2 bands for tiny materials;
calibrating lint thresholds against human-reviewed sprites.
