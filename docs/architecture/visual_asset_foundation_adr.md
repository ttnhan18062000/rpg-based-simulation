---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-10-02
tags: [architecture, mcp, documentation, rendering]
---

# ADR: Visual asset foundation (`visual_assets/`)

## Status

Accepted for D1, D5, D6, D7 (decided by the user on 2026-10-02 or forced by existing CI constraints). **Proposed, not decided:**
D2, D3, D4. Delivered so far: `TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT` (the move, the skeletons, the boundary test, CI step,
`.mcp.json` entry). The store logic is not built.

## Context

The Aseprite drawing tools existed only as a spike in `experiments/aseprite_mcp/`. The user decided the code must live in the
project proper, with a place for a managed asset store, before PR #286 merges. The asset-management plans separate agent
drawing from human adoption and runtime activation (`docs/plans/visual-asset-management-runtime-integration/`); the physical
paths were deliberately left open. Full structure, layering rules and command table: `docs/plans/visual-asset-foundation/README.md`.

## Decisions

| # | Decision | Status | Why | Reverse when |
|---|---|---|---|---|
| D1 | One root folder `visual_assets/` (`drawing/`, `store/`, `catalog/`); tests in `tests/visual_assets/` | **decided** | not `src/` (the installable engine; asset systems must never touch simulation state), not `tools/` (94 unrelated entries); root subsystems have precedent (`agent-orchestration/`, `frontend/`) | the store must ship inside the installable package |
| D5 | Human gates (`adopt`, `revoke`, release, gc deletion) are CLI-only and absent from the MCP surface | **decided** | proposal section 6: no agent or MCP server may collapse the gates | never without a new decision |
| D6 | Release **candidates** only; no active pointer, no runtime resolver | **decided** | deployment profile A vs B (`AM1-W01`) is not selected; activation is `AM-M6` | profile selected and M5 gates pass |
| D7 | One CI step `Run: tests/visual_assets` in the `api-tools` job | **decided** | CI lists test directories explicitly, so a new test root runs nowhere until added | never |
| D2 | Commit adopted `.aseprite` sources directly, no Git LFS | proposed | 16-32 px sources are about 1-5 KB each | sources exceed about 100 KB or history grows past an agreed size |
| D3 | Commit generated PNGs only for adopted assets; candidates and anything under review stay local in gitignored `visual_assets/catalog/.review/`; verify the committed ones in CI by canonical pixel hash | **decided (user, 2026-10-02)** | assets are chosen carefully and not always used, so nothing unaccepted enters git history; CI has no Aseprite, so it cannot rebuild | CI gains Aseprite, or the frontend build takes over generation |
| D4 | Hash artifacts by decoded pixels, not file bytes | proposed | PNG byte determinism across Aseprite versions is unproven | byte-exact reproducibility is demonstrated |

## Decisions taken while implementing the move (no behaviour change)

- The drawing tools' experiment-workspace package is `workspace/`, not `store/`, because `visual_assets/store/` is the asset store.
- Modules read limits and paths as `config.NAME` at call time, never `from ...config import NAME`; tests patch the owning module.
  Enforced by `tests/visual_assets/test_boundaries.py` and `tests/visual_assets/drawing/unit/test_workspace_isolation.py`.
- `technique/` may import the leaf modules `errors` and `colors` (it raises `AdapterError` and parses colours) in addition to
  other `technique` modules; it imports no I/O layer. The structure doc's table said "nothing".
- `pin_hash.sh` became `python -m visual_assets.drawing.pin`; `backend/lua/ops.lua` is byte-identical to the spike's.

## Consequences

- Drawing tools are in the project, registered in `.mcp.json`, unit-tested in CI; Aseprite-backed tests still run only where
  Aseprite and bwrap exist (`U-14` open).
- The catalog and store are empty skeletons: no asset, record or definition exists and nothing activates at runtime.
- Plan packages gain dated status notes; open items there (`U-02`, `U-05`, `U-07`..`U-14`, `AM1-W01` ...) are unchanged.
