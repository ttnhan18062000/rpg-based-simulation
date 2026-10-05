---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [mcp, live-map, documentation]
---

# Pilot terrain key: `terrain.forest`

The one real visual key in the store, made by `TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE` as the role `AM-M6` needs ("one exact noncritical role,
source and artifact separately reviewed and adopted under named human authority"). The role kind is a terrain cell (user decision, 2026-10-04); the terrain is
Forest (Live Map tile code 6, fallback fill `TILE_COLORS[6]` = `#1b3a1b`). Nothing activates it: `AM-M6` execution stays `NO-GO` and the normal Live Map does not read it.

## What it is

16 x 16, scale class `x1`, 7 colours, no animation: a quiet speckled ground with crowded canopies of varying size and a darkest-tone shadow, drawn so it wraps at every
edge (a 4 x 4 repeat has no seam). Its average colour is (28, 60, 28) against the fallback (27, 58, 27). The user chose it over a first, plainer candidate on 2026-10-04.
This tile is the `plain` slot of the key's detail axis (see "The three slots"). The registry entry has `variant_axes: []` and a `detail` axis.

## The chain (everything that belongs together)

| Link | Value |
|---|---|
| Visual key / family | `terrain.forest` / `terrain` (hand-edited `definitions/visual_keys.yaml`) |
| Source asset id | `terrain_forest` |
| Producer revision | experiment workspace sprite `forest_b` `r0002`, source hash `sha256:2d87ed5de4c5de406f219aa22493b50a5201e1785a26f1f52a7d7eb7e38d5c03` |
| Intake | `in-ea65cc2668bc8430` (PASSED, no findings; the store's own render matched the producer preview) |
| Adoption | `ad-caf09a15bd89d2af`, adopted as `terrain_forest` `r0001` on 2026-10-04 by `nhan` (owner) through the CLI gate, licence `CLEARED` stated by the adopter |
| Artifact | `generated/terrain_forest--x1/2f62ba6c...e672a8.png`, pixel hash `pixels-v1:2f62ba6cd4df1284815545b59371f7f5d37216234a1d6342424312da56e672a8`, png hash `sha256:e542661faa1b5a62bbb68ca6a63ffe152116b134c8582fe573aa523d7aa3f8ce` |
| Release candidate | `manifests/candidates/pilot/rc-0001.json`, file hash `sha256:4f5eb10ff20955596bfabbc7a9a19f11cee8d2dda38ea11beb814b8655aaea42` (one entry; not active) |
| Runtime manifest | `export-runtime --catalog-id pilot --release-id rc-0001`: `candidate_manifest_hash` above, `registry_hash` `sha256:07f5d265767176d981aaa41c68544779436225de80da7c1fdefafa4e41821133` |

A first candidate (`forest_a` r0002, intake `in-87b5972640ed63c7`, PASSED) was drawn, found short of detail by the user and **never adopted**; its quarantine stays local and ungit.

## How it was checked

`python -m visual_assets.store audit` (`chain ok`) and `verify` (`store ok`) on the committed catalog; `tests/visual_assets` (including the real-Aseprite tests, run locally under D10) pass.
The adoption was typed by the user in their own terminal; an agent never ran `adopt`. Reproduce the export with
`python -m visual_assets.store export-runtime --catalog-id pilot --release-id rc-0001 --out <new dir>`.

## The three slots (`TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES`)

The key declares a decorative detail axis, `detail: {values: [plain, bush, tree], default: plain}`, in that order: the client picks over the declared order, and the
64 x 64 spread the user approved on 2026-10-04 (plain 1354, bush 1397, tree 1345 at seed 1) was computed for it. Each value has its own adopted tile; the
client falls back picked -> `plain` -> the flat fill. Look only.

| Slot | Source asset | Adoption | Artifact pixel hash |
|---|---|---|---|
| `plain` (the default) | `terrain_forest` r0001 | `ad-caf09a15bd89d2af` (names no detail value: it was adopted before the axis existed and fills the default, unchanged) | `pixels-v1:2f62ba6c...e672a8` |
| `bush` | `terrain_forest_bush` r0001 | `ad-5615d03ed5a98f0a`, `--detail bush`, 2026-10-04 by `nhan` (owner) | `pixels-v1:58f2fd6fff9025564b0b03efbe0cef18691e3673486e616539d20ef6ba8fac33` |
| `tree` | `terrain_forest_tree` r0001 | `ad-34303489f1e5db70`, `--detail tree`, 2026-10-04 by `nhan` (owner) | `pixels-v1:569ba7004064ee83b51f9c8c13c2624e1c8e4bcf0ad76936e740a4b8fa031654` |

The bush (producer sprite `forest_bush2`, intake `in-0bb0ef9116d72ee2`) is low, lighter foliage clumps with red berries; the tree (`forest_tree2`, intake `in-3cafac684023adbc`) is one large
dome crown with leaf highlights and a cast shadow. Both keep the plain tile's outer ring and its bottom band, so any mix of the three tiles shows no seam (evidence: a 4 x 4 mixed preview and a
side-by-side strip in `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-FOREST-DETAIL-TILES/`). They add two colours to the plain tile's seven: leaf-light `#3a6e32` and berry `#9a3b3b`.

**The redraw.** A first draft of each (intakes `in-1f3ef37e2cc9156b` bush and `in-990026dd005070e8` tree) changed only one canopy and used the plain palette; the user found both too close to the plain tile
and asked why, so both were redrawn. The first drafts stay PASSED, reviewed and **un-adopted** in the local, gitignored quarantine; they are not part of the catalog.

| Link | Value |
|---|---|
| Release candidate | `manifests/candidates/pilot/rc-0002.json`, file hash `sha256:b330f49dd0cf980a06ffe6a93cb28ffe70e39ea1dc03be9eb146cdc53bd83367` (three entries, one per slot; not active). `rc-0001` stays as the retained previous release |
| Runtime manifest | `export-runtime --catalog-id pilot --release-id rc-0002`: `candidate_manifest_hash` the file hash above, `registry_hash` `sha256:cefb9984f300603b37ec5c9a2fbaa911800d0829a72244f46c5474c4ca0efce9`, entries per slot and a `details` block with the declared axis |
| Frontend fixture | `frontend/src/visualAssets/__fixtures__/pilot/` is the committed copy of that export; `tests/visual_assets/test_pilot_fixture.py` checks it equals a fresh export |

`rc-0001` can no longer be exported (the registry changed since it was assembled, `registry_mismatch`); it is still read and `verify` tolerates its axis-less entry.

**`pilot/rc-0003`** (`TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET`): registering the other 22 Live Map terrain keys (`optional: true`, for the draft set `terrain-v1`) changed the registry hash, so `rc-0002` can no longer be exported (`registry_mismatch`, by design). `rc-0003` was assembled from the new registry with exactly rc-0002's three entries

**`pilot/rc-0004`** (`TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT`, user approved assembling it on 2026-10-06): registering the three `border.*` mask keys (D19) changed the registry hash again, so `rc-0003` can no longer be exported (`registry_mismatch`, by design). `rc-0004` was assembled from the new registry with exactly rc-0003's three entries (a test asserts it); the pilot fixture is its export. `rc-0001` to `rc-0003` stay as history. Candidate only: nothing is active.

**Draft set `terrain-v1` adopted (2026-10-05T18:17:03Z, `TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION`):** the owner ran `adopt-set` (set adoption `sa-f4c541f25f112221`, draft set hash `sha256:287ab36c0299f9180b2ebf47afc84c95babf612818f80af3e0eeb78457023eb2`) after reviewing the whole map with borders. The catalog now holds 31 more sources (22 terrain tiles and the nine `border.*` masks) next to the forest's three. The drafts stay in `visual_assets/drafts/terrain-v1/` as history and the adoption points at each of them. **No release candidate covers the 31 new slots**: `pilot/rc-0004` holds the forest's three slots only, nothing has been built for the new sources, and the game does not read them. A candidate for them is the owner's decision, asked by `TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN` if the rerun needs the runtime export.
(same slots, artifact ids and pixel hashes: tested) and is what the committed runtime fixture now exports (`registry_hash` `sha256:3d2eeeccc864b5a0dae9660075eba66e0f27940ab024f2a58740d229f0a41451`, `candidate_manifest_hash` `sha256:32c38266f10a1fb8b5e3d31d7b865e1fc350c00fde696d2ce6f2aa0c18eada19`). `rc-0001` and `rc-0002` stay committed as history.

