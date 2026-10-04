---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST
artifact_type: investigation
tags: [architecture, rendering, determinism, testing]
---

# Investigation — TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST

- Re-checked against what landed: `release`/`assemble_release` take `--catalog-id`/`--release-id`, so `export-runtime` uses the same spelling (the ticket wrote `--catalog`/`--release`). Candidates live at `manifests/candidates/<catalog_id>/<release_id>.json`; `verify.verify()` returns `Finding`s with `blocking`.
- The planner's per-type bound (ticket 2) applies: `RuntimeManifest.size_bound = "MAX_MANIFEST_BYTES"`. The maximum-legal-instance guard showed the widest runtime manifest at `MAX_VISUAL_KEYS` = 1024 entries is **359764 B** (family, file and sizes per entry) against the candidate manifest's 292081 B, over the 327680 B bound set in ticket 2; `MAX_MANIFEST_BYTES` is now 393216 (6 x 64 KiB) and `docs/assets/budgets.md` says why.
- `adopt` needs the store's render to match the producer preview, so the fixture's previews are the same shape images as the renderer's output (a renderer that draws by source hash).
- Byte-identical regeneration: all inputs are fixed (timestamps, ids, a hash-keyed renderer); PNGs are written with zlib level 0 (stored blocks) so different zlib builds produce the same bytes.
- Added refusal `registry_mismatch` (not in the ticket): a candidate carries the registry hash it was assembled from; exporting families from a changed registry would be silently wrong.
