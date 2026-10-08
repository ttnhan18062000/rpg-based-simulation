---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-02
tags: [architecture, mcp, documentation, rendering]
---

# Visual asset store contract (built)

**Status: built (`TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION`, children 1-6).** The drawing tools hand off a candidate, the store
stages it into a quarantine, judges it independently, lets a human adopt it as an immutable source revision, exports pixel-hashed artifacts
and assembles release CANDIDATES, and checks the whole store in pure Python. Nothing activates anything at runtime (`AM-M5`-`M7` are out of
scope). The committed `visual_assets/catalog/` holds one real key, `terrain.forest` (the `AM-M6` pilot tile, `docs/assets/pilot_terrain_key.md`), with its three adopted slot sources, adoptions, artifacts and the release candidates (`pilot/rc-0001` to `rc-0004`), plus the owner's adoption of draft set `terrain-v1` on 2026-10-05T18:17:03Z (`sa-f4c541f25f112221`): 31 more sources, 22 terrain tiles and 9 `border.*` masks. **No release candidate or runtime export covers those 31 slots yet** (`rc-0004` holds the forest only; no `build` has produced artifacts for them); everything else is layout, rules and synthetic fixtures. The owner then adopted the icon key set, `icons-key-v1` (2026-10-06T15:21:47Z, set adoption `sa-b4bb738d6b5526f0`, draft set hash `sha256:29854e8b32bcd9701f5e717a2e01dce5934cc04af63d4c6e3bc156c78ce5cbbd`): 14 more sources (`icon_*`, one per `icon.*` key, each `optional`). **No release candidate covers those 14 slots** (`pilot/rc-0007` holds 34) and no `build` has covered them; the catalog holds 48 sources and two set adoptions. The registry also holds 22 more `icon.*` keys of icon set v2 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`; 5 map locations, 5 buildings, 3 classes, 3 rarity badges, 6 item families, each `optional`, axis-free, with its size, class and fallback in the description): registered, not drawn, not adopted, in no release candidate.
This page says what each command and MCP tool does, who may run it and what it writes.

Source of truth for vocabulary and gates: `docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md`
(sections 6-9) and `docs/plans/visual-asset-management-runtime-integration/`. What each `AM1-W01`..`W13` acceptance clause has, as built: `docs/assets/m1_contract_register.md`. Physical layout, layering rules and the
command table: `docs/plans/visual-asset-foundation/README.md`. Build order: `agent-working/tickets/todos/visual-asset-foundation/SEQUENCE.md`.

## Lifecycle and gates

```
candidate --(human review)--> adoption approved --> adopted source --> validated build
   --> release candidate --(compatibility validation, human activation)--> active release
```

No tool may collapse a gate. An agent can draw, hand off a candidate, submit it for intake and read the store; only a human-run command can adopt or revoke;
release candidates are assembled but never activated (the last arrow is out of scope: there is no active pointer, D6).

## Three places, three writers

| What | Where | Who may write | State |
|---|---|---|---|
| Experiment workspace (every drawing revision) | `~/.cache/rpg-aseprite-mcp/` | the drawing tools | built |
| Intake quarantine | `visual_assets/catalog/.quarantine/` (gitignored) | the store's intake step only | **built** (store side); holds the staged files and the `IntakeResult` until adoption |
| Local review area | `visual_assets/catalog/.review/` (gitignored) | `review` only | **built** |
| Managed store | `visual_assets/catalog/` | the store's commands only: `adopt`, `revoke` (human-gated), `build`, `release` | **built**; only adopted assets and their derived files are tracked |

## What is built now

- `visual_assets/store/` with `errors`, `config`, `identities`, `contracts/` and `catalog/registry.py` (read-only), and `visual_assets/catalog/`
  (README, `STORE_FORMAT` = version 1, the `definitions/visual_keys.yaml` (one real key, `terrain.forest`), synthetic `fixtures/contracts/`, other directories empty).
- Typed records (`extra="forbid"`, frozen, strict, `record_type` + `schema_version`, no free-form field): `CandidateHandoffPackage`,
  `IntakeResult`, `AdoptionRecord`, `RevocationRecord`, `SourceRecord`, `ArtifactRecord`, `ReleaseCandidateManifest`,
  `VisualKeyRegistry`. Canonical JSON (`canonical_json`) and strict parsing (`parse_record`: oversize, UTF-8, duplicate keys, NaN,
  unknown fields, wrong type, unsupported version each rejected with a stable `ContractError.code`).
- Identities with no normalisation: `VisualKey`, eight opaque id types, `SourceRevision`, `FileHash` (`sha256:`), `PixelHash`
  (`pixels-v1:`, defined below), `UtcTimestamp`.
- Registry loader: duplicate YAML keys, anchors, alias problems and the reserved `fixture.*` namespace are rejected; nothing registers dynamically.
- Adoption and revocation (**human-gated**, `python -m visual_assets.store adopt|revoke`; the first writers of the tracked catalog): `adopt` takes the licence state and its
  evidence ONLY from the human's own arguments (never from the package, whose licence statement is only a claim), refuses an Evidence marker as evidence and anything but
  `CLEARED`, requires an explicit `--source-asset-id` and exactly one of `--new` or `--parent rNNNN` (the latest unrevoked revision), checks the visual key against the
  registry, and refuses, each with its own code and before writing anything: an unknown, failed, revoked or already-adopted intake, changed staged bytes, an oversize source
  (ADR D2), a revoked or closed lineage. It prints the preview warning and what is being decided, then makes the operator type the id. The five files (source bytes, intake
  copy, render check copy, adoption record, SourceRecord) are published all together or not at all, the SourceRecord last. `revoke` never deletes: a source revision gets a tracked revocation
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
  tracked provenance and binds its hash in the `AdoptionRecord`; `audit_chain` covers it. It also decodes the image file the human actually opened
  (`store_render.png` in the gitignored review area, which any local process can rewrite) and refuses `review_image_changed` unless its pixels equal the adoption-time render (`review_render_missing` if it is gone).
  The producer preview is bounded to 1024 px (scale 8 of the largest sprite, the only scale `export_handoff` makes) because PNG unfiltering is a pure-Python per-byte loop.
- **Build, release candidate, verify, gc.** `build` exports the latest build-eligible revision of each adopted source (fixed allowlisted command through the shared sandbox, rules pinned in
  `build-config/export.toml`, one scale class `x1`) to `generated/<source_asset_id>--x1/<pixel hash hex>.png` plus `<hex>.<revision>.artifact.json` (the PNG is named by its pixels and shared by
  revisions that render identically; each revision has its own record). Building twice gives the same hash and one file; a render that is not reproducible is refused. `ArtifactRecord` carries the hash
  of the exact `SourceRecord` bytes it was built from, so a release manifest anchors the whole chain intake -> adoption -> source record -> artifact. The build fingerprint's "Lua pin hash" is the pin of the
  template mounted in the sandbox; plain PNG export does not run Lua. `assemble_release` writes `manifests/candidates/<catalog_id>/rc-NNNN.json` (ordered ids, exclusive create, never overwritten, no active pointer:
  D6) from the registry and the current artifacts; eligibility is decided by `is_build_eligible` alone, and a registry key with no artifact is refused unless marked `optional`. `verify` (pure Python, run
  on the committed catalog in CI) rebuilds the chain, re-hashes every artifact and checks every record against its bytes and name, follows every manifest entry, and flags anything unexpected;
  an artifact of a revoked revision is visible non-blocking history, a manifest entry for one is a blocking finding. `gc` lists, and only with `--delete` removes, quarantine directories with no
  adoption and no pending review, review exports of adopted/revoked/gone/expired intakes, unreferenced PNGs and, as retention, a PASSED never-adopted intake older than `MAX_UNADOPTED_INTAKE_AGE_DAYS` (30, approved 2026-10-04; counted from the intake's own timestamp, strictly older); deleting a locally revoked intake also deletes its local revocation record; it never touches
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

## The runtime manifest and `export-runtime`

Under Profile A (ADR D8) the frontend build consumes the assets of one release candidate. The candidate manifest is an internal record; what ships is the smaller
`RuntimeManifest` (`contracts/runtime.py`, proposal 9.3): `catalog_id`, `release_id`, `candidate_manifest_hash` (the `sha256:` file hash of the exact candidate
manifest bytes it was exported from), `registry_hash`, `fallback_contract_version` (1) and `entries`, each `visual_key`, `family` (from the registry), `pixel_hash`,
`file`, `width`, `height`, and `detail` (the slot's detail value, present exactly for a key listed in `details`). `details` (omitted when empty) holds one `{visual_key, values, default}` per key that declares a detail
axis and has an entry, copied from the registry and sorted by key (at most `MAX_DETAIL_KEYS`): the client picks over these DECLARED values, so adding art for a declared value never reshuffles the map.
`file` is exactly `<64 hex>.png`, derived from the pixel hash and never a path; entries are unique per slot and sorted by `(key, detail)`, at most `MAX_VISUAL_KEYS`;
the record's size bound is `MAX_MANIFEST_BYTES`. It **excludes** everything protected: approver, licence record, source path or revision, review note, intake, artifact id.
Same strictness as every record (unknown fields, wrong versions, oversize dimensions rejected).

**Client detail pick (contract version 1, `frontend/src/visualAssets/pickDetail.ts`).** For a key listed in `details`, the client shows one DECLARED value per Live Map cell:
`index = fnv1a32(utf8("<key>|<x>|<y>|<seed>")) mod values.length`, with x, y and seed base-10 integers (a negative keeps its `-`), over the declared `values` in their declared order, and
the fixed `DETAIL_SEED` (1; per-world seeds would be a later decision). FNV-1a is the 32-bit variant (offset basis `0x811c9dc5`, prime `0x01000193`, wrapping multiply). It is pure: no `Math.random`, no clock, no
state, nothing from the simulation, so the same map always looks the same. Changing the hash, the string, the value order or the seed changes every map and is a contract change (bump `PICK_CONTRACT_VERSION`).
`resolveVisual(snapshot, key, context, cell?)` then resolves, in order: the picked value's image, the default value's image (result `detail` = the shown value, `picked` = the pick, `detailFallback` = why they differ), the
role fallback (a typed fallback result carrying `picked`; the caller draws its flat fill). Without a cell the default is used; a key without an axis ignores the cell. Weighted picks, per-world seeds and neighbour-aware
(autotile) picks are out of scope. Golden vectors and a 64 x 64 spread are in `__tests__/pickDetail.test.ts`.

`python -m visual_assets.store export-runtime --catalog-id C --release-id rc-NNNN --out DIR` (library: `runtime_export.export_runtime`) runs `verify` first, reads the
candidate strictly, re-decodes every artifact PNG and checks its pixel hash, and writes `runtime_manifest.json` (canonical JSON) plus the PNGs named by their pixel hash into
`DIR`, staged in a `.tmp-*` sibling and renamed, so the result is all-or-nothing and byte-identical for the same release. It never writes into the catalog and has no MCP tool
(the drawing server may not import it). Refusals, each leaving no output and the catalog unchanged (exit code 2): `verify_failed`, `unknown_release`, `registry_mismatch` (the registry
changed since the candidate was assembled), `artifact_mismatch`, `out_exists` (also a symlink, and an output that appears while exporting), `out_inside_catalog`,
`out_parent_missing`, `invalid_catalog_id`, `invalid_release_id`, `registry_invalid`, `catalog_unreadable`. A committed synthetic export (three `fixture.rehearsal.*` images in
different shapes) lives at `frontend/src/visualAssets/__fixtures__/rehearsal/`; `python -m tests.visual_assets.store.runtime_fixture --write` (run from the repo root, module form) refreshes it and a test checks it equals a fresh
regeneration. Wiring the export into the real frontend build is `AM-M6` (dormant).

## Commands (`python -m visual_assets.store <command>`)

| Command | Gate | Writes | Tracked |
|---|---|---|---|
| `intake` | none (agent or human) | the staged files and `IntakeResult` in `.quarantine/<intake_id>/` | no (gitignored) |
| `review` | none | `.review/<intake_id>/` (producer preview, the store's own `store_render.png`, `summary.txt`) and, with a renderer, `review_render.json` in the quarantine | no (gitignored) |
| `list` | none | nothing | n/a |
| `show` | none | nothing | n/a |
| `audit` | none | nothing | n/a |
| `verify` | none | nothing | n/a |
| `build` | none; needs Aseprite and bwrap | `generated/<source_asset_id>--x1/<pixel hash>.png` and `<hash>.<revision>.artifact.json` | yes |
| `release` | none | `manifests/candidates/<catalog_id>/rc-NNNN.json` (a CANDIDATE, never active) | yes |
| `export-runtime` | none (reads committed candidates; writes outside the catalog) | a NEW directory given by `--out`: `runtime_manifest.json` and `<64 hex>.png` files (all-or-nothing, never into the catalog) | n/a |
| `gc` | none; deletes only with `--delete` | removes only what it lists, under the quarantine, the review area and `generated/` | no (never `sources/`, `provenance/`, `manifests/`) |
| `adopt` | **human only**: terminal on stdin and the typed id | `sources/<id>/rNNNN.aseprite` + `.source.json`, `provenance/adoptions/`, `provenance/intake/<in>.json` and `.review.json` | yes |
| `draft` | `keep`: none (an agent may run it; it records no approval and is not an MCP tool). `verify`: none (read-only) | `visual_assets/drafts/<set_id>/` (outside the catalog): `draft_set.json` and one folder per entry (`package.json`, `source.aseprite`, `preview.png`, `intake_result.json`) | yes (drafts are tracked, never released) |
| `adopt-set` | **human only**: terminal on stdin and the typed set id | per entry what `adopt` writes (`sources/`, `provenance/adoptions/`, `provenance/intake/<in>.json` and `.review.json`) plus `provenance/set-adoptions/<sa-id>.json` | yes |
| `revoke` | **human only**: terminal on stdin and the typed id | `provenance/revocations/<id>.json` for a source revision; `revocation.json` in the quarantine for an un-adopted intake | revision: yes; intake: no |

## Draft sets and `adopt-set`

The user decided (2026-10-04, "Drafts now, batch review") that assets are drafted without adoption and reviewed as a whole set, then approved in one decision. Adoption stays the human gate (`AM-F01`); its unit becomes
a reviewed set. A **draft set** is `visual_assets/drafts/<set_id>/`, tracked in git and OUTSIDE the catalog: `build`, `release`, `export-runtime` and the catalog's `verify` never read it, and `gc` never touches it (its 30-day
rule is for local quarantine and review files, which drafts do not depend on). `draft_set.json` is a `DraftSet` (`contracts/draft.py`): entries `{visual_key, detail?, source_asset_id, draft_id, pixel_hash, intake_hash}`,
unique per slot, sorted, at most `MAX_DRAFT_SET_ENTRIES` (256; no limit on the number of sets). `draft_id` is the intake id and the entry's folder, which holds the three staged files and the intake result of a PASSED intake.
`pixel_hash` is the pixels-v1 hash of the preview, the image the human reviews. The source's hash is deliberately not repeated: it is bound through the chain (below), which keeps a full set under `MAX_RECORD_BYTES`.

- `draft keep <intake_id> --set <set_id> --as <visual_key> [--detail <value>] [--source-asset-id <id>] [--replace]`: only from a PASSED, locally unrevoked intake, with a declared key and value. `source_asset_id` is the id the entry will be adopted under (default: the key with dots as
  underscores plus `_<detail>`); it is refused if it already exists as a source asset in the catalog or is used by another entry of the set, so a collision shows when the draft is kept, not at adoption. A second draft for the same slot
  (the key's default counts as its default value) is refused unless `--replace`. All-or-nothing writes (a staged `.tmp-*` directory renamed into place). Errors have stable codes (`DraftError`).
- `draft verify [set_id]`: the full chain for every entry, declared keys and values, one entry per effective slot, no stray or leftover files. **The chain**, checked identically by `draft verify` and `adopt-set` (`drafts.read_entry`):
  `source.aseprite` bytes -> the staged-file hash inside `intake_result.json`; `intake_result.json` bytes -> `intake_hash`; `preview.png` pixels -> `pixel_hash`.
- `adopt-set <set_id> --approver ... --approver-role ... --licence CLEARED --licence-evidence ... --review-evidence ...` (`setadoption.py`): **human only** (terminal on stdin, one typed confirmation of the set id; the drawing server may not import it, and it is not an MCP tool).
  For every entry it runs the checks `adopt` runs (shared code: staged bytes, the same bytes not adopted or revoked, key and slot declared and free, licence, approver; entries are always NEW source assets, so a held slot is refused and replacing means revoking first) and, instead of the
  per-intake review area, **re-renders the draft's source with the store's own Aseprite now and requires the render to equal the draft's preview pixel for pixel** (a hard refusal on any mismatch: no stored check is trusted). It prints ONE notice listing every entry, the licence evidence,
  the review evidence and the **DraftSet's file hash** (the preview page shows the same hash, so "what I reviewed" and "what I adopted" are the same bytes), then writes all files together or none: per entry the source, the intake result copy, a fresh `ReviewRenderCheck`, an ordinary `AdoptionRecord` (schema unchanged)
  and a `SourceRecord`, then one `SetAdoptionRecord` in `provenance/set-adoptions/` (a folder of its own, because every reader parses `provenance/adoptions/*.json` as an `AdoptionRecord`). The catalog's `verify` checks each set record and that every entry points at an adoption of the same intake, key and slot.
  A set adoption does not change the meaning of an adoption record, a release or the runtime manifest.
- `draft export <set_id> <out_dir>` (`draftexport.py`, read-only on the drafts and the catalog; writes a NEW directory outside both, all-or-nothing, deterministic) verifies the set first (the chain, declared keys, no revoked intake: any finding refuses) and writes `draft_preview_manifest.json`
  (`DraftPreviewManifest`, record type `draft_preview_manifest`, bound `MAX_MANIFEST_BYTES`) plus each entry's `preview.png` byte for byte, named by its pixel hash. The manifest has the runtime manifest's entry and `details` shape plus `set_id`, `draft_set_hash` (the file hash of the exact `draft_set.json`
  bytes: the value `adopt-set` prints), `registry_hash`, and per entry `source_asset_id`, `draft_id` and `scale` (a whole number dividing the preview size; the page draws the preview at 1/`scale` with smoothing off). A live ADOPTED slot the set does not hold (for example the adopted forest tiles in `terrain-v1`) is added as a labelled **reference** entry (`adopted: true`, only ever the literal `true`, built from the catalog's 16 x 16 artifact at `scale` 1,
  never copied into the drafts); a draft for the slot always wins, and a reference exists only in this export, never in a `DraftSet`, so `draft verify` and `adopt-set` never see one. The page labels it "adopted (reference)". It is **never parseable as a runtime manifest and a runtime manifest never as it** (record type, required set fields, strict
  unknown-field rejection; tested in Python and in the client). The isolated page that shows it is documented in `docs/assets/drawing_tools.md`.
- Layering (`tests/visual_assets/test_boundaries.py`): `drafts` is a store layer of its own (it writes outside the catalog and records no approval, so it is not a gate layer, but the drawing server may not import it); `setadoption` is a gate layer like `adoption` and `revoke`, never importable from `visual_assets/drawing/`, and the CLI is the only caller.

### Non-terrain families in a draft set: border masks (D19)

A draft set accepts any registered key: `Family` is a free `[a-z][a-z0-9_]{0,31}` string and `draft keep` checks only that the key and detail value are declared. The `border.*` keys (`border.edge`,
`border.outer_corner`, `border.inner_corner`, each optional with a detail axis `v1`-`v3`) therefore live in `terrain-v1` beside the tiles, and one `adopt-set` covers both. A mask is a 16x16 image whose alpha channel is a
1-bit shape, authored for one orientation (`edge`: north, rows 0-3; `outer_corner`: north-east; `inner_corner`: north plus east) and rotated by the client in 90-degree steps; rotation is client-side and the store records
no orientation. The store does not check shape, depth or orientation: the 4 px cap is enforced by the client compositor and checked on every committed mask by a test. See `docs/assets/pilot_terrain_m5_criteria.md` (AM5-B).

The `icon.*` family (14 optional keys, D20, `TCK-20261006-VISUAL-ASSETS-ICON-KEY-FAMILIES`) is the icon key set: `icon.plate.location` and `icon.marker.enemy_camp` (16x16), `icon.building.blacksmith` and `icon.class.warrior` (24x24), `icon.tier.e` to `icon.tier.sss` (eight 8x8 badges) and `icon.status.frame_buff` and `icon.status.frame_debuff` (16x16). Every key has `variant_axes: []` (D17: tier and marker state are separate keys) and no detail axis, and its description states its size, scale x1, fallback-safety class and fallback. Registering them moved `registry_hash`, so `pilot/rc-0006` was assembled (same 34 slots as `rc-0005`; `docs/assets/pilot_terrain_key.md`). No icon has art yet.

## MCP tools on the drawing server (restart the server for new tools to appear in a running session)

| Tool | What it does | Writes |
|---|---|---|
| `export_handoff` | packages one exact revision as a handoff directory in the experiment workspace | the experiment workspace only |
| `submit_candidate` | runs intake on a handoff written by `export_handoff`, found only by its `handoff_id` (never a path, never a bare candidate id) | the quarantine only |
| `store_list` | bounded listing of intakes, sources, artifacts or release candidates | nothing |
| `store_show` | one record as a shaped summary (producer statements labelled as claims); no raw files, no absolute paths | nothing |

**Which checkout the server serves.** The store the server reads and writes is the checkout its code lives in (`visual_assets/start_mcp.sh` runs from the checkout that holds it), so a Claude session started in the main checkout wrote intakes into the MAIN checkout's quarantine even while the work was in a worktree. `VISUAL_ASSETS_CHECKOUT=<absolute path of a git checkout or worktree>` (set before starting Claude Code; `.mcp.json` passes it through, empty means unset) names another checkout explicitly; a value that is relative, missing, not a git checkout or without `visual_assets/catalog/STORE_FORMAT` stops the server with a reason (`StoreRootError`) instead of falling back. The root is printed to stderr at startup and every `submit_candidate`, `store_list` and `store_show` result carries `store_root` (checkout name, branch, `linked_worktree`, `source`: `module` or `env`; never an absolute path), so a wrong root is visible. The handoff workspace (`ASEPRITE_MCP_WORKSPACE`, default `~/.cache/rpg-aseprite-mcp`) is shared by every checkout and unchanged. `docs/assets/drawing_tools.md` has the how-to.

There is no MCP tool that adopts, revokes, builds, releases, deletes or activates, and the boundary test lets the drawing server import only the store layers
`intake`, `readmodel`, `contracts`, `identities`, `errors` and `config`.

## Not built (outside this foundation's scope)

Runtime activation, a resolver in the real client, Live Map and HUD consumption, client compatibility ranges (register `W03.5`, `W07`), more than one scale class, atlases and animation export
(`AM-M6`/`M7`; signing was decided against, ADR D9). Built since: the runtime manifest and `export-runtime` (above) and an **isolated** `AM-M5` surface rehearsal on synthetic fixtures in
`frontend/src/visualAssets/` (a strict parser, resolver, typed fallbacks and single-generation loader that nothing in the normal app imports); its per-gate result, overall
`INCONCLUSIVE`, is `docs/assets/surface_rehearsal_result.md`; the pilot terrain tile's gap results (reviewer criteria, colour-vision check, client matrix) are in `docs/assets/pilot_terrain_m5_results.md`. Open decisions are listed at the end of this page.

## Known gaps (stated, not hidden)

- **The human gate does not authenticate the person.** The terminal check and the typed id stop accidental and scripted adoption; the approver name and role are recorded, not proven.
- **Approver and audit are one person (accepted limit, `ADR D13`, 2026-10-04).** The owner holds the approver role and also runs the audit; separation is not achieved and is an accepted, stated limit of a one-person project. There is no store lock by rule (`ADR D18`): one store command at a time, a single-operator rule that the code does not enforce.
- **The catalog alone cannot catch a consistent forgery.** Someone who edits an adoption record and the hash in its SourceRecord together still passes `audit_chain`; git history is the
  backstop. (Ticket 5 binds artifacts to the SourceRecord bytes, so a release manifest anchors the whole chain.)
- **A local intake revocation is local.** Revoking an un-adopted intake writes only into this machine's gitignored quarantine, so it covers other intakes of the same bytes
  on this machine only; another checkout does not see it. A revoked SOURCE REVISION is tracked and covers its bytes everywhere: `adopt` refuses the same bytes through any
  other intake (`source_bytes_revoked`) and refuses identical bytes already live under any asset (`duplicate_source`).
- **`gc` never deletes a tracked object or record.** Retention is limited to the local quarantine and review dirs (and unreferenced untracked-style PNGs). A dry run also prints a report line, "kept: tracked history, never deleted", for each artifact record no committed release candidate refers to (`gc.tracked_unreferenced`). Retained releases are derived (every committed candidate under `manifests/candidates`), not declared; which frontend builds may still be in use is a deployment fact for the `AM-M6` charter, not store state. **If `gc` ever gains a deletion kind for tracked objects, a typed roots record (which releases, builds and evidence to keep) must exist first, in its own ticket.** `AM-C09` is judged as "`gc` removes no protected object", protected = all tracked state + young PASSED intakes + referenced review evidence (`docs/assets/retention_and_rollback.md`).
- **Agents never run `adopt` or `revoke`.** They are absent from the MCP server and a boundary test forbids the drawing code from importing them.
- **The preview is proven only where Aseprite is available.** Intake alone cannot prove a preview depicts its source, so adoption requires the store's own render (see above) and therefore refuses on a machine
  without Aseprite and bwrap. The comparison is by decoded pixels at the preview's scale, so it is exact for what the sandboxed Aseprite renders; it is not a statement about artistic intent.
- **One SLOT maps to one artifact** (the single `x1` scale class). A slot is a visual key, plus a detail value when the key declares a **detail axis** (`detail: {values, default}` on the
  registry key; at most `MAX_DETAIL_VALUES` values, at most `MAX_DETAIL_KEYS` keys per registry; a key without an axis is the single slot `(key, none)`). An adoption names its slot with `adopt --detail <value>`
  (`AdoptionRecord.detail_value`; omitted/`None` = the key's declared default, so an adoption made before the axis existed fills the default slot unchanged). A release candidate lists one artifact per slot,
  sorted by `(key, detail)`; a key that is not optional needs its default slot's artifact and every other declared value needs no art until someone adopts it (the client falls back to the default), but an adopted slot without a built artifact is refused at release (`key_without_artifact`, run `build`) unless the key is optional. A second asset cannot take a slot a live
  asset holds (`visual_key_taken`); replacing an asset in a slot means revoking the old asset's revisions first. Refusals: `detail_not_declared` (a value on a key with no axis), `unknown_detail_value`; at release,
  `undeclared_detail` (the registry no longer declares an adopted value). Total entries across all slots stay at most `MAX_VISUAL_KEYS`. The default is the only declared meaning of "no value": changing a key's
  `default` re-binds every adoption that names none, and the release lists the explicit value on each entry. This replaced the earlier limit "one visual key maps to one artifact"
  (ADR D11); no schema version changed: every new field has a default and is omitted from the bytes when absent, and a strict client rejects the new fields.
- Animation metadata beyond `frame_count` and `tag_count` (per-frame durations, tag ranges, loop modes) is not part of the handoff package or checked by intake
  (proposal 9.6 lists "animation metadata"; ticket 3 adds only the producer state).
- **Palette size is unverifiable for an all-opaque-black stored palette.** Aseprite 1.3.18.6 rebuilds such a palette from the image when it loads a file
  (size = 1 + distinct opaque colours), which needs pixel decoding. Intake quarantines it with `PALETTE_UNVERIFIABLE`. Only a never-edited first revision
  carries one; any edit re-saves a palette with real entries. Every other palette is checked exactly against what Aseprite reports.
- Intake accepts only 32-bit RGBA sources (`SOURCE_UNSUPPORTED_COLOR_DEPTH` otherwise); the package carries no colour-depth claim, so it is a support policy, not a claim check.
- The unsupported-feature list (`unsupported:tilemap`, `...indexed_color`, `...grayscale`, `...linked_cels`, `...external_reference`) are a support list recorded in `docs/assets/budgets.md`. Every numeric bound (preview, file, record, registry, decode) is a budget there, measured on 2026-10-03, pinned to the code by a test and `APPROVED 2026-10-04` by the owner (PR #309); retention (30 days) was the last row and was approved the same day. Rulings F1-F6 are recorded there. Size bounds are per record type (`StoreRecord.size_bound`, `record_bound(cls)`): the registry and the release manifest have their own bounds, and `tests/visual_assets/store/unit/test_record_bounds.py` proves every record a writer can produce under the contract bounds is readable by every reader. PNG files are bounded by `MAX_PNG_FILE_BYTES`; `MAX_DECODED_BYTES` bounds decoded size only.

## Decisions

D2 (sources committed directly, no Git LFS), D3 (only adopted assets' PNGs committed; verified in CI by pixel hash), D4 (artifact identity is the decoded-pixel hash), D8 (deployment profile A, `AM1-W01`), D9 (no signing,
`AM1-W08`), D10 (real Aseprite on the licence holder's own machine only, which closes the licence review `U-02` and decides against CI with Aseprite, `U-14`), D11 (the detail axis) and D12 (draft sets) are **decided**
(`docs/architecture/visual_asset_foundation_adr.md`). Numeric budgets (`U-05`) and retention (30 days) are approved (`docs/assets/budgets.md`, `docs/assets/retention_and_rollback.md`). What is still open is per
`AM-M1` item in `docs/assets/m1_contract_register.md`, which also records the `AM-M1` result (`BLOCKED`, re-derived 2026-10-04: `AM-M0` is `INCONCLUSIVE`) and what remains: an `AM-M0` `PASS`, the registry class field, the fallback activation check, a `verify` rule for `variant_axes`, and the `AM-M6`-carried clauses. The owner's role, key, retirement, range and retention decisions are `D13`-`D18`.
