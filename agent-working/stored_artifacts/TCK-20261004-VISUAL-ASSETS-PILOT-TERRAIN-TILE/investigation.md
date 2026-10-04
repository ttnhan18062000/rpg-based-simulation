---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE
artifact_type: investigation
tags: [mcp, live-map, testing]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

- Re-checked against what landed: ticket 1 left one stale "proposed budget" bullet in `store_contract.md` (fixed here). The store has no tool path into the registry, so the key is a hand edit; `adopt` checks the key against it, so it had to land before adoption.
- The MCP server may be rooted in another checkout, so intake was run through the CLI in this worktree to put the quarantine in the catalog that adoption uses.
- Candidate A (`forest_a` r0002, intake `in-87b5972640ed63c7`) was rejected by the user for lack of detail and never adopted. Candidate B (`forest_b` r0002, intake `in-ea65cc2668bc8430`) was chosen on the previews, 4 x 4 patch and neighbour-fill comparison (average (28,60,28) vs fallback (27,58,27)).
- Detail variants (plain/bush/tree) were deferred by user decision to `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS`.
- A first adoption was made under a misspelled source asset id. Before any commit landed it was discarded, at the user's choice: the adoption-derived files were removed from the working tree and index, intake `in-ea65cc2668bc8430` (still PASSED in the quarantine) was kept, and the user adopted again in their own terminal as `terrain_forest` (`ad-caf09a15bd89d2af`). The store records were never hand-edited. Build, `release --catalog-id pilot` (rc-0001 again, on a clean tree) and `export-runtime` were re-run; the pixel and PNG hashes are unchanged, the candidate manifest hash is new.
- Which revision, intake, adoption, artifact, release and manifest hashes belong together: `docs/assets/pilot_terrain_key.md`.
