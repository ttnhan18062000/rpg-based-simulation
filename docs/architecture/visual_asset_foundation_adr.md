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

Accepted for D1-D7 (decided by the user on 2026-10-02 or forced by existing CI constraints) and D8-D10 (decided by the user on 2026-10-03: deployment profile, trust, where Aseprite may run); nothing is still proposed.
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
| D6 | Release **candidates** only; no active pointer, no runtime resolver | **decided**; D8 (2026-10-03) selects Profile A, under which there is never an asset-only active pointer: activation will be the frontend deployment itself (`AM-M6`, dormant). A read-only resolver may exist in an isolated rehearsal harness (`AM-M5`) | activation is `AM-M6` | M5 gates pass and `AM-M6` is separately authorized |
| D7 | One CI step `Run: tests/visual_assets` in the `api-tools` job | **decided** | CI lists test directories explicitly, so a new test root runs nowhere until added | never |
| D2 | Commit adopted `.aseprite` sources directly, no Git LFS | **decided (user, 2026-10-02)** | 16-32 px sources are about 1-5 KB each | sources exceed about 100 KB or history grows past an agreed size |
| D3 | Commit generated PNGs only for adopted assets; candidates and anything under review stay local in gitignored `visual_assets/catalog/.review/`; verify the committed ones in CI by canonical pixel hash | **decided (user, 2026-10-02)** | assets are chosen carefully and not always used, so nothing unaccepted enters git history; CI has no Aseprite, so it cannot rebuild | CI gains Aseprite, or the frontend build takes over generation |
| D4 | Hash artifacts by decoded pixels, not file bytes | **decided (user, 2026-10-02)**; algorithm `pixels-v1` recorded in `docs/assets/store_contract.md` (sha256 over a magic, width and height as u32 big-endian, then non-premultiplied RGBA rows with alpha-0 pixels zeroed) | PNG byte determinism across Aseprite versions is unproven | byte-exact reproducibility is demonstrated |
| D8 | Deployment profile A (`AM1-W01`): the semantic registry, the runtime manifest, the artifacts and the frontend client form one immutable deployable release built by Vite; activation and rollback are the normal reviewed deployment of a whole frontend release; there is no asset-only active pointer and no bootstrap record | **decided (user, 2026-10-03)** | the repository builds one Vite frontend and has no asset service; Profile B's bootstrap, compare-and-swap pointer, cache fencing and trust channel are justified only by a measured need (proposal 8.1) | asset replacement cadence, size or a native client needs independent activation (then Profile B is a new decision, not an extension) |
| D9 | No signing or separate trust channel for assets (`AM1-W08`, `AM-U09` for Profile A): integrity is the `pixels-v1` hash plus the hash-linked provenance chain, checked by `verify` in CI; authenticity and authorization are the reviewed git history and the normal frontend deployment, the same as for the client code itself | **decided (user, 2026-10-03)**, follows from D8 | under Profile A the assets ship inside the client build, so they cannot be swapped without swapping the client; a signature would protect nothing the deployment does not already protect | Profile B is chosen, or assets are fetched from anywhere other than the client's own build output |
| D10 | Real Aseprite runs only on the licence holder's own machine (`U-02`, `U-14`): never installed, built, cached or uploaded on GitHub-hosted runners or any shared machine; the real-Aseprite tests stay local and run through one strict make target that refuses to skip; CI states the skipped count. Facts and clauses: `docs/assets/aseprite_licence_review.md` | **decided (user, 2026-10-03)** | the EULA grants installation and use "on your computer" (1a), forbids distribution to third parties (2b) and allows compiling the source only "for your own personal purpose" (2g); a hosted runner is a third party's computer | the licensor grants written CI or server use, or a self-hosted runner on the licence holder's own machine is set up (a new decision) |

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
- Store layers `pixels` (pure PNG decoding and the hash, shared by intake and build), `rendering` (the injected-renderer comparison shared by review and adopt), `review`, `build` (the one layer that imports the shared sandbox from
  `drawing`), `release`, `verify`, `gc` have rows too; the human-gated or tracked-catalog writers `adoption`, `revoke`, `catalogwrite`, `release`, `gc` are never importable from the drawing code. `assemble_release` is
  `store/release.py`, not `store/catalog/release.py`, because it needs records and eligibility.
- `adopt` re-renders the source itself and never trusts a stored render check (the quarantine is writable by any local process); see the store contract.
- Store layers `records`, `catalogwrite`, `adoption`, `revoke`, `audit` have rows too; `adoption`, `revoke` and `catalogwrite` are the human-gated writers the drawing code may never import.
- Store layers `intake`, `cli`, `__main__` have their own `STORE_ALLOWED` rows; `intake` does file I/O, only `cli` reads the clock.
- Aseprite file facts used by intake were verified against the pinned Aseprite 1.3.18.6 by round-tripping files through the real binary (integration tests).
  Notably an all-opaque-black stored palette is unverifiable without decoding pixels (see `docs/assets/store_contract.md`, known gaps).
- `pin_hash.sh` became `python -m visual_assets.drawing.pin`; `backend/lua/ops.lua` was byte-identical to the spike's until `TCK-20261002-VISUAL-ASSETS-STORE-INTAKE` added one
  read-only line to `summary()` (`res.cels`, `res.aseprite_version`) in its own reviewed commit and re-pinned `LUA_SHA256`; no op and no existing key changed.

## Consequences

- Drawing tools are in the project, registered in `.mcp.json`, unit-tested in CI; Aseprite-backed tests still run only where
  Aseprite and bwrap exist (`U-14` open).
- The store is built through its last child: records and identities, intake, human-gated adoption and revocation, sandboxed build, release candidates, `verify`, `gc`, and read-only MCP store tools (`submit_candidate`, `store_list`, `store_show`). The committed catalog
  held zero keys, sources, adoptions and artifacts when the store was built (synthetic fixtures only, under `catalog/fixtures/`); since 2026-10-04 it holds the one pilot terrain tile (`docs/assets/pilot_terrain_key.md`). Nothing activates at runtime.
- The drawing server may import from the store only `intake`, `readmodel` and the shared leaves; the human-gated and tracked-catalog layers are unreachable from it (boundary test).
- Real-Aseprite tests run locally only; CI sees the unit and stdio tests that need no Aseprite (`U-14` open).
- Plan packages gain dated status notes; open items there (`U-02`, `U-05`, `U-07`..`U-14`, `AM1-W01` ...) are unchanged.
