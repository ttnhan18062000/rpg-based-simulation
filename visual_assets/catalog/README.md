# visual_assets/catalog — managed store data (empty skeleton)

This tree will hold the **managed** asset store: adopted sources, semantic definitions, provenance records,
build configuration, generated artifacts, release-candidate manifests and synthetic test fixtures. At this
point it contains only the empty directory layout and `STORE_FORMAT`; **no asset, record or definition exists.**

## Who may write here

Only the store's own human-gated commands (a later ticket). The drawing tools (`visual_assets/drawing`) and
the MCP server **never** write here: an agent can draw and hand off a candidate, but only a human-run
command can adopt it. `tests/visual_assets/test_boundaries.py` enforces that the drawing code cannot even
reference this path.

## Layout

| Directory | Will hold |
|---|---|
| `definitions/` | semantic registry (`visual_keys.yaml`): finite key namespace, family, variant axes |
| `sources/<source_asset_id>/` | adopted editable `.aseprite` revisions (immutable) and their `SourceRecord`s |
| `provenance/` | immutable intake results, adoption records, revocations, licence evidence references |
| `build-config/` | pinned export rules and tool fingerprint |
| `generated/` | derived artifacts (PNG plus `ArtifactRecord`), never hand-edited |
| `manifests/candidates/` | immutable release **candidate** manifests only; there is no "active" pointer |
| `fixtures/` | synthetic fixtures for tests; cannot be mistaken for production assets |
| `.quarantine/` | intake staging; **gitignored**, created at runtime |

Nothing here activates anything at runtime: activation, runtime resolution and any `src/` or `frontend/`
consumption are out of scope of this foundation (`docs/plans/visual-asset-foundation/README.md`).
