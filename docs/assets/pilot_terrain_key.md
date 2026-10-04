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
Detail variants (plain, bush, tree) are deferred to `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS` by user decision; this tile is meant to become their `plain` default.
The registry entry has `variant_axes: []`.

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
