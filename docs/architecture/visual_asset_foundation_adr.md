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

Accepted for D1-D7 (decided by the user on 2026-10-02 or forced by existing CI constraints); nothing is still proposed.
Delivered so far: `TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT` (the move, the skeletons, the boundary test, CI step,
`.mcp.json` entry; merged in PR #286) and `TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS` (typed records, identities and the semantic
registry loader, on branch `visual-assets-store`). The store's writers (intake, adoption, build, release, verify, gc) are not built.

## Context

The Aseprite drawing tools existed only as a spike in `experiments/aseprite_mcp/`. The user decided the code must live in the
project proper, with a place for a managed asset store, before PR #286 merges. The asset-management plans separate agent
drawing from human adoption and runtime activation (`docs/plans/visual-asset-management-runtime-integration/`); the physical
paths were deliberately left open. Full structure, layering rules and command table: `docs/plans/visual-asset-foundation/README.md`.

## Decisions

| # | Decision | Status | Why | Reverse when |
|---|---|---|---|---|
| D1 | One root folder `visual_assets/` (`drawing/`, `store/`, `catalog/`); tests in `tests/visual_assets/` | **decided** | not `src/` (the installable engine; asset systems must never touch simulation state), not `tools/` (94 unrelated entries); root subsystems have precedent (`agent-working/agent-orchestration/`, `frontend/`) | the store must ship inside the installable package |
| D5 | Human gates (`adopt`, `revoke`, release, gc deletion) are CLI-only and absent from the MCP surface | **decided** | proposal section 6: no agent or MCP server may collapse the gates | never without a new decision |
| D6 | Release **candidates** only; no active pointer, no runtime resolver | **decided** | deployment profile A vs B (`AM1-W01`) is not selected; activation is `AM-M6` | profile selected and M5 gates pass |
| D7 | One CI step `Run: tests/visual_assets` in the `api-tools` job | **decided** | CI lists test directories explicitly, so a new test root runs nowhere until added | never |
| D2 | Commit adopted `.aseprite` sources directly, no Git LFS | **decided (user, 2026-10-02)** | 16-32 px sources are about 1-5 KB each | sources exceed about 100 KB or history grows past an agreed size |
| D3 | Commit generated PNGs only for adopted assets; candidates and anything under review stay local in gitignored `visual_assets/catalog/.review/`; verify the committed ones in CI by canonical pixel hash | **decided (user, 2026-10-02)** | assets are chosen carefully and not always used, so nothing unaccepted enters git history; CI has no Aseprite, so it cannot rebuild | CI gains Aseprite, or the frontend build takes over generation |
| D4 | Hash artifacts by decoded pixels, not file bytes | **decided (user, 2026-10-02)** | PNG byte determinism across Aseprite versions is unproven | byte-exact reproducibility is demonstrated |

## Decisions taken while implementing the move (no behaviour change)

- The drawing tools' experiment-workspace package is `workspace/`, not `store/`, because `visual_assets/store/` is the asset store.
- Modules read limits and paths as `config.NAME` at call time, never `from ...config import NAME`; tests patch the owning module.
  Enforced by `tests/visual_assets/test_boundaries.py` and `tests/visual_assets/drawing/unit/test_workspace_isolation.py`.
- `technique/` may import the leaf modules `errors` and `colors` (it raises `AdapterError` and parses colours) in addition to
  other `technique` modules; it imports no I/O layer. The structure doc's table said "nothing".
- Store layering deviates from the structure doc (`store.contracts -> (pydantic only)`): `contracts` also imports the store leaves
  `identities`, `errors` and `config`, and `identities` imports `errors` (its helpers raise `IdentityError`). `contracts` and
  `identities` stay free of `os`, `pathlib`, `io`, `time`, `datetime`, `subprocess`, `yaml` and `open()` (AST rule in
  `tests/visual_assets/test_boundaries.py`); only `store/catalog` may import `yaml`. A store layer without a row in
  `STORE_ALLOWED` fails the test, so each later ticket adds its own.
- `IntakeResult` is written inside the gitignored quarantine directory, not the tracked `provenance/intake/` (the structure doc's placement). Intake has no
  human gate, and D3 says nothing unaccepted enters git history; `adopt` (ticket 4) copies the result into `provenance/intake/`.
- Adoption binds its records by hash (`AdoptionRecord.intake_hash`, `SourceRecord.adoption_hash`) because `adoption_id` alone cannot show an edited approver; the remaining limit (a consistent
  edit of both records) is stated in `docs/assets/store_contract.md`. `source_asset_id` is never defaulted: naming an asset is a deliberate human act.
- Store layers `records`, `catalogwrite`, `adoption`, `revoke`, `audit` have rows too; `adoption`, `revoke` and `catalogwrite` are the human-gated writers the drawing code may never import.
- Store layers `intake`, `cli`, `__main__` have their own `STORE_ALLOWED` rows; `intake` does file I/O, only `cli` reads the clock.
- Aseprite file facts used by intake were verified against the pinned Aseprite 1.3.18.6 by round-tripping files through the real binary (integration tests).
  Notably an all-opaque-black stored palette is unverifiable without decoding pixels (see `docs/assets/store_contract.md`, known gaps).
- `pin_hash.sh` became `python -m visual_assets.drawing.pin`; `backend/lua/ops.lua` was byte-identical to the spike's until `TCK-20261002-VISUAL-ASSETS-STORE-INTAKE` added one
  read-only line to `summary()` (`res.cels`, `res.aseprite_version`) in its own reviewed commit and re-pinned `LUA_SHA256`; no op and no existing key changed.

## Consequences

- Drawing tools are in the project, registered in `.mcp.json`, unit-tested in CI; Aseprite-backed tests still run only where
  Aseprite and bwrap exist (`U-14` open).
- The store has typed records, identities and a registry loader but no writer; the committed catalog holds zero keys, sources and
  artifacts (synthetic fixtures only, under `catalog/fixtures/`). Nothing activates at runtime.
- Plan packages gain dated status notes; open items there (`U-02`, `U-05`, `U-07`..`U-14`, `AM1-W01` ...) are unchanged.
