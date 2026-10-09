# visual_assets — drawing tools, asset store, managed catalog

One root folder for the visual-asset work (not `src/`, which is the installable engine and must never be
touched by asset systems; not `tools/`). Structure, layering rules and decisions:
`docs/plans/visual-asset-foundation/README.md`; decisions record: `docs/architecture/visual_asset_foundation_adr.md`.

| Path | What | State |
|---|---|---|
| `drawing/` | Aseprite drawing tools: typed ops, hash-pinned Lua, bwrap sandbox, immutable revisions, high-level pixel-art tools, stdio MCP server | built (moved here from `experiments/aseprite_mcp/`, no behaviour change) |
| `store/` | asset store logic (intake, adoption, build, release candidates, verify) | skeleton only, not implemented |
| `review/` | review tooling for draft sets: sheet rule, compliance, look-alikes, owner review folder; `python -m visual_assets.review evaluate\|review-sheets --set <id>` (reads drafts and records only) | built |
| `catalog/` | managed store data | empty skeleton |
| `start_mcp.sh` | launcher used by `.mcp.json` (`aseprite-pixel-art`) | built |

Tests live in `tests/visual_assets/` (`drawing/unit` runs everywhere; `drawing/integration` needs Aseprite and bwrap and
skips cleanly without them; `test_boundaries.py` enforces the layering). Run:
`python -m pytest tests/visual_assets -q`. The real-Aseprite tests run strictly (no skips, pinned version, evidence
JSON) only on the licence holder's machine: `make visual-assets-aseprite-local` (ADR D10; see `docs/assets/drawing_tools.md`).
