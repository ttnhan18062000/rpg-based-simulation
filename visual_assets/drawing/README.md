# visual_assets/drawing — Aseprite drawing tools

Layers (each may import only the ones listed; enforced by `tests/visual_assets/test_boundaries.py`):

```
technique -> (errors, colors)           pure pixel-art maths, no I/O, no Aseprite
schema    -> config, errors, colors     request validation
backend   -> config, errors             bwrap sandbox + the pinned Lua template (backend/lua/ops.lua)
workspace -> config, errors             the EXPERIMENT workspace (revisions, jobs, locks); not the asset store
api       -> schema, backend, workspace new_sprite, apply_ops, branch, inspect, preview, filmstrip, list
compose   -> api, technique             high-level tools (shade, dither, stroke, outline, remap, lint)
server    -> api, compose               FastMCP app and tool registration (python -m visual_assets.drawing.server)
```

Rule that matters in tests: modules read limits and paths as `config.NAME` at call time, never
`from ...config import NAME`, so patching `config` reaches every module.

After editing `backend/lua/ops.lua`: `python -m visual_assets.drawing.pin`.

Tool reference: `docs/assets/drawing_tools.md`. Technique rules and sources: `docs/assets/pixel_art_technique.md`.
