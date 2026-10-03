---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-02
tags: [architecture, mcp, documentation, rendering]
---

# Visual asset store contract (partly built)

**Status: the typed records, identities and the semantic registry loader are built; every store writer is still
designed only.** `visual_assets/store/` and `visual_assets/catalog/` were created as skeletons by
`TCK-20261002-VISUAL-ASSETS-FOUNDATION-INIT`; `TCK-20261002-VISUAL-ASSETS-STORE-CONTRACTS` added the pure contract layer.
This page records what the store is meant to guarantee so later tickets build to one contract. Each section is marked
**designed** or **built**.

Source of truth for vocabulary and gates: `docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md`
(sections 6-9) and `docs/plans/visual-asset-management-runtime-integration/`. Physical layout, layering rules and the
command table: `docs/plans/visual-asset-foundation/README.md`. Build order: `agent-working/tickets/todos/visual-asset-foundation/SEQUENCE.md`.

## Lifecycle and gates (designed)

```
candidate --(human review)--> adoption approved --> adopted source --> validated build
   --> release candidate --(compatibility validation, human activation)--> active release
```

No tool may collapse a gate. An agent can draw and hand off a candidate; only a human-run command can adopt it;
nothing in this foundation activates anything at runtime (`AM-M5`-`M7` are out of scope).

## Three places, three writers

| What | Where | Who may write | State |
|---|---|---|---|
| Experiment workspace (every drawing revision) | `~/.cache/rpg-aseprite-mcp/` | the drawing tools | built |
| Intake quarantine | `visual_assets/catalog/.quarantine/` (gitignored) | the store's intake step only | **built** (store side); holds the staged files and the `IntakeResult` until adoption |
| Local review area | `visual_assets/catalog/.review/` (gitignored) | `review` only | **built** |
| Managed store | `visual_assets/catalog/` | the store's human-gated commands only | layout built (empty); commands designed |

## What is built now

- `visual_assets/store/` with `errors`, `config`, `identities`, `contracts/` and `catalog/registry.py` (read-only), and `visual_assets/catalog/`
  (README, `STORE_FORMAT` = version 1, the zero-key `definitions/visual_keys.yaml`, synthetic `fixtures/contracts/`, other directories empty).
- Typed records (`extra="forbid"`, frozen, strict, `record_type` + `schema_version`, no free-form field): `CandidateHandoffPackage`,
  `IntakeResult`, `AdoptionRecord`, `RevocationRecord`, `SourceRecord`, `ArtifactRecord`, `ReleaseCandidateManifest`,
  `VisualKeyRegistry`. Canonical JSON (`canonical_json`) and strict parsing (`parse_record`: oversize, UTF-8, duplicate keys, NaN,
  unknown fields, wrong type, unsupported version each rejected with a stable `ContractError.code`).
- Identities with no normalisation: `VisualKey`, eight opaque id types, `SourceRevision`, `FileHash` (`sha256:`), `PixelHash`
  (`pixels-v1:`; the algorithm is child 5), `UtcTimestamp`.
- Registry loader: duplicate YAML keys, anchors, alias problems and the reserved `fixture.*` namespace are rejected; nothing registers dynamically.
- Adoption and revocation (**human-gated**, `python -m visual_assets.store adopt|revoke`; the first writers of the tracked catalog): `adopt` takes the licence state and its
  evidence ONLY from the human's own arguments (never from the package, whose licence statement is only a claim), refuses an Evidence marker as evidence and anything but
  `CLEARED`, requires an explicit `--source-asset-id` and exactly one of `--new` or `--parent rNNNN` (the latest unrevoked revision), checks the visual key against the
  registry, and refuses, each with its own code and before writing anything: an unknown, failed, revoked or already-adopted intake, changed staged bytes, an oversize source
  (ADR D2), a revoked or closed lineage. It prints the preview warning and what is being decided, then makes the operator type the id. The four files (source bytes, intake
  copy, adoption record, SourceRecord) are published all together or not at all, the SourceRecord last. `revoke` never deletes: a source revision gets a tracked revocation
  record, an un-adopted intake a local one; `is_build_eligible` fails closed. A revoked revision does not freeze its asset: the next revision continues the numbering and takes the
  latest UNREVOKED revision as its parent; an asset whose every revision is revoked is closed.
- `audit_chain` rebuilds intake result -> adoption record -> SourceRecord -> source bytes from the tree alone using the hashes the records carry (`AdoptionRecord.intake_hash`,
  `SourceRecord.adoption_hash`) and reports every break by code; leftover `.tmp-*` directories are notes.
- **`pixels-v1` (decision D4), the identity of an artifact.** `sha256` over `b"pixels-v1\0"`, then width and height as unsigned 32-bit big-endian integers, then the image as
  8-bit NON-premultiplied RGBA rows from top to bottom, where every pixel with alpha 0 is written as `00 00 00 00`; the string is `pixels-v1:` + hex. Two PNGs with the same visible
  pixels have the same hash whatever their filter choice, compression level, colour type or ancillary chunks, and whatever RGB sits under a transparent pixel. The reader that
  computes it (`store/pixels.py`, stdlib only, no I/O) accepts only non-interlaced 8-bit greyscale, greyscale+alpha, RGB, RGBA and indexed (with `tRNS`) PNGs, checks every chunk CRC,
  bounds the dimensions and the decompressed size before inflating, and refuses 16-bit, interlaced, APNG, colour-key `tRNS`, unknown critical chunks, truncated or surplus data and
  anything after `IEND`. Intake uses the same reader to fully validate the producer's preview.
- **The store's own render of the source.** `review` renders the staged source itself (sandboxed Aseprite, frame 1, all visible layers) at the preview's scale, compares decoded
  pixels with the producer's preview, writes a typed `ReviewRenderCheck` into the candidate's quarantine directory and shows `store_render.png` plus a prominent mismatch warning in the
  review area. Without Aseprite it says plainly that the preview is producer-supplied and unverified and records nothing. `adopt` never trusts that stored file (any local process can write
  the gitignored quarantine): it re-renders at adoption time, refuses `preview_mismatch`, `review_render_missing`, `review_render_stale` or `renderer_unavailable`, then copies the check into the
  tracked provenance and binds its hash in the `AdoptionRecord`; `audit_chain` covers it.
- **Build, release candidate, verify, gc.** `build` exports the latest build-eligible revision of each adopted source (fixed allowlisted command through the shared sandbox, rules pinned in
  `build-config/export.toml`, one scale class `x1`) to `generated/<source_asset_id>--x1/<pixel hash hex>.png` plus `<hex>.<revision>.artifact.json` (the PNG is named by its pixels and shared by
  revisions that render identically; each revision has its own record). Building twice gives the same hash and one file; a render that is not reproducible is refused. `ArtifactRecord` carries the hash
  of the exact `SourceRecord` bytes it was built from, so a release manifest anchors the whole chain intake -> adoption -> source record -> artifact. The build fingerprint's "Lua pin hash" is the pin of the
  template mounted in the sandbox; plain PNG export does not run Lua. `assemble_release` writes `manifests/candidates/<catalog_id>/rc-NNNN.json` (ordered ids, exclusive create, never overwritten, no active pointer:
  D6) from the registry and the current artifacts; eligibility is decided by `is_build_eligible` alone, and a registry key with no artifact is refused unless marked `optional`. `verify` (pure Python, run
  on the committed catalog in CI) rebuilds the chain, re-hashes every artifact and checks every record against its bytes and name, follows every manifest entry, and flags anything unexpected;
  an artifact of a revoked revision is visible non-blocking history, a manifest entry for one is a blocking finding. `gc` lists, and only with `--delete` removes, quarantine directories with no
  adoption and no pending review, review exports of adopted/revoked/gone intakes and unreferenced PNGs; deleting a locally revoked intake also deletes its local revocation record; it never touches
  `sources/`, `provenance/` or `manifests/`.
- Handoff builder (drawing side): `export_handoff` writes a candidate directory inside the experiment workspace (see `docs/assets/drawing_tools.md`); it never writes the store.
- Intake (store side; `python -m visual_assets.store intake|review|list|show`): the package directory is opened without following symlinks and read
  into memory first (refused before any byte is copied, leaving no quarantine directory, for a symlink, extra file or sub-directory, oversize file,
  FIFO or hard-linked file; these are `StageError`s, not findings). The independent validator then judges the bytes with one policy for every
  producer class and records an immutable `IntakeResult` **inside the quarantine directory** (`in-` + 16 hex of a hash over the package, source and preview file hashes, so
  different bytes are a different intake). Staging is atomic: the files are written to a `.tmp-*` sibling and renamed, so a killed process leaves only an ignored,
  deletable temporary directory. Re-submitting identical files returns the existing result and writes nothing.
  `review` re-verifies the staged hashes and exports the preview plus a text summary of a PASSED intake to `.review/`. No intake step adopts anything.
- `tests/visual_assets/test_boundaries.py`: `drawing` has no write path into `catalog/` (it may not even reference the path),
  `store` does not import `drawing`, nothing imports `src/` and `src/` never imports `visual_assets`.

## What is designed, not built

| Piece | Designed behaviour | Child ticket |
|---|---|---|
| Intake | bounded copy into quarantine, claims checked against staged bytes (hashes, format, bounds, symlinks, traversal, licence state), immutable `IntakeResult` | 3 |
| MCP store tools | read-only `store_list` / `store_show` and `submit_candidate`; never adopt, build, release, revoke or gc | 6 |

## Known gaps (stated, not hidden)

- **The human gate does not authenticate the person.** The terminal check and the typed id stop accidental and scripted adoption; the approver name and role are recorded, not proven.
- **The catalog alone cannot catch a consistent forgery.** Someone who edits an adoption record and the hash in its SourceRecord together still passes `audit_chain`; git history is the
  backstop. (Ticket 5 binds artifacts to the SourceRecord bytes, so a release manifest anchors the whole chain.)
- **A local intake revocation is local.** Revoking an un-adopted intake writes only into this machine's gitignored quarantine, so it covers other intakes of the same bytes
  on this machine only; another checkout does not see it. A revoked SOURCE REVISION is tracked and covers its bytes everywhere: `adopt` refuses the same bytes through any
  other intake (`source_bytes_revoked`) and refuses identical bytes already live under any asset (`duplicate_source`).
- **Agents never run `adopt` or `revoke`.** They are absent from the MCP server and a boundary test forbids the drawing code from importing them.
- **The preview is proven only where Aseprite is available.** Intake alone cannot prove a preview depicts its source, so adoption requires the store's own render (see above) and therefore refuses on a machine
  without Aseprite and bwrap. The comparison is by decoded pixels at the preview's scale, so it is exact for what the sandboxed Aseprite renders; it is not a statement about artistic intent.
- **One visual key maps to one artifact** (the single `x1` scale class): a key cannot carry two variants. A release candidate lists one artifact per key. A second asset cannot take a key a live asset holds (`visual_key_taken`);
  replacing an asset under the same key means revoking the old asset's revisions first.
- Animation metadata beyond `frame_count` and `tag_count` (per-frame durations, tag ranges, loop modes) is not part of the handoff package or checked by intake
  (proposal 9.6 lists "animation metadata"; ticket 3 adds only the producer state).
- **Palette size is unverifiable for an all-opaque-black stored palette.** Aseprite 1.3.18.6 rebuilds such a palette from the image when it loads a file
  (size = 1 + distinct opaque colours), which needs pixel decoding. Intake quarantines it with `PALETTE_UNVERIFIABLE`. Only a never-edited first revision
  carries one; any edit re-saves a palette with real entries. Every other palette is checked exactly against what Aseprite reports.
- Intake accepts only 32-bit RGBA sources (`SOURCE_UNSUPPORTED_COLOR_DEPTH` otherwise); the package carries no colour-depth claim, so it is a support policy, not a claim check.
- The unsupported-feature list (`unsupported:tilemap`, `...indexed_color`, `...grayscale`, `...linked_cels`, `...external_reference`) and the preview/file size bounds are provisional (`U-05`).

## Decisions still open

D2 (sources committed directly, no Git LFS), D3 (only adopted assets' PNGs committed; verified in CI by pixel hash) and D4
(artifact identity is the decoded-pixel hash) are **decided** (`docs/architecture/visual_asset_foundation_adr.md`). Still open: deployment profile (`AM1-W01`), signing/trust channel (`AM1-W08`),
retention numbers, the Aseprite licence review (`U-02`), numeric budgets (`U-05`) and CI with Aseprite (`U-14`).
