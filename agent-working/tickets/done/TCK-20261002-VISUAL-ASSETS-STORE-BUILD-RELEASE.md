---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE
phase: done
date: 2026-10-02
tags: [architecture, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE

## Title
Sandboxed build, canonical pixel hash, release-candidate manifest, `verify` and `gc`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 5 of `TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION`. Export adopted sources to PNG artifacts identified by a
hash of their decoded pixels, assemble an immutable release **candidate** manifest, check the whole store's
integrity in pure Python (so CI can do it without Aseprite), and list unreachable files. Blocked by
`TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION`. Same branch (`visual-assets-store`).

## Scope
1. `visual_assets/store/build/fingerprint.py`:
   - `pixel_hash(png_bytes) -> PixelHash`, algorithm `pixels-v1` (D4): sha256 over
     `b"pixels-v1\0"` + width and height as unsigned 32-bit big-endian + the image as 8-bit non-premultiplied
     RGBA rows, top to bottom, where every pixel with alpha 0 is written as `00 00 00 00`.
   - A bounded pure-Python PNG reader (stdlib `zlib` only; Pillow and numpy are not project dependencies and must
     not be added): 8-bit greyscale, greyscale+alpha, RGB, RGBA and indexed (with `tRNS`), non-interlaced, all
     five filter types, CRCs checked, dimensions within `MAX_DIM`, decompressed size bounded. Anything else
     (16-bit, interlaced, APNG chunks, bad CRC, trailing data) is rejected.
   - `build_fingerprint(...)`: tool name and version, export-config hash, Lua pin hash.
2. `visual_assets/catalog/build-config/export.toml`: pinned export rules (format PNG, scale classes; start with
   one class `x1`). Parsed strictly; unknown keys rejected.
3. `visual_assets/store/build/exporter.py`: `build(source_asset_id=None)` exports each build-eligible adopted
   source revision through the shared sandbox (`visual_assets.drawing.backend.sandbox`, the one allowed import
   from `drawing`) with a fixed allowlisted command, into a temporary directory, then decodes the result and
   writes `generated/<artifact_id>/<pixel hash hex>.png` and `.artifact.json` (exclusive create; an existing
   identical artifact is a no-op). `artifact_id = <source_asset_id>--<scale class>`, so replacing an image keeps
   the id and changes the hash. Refuses revoked or non-adopted sources. Needs Aseprite and bwrap.
4. `visual_assets/store/catalog/release.py`: `assemble_release(catalog_id, *, release_id, ...)` writes
   `manifests/candidates/<catalog_id>/<release_id>.json` from the registry and the current artifacts; exclusive
   create; refuses a `release_id` that already exists or is not greater than every existing one, a registry key
   with no artifact (unless the key is marked optional), an artifact from a revoked source, and any artifact
   whose bytes fail re-hashing. No active pointer, no "latest" file (D6).
5. `visual_assets/store/verify.py`: `verify(catalog_root) -> list of findings`, pure Python: `STORE_FORMAT`
   supported; registry loads; `audit_chain` from child 4; every source, artifact and manifest record parses
   strictly and matches its bytes (`FileHash` for sources, `PixelHash` recomputed for PNGs, and file name equals
   the hash); no orphan file, no dangling reference; no manifest references a revoked source; nothing unexpected
   in the tracked tree. `tests/visual_assets/test_catalog_integrity.py` runs it on the committed catalog in CI.
6. `visual_assets/store/gc.py`: `gc(dry_run=True)` lists quarantine directories with no adoption and no pending
   review, review exports, and generated files not referenced by any artifact record. Deletion only with an
   explicit `--delete` flag on the CLI and never touches `sources/`, `provenance/` or `manifests/`.
7. CLI: `build`, `release`, `verify`, `gc`. `verify` exits non-zero on any finding.
8. Tests: unit (CI) with small committed PNG fixtures under `visual_assets/catalog/fixtures/png/`; integration
   (`needs_aseprite`) for the exporter.
9. Docs: `docs/assets/store_contract.md` (build, release candidate, verify, gc **built**; the exact `pixels-v1`
   definition), ADR (D4 algorithm recorded), structure doc, READMEs.
10. **Preview-to-source binding (added by asset-planner 2026-10-03).** The human reviews `preview.png` but adopts
    `source.aseprite`, and intake cannot prove the preview depicts the source (it checks only the PNG signature, IHDR
    and scale). So:
    a. Put the bounded PNG reader in a store layer that `intake` may import (not under `build`) and make intake
       fully validate the preview structure with it (new finding codes as needed).
    b. `review`, when Aseprite is available, renders the staged source through the sandboxed exporter into the review
       area as the image the human looks at, compares its pixel hash with the producer's preview at the same scale,
       and shows a mismatch prominently in `summary.txt` and records it. Without Aseprite, `review` says plainly that
       the preview is producer-supplied and unverified.
    c. `adopt` refuses an intake whose store-rendered review is missing or whose preview did not match, with its own
       error code.
11. **Chain anchoring (added by asset-planner 2026-10-03).** `ArtifactRecord` carries the hash of the exact `SourceRecord` bytes it was built from, so the release manifest
    (which carries artifact hashes) anchors the whole chain intake -> adoption -> source record -> artifact. `verify` checks it.

## Out of Scope
- Activation, runtime manifest locators, client compatibility ranges, signing (`AM-M5`-`M7`, `AM1-W08`).
- Atlases, sheets, animation export; more than one scale class.
- CI with Aseprite (`U-14`); the exporter is exercised locally only.
- MCP store tools (child 6).

## Acceptance Criteria
- [x] Two PNG fixtures with identical pixels but different encodings (different filter choice, compression
      level, colour type RGBA vs indexed, an extra ancillary text chunk, different RGB under alpha 0) have the
      same `pixel_hash`; changing one visible pixel, the width, or swapping width and height changes it.
- [x] `pixel_hash` of one fixture equals a value computed by hand in the test from the documented definition
      (not by calling the same function twice).
- [x] The PNG reader rejects each of: bad signature, bad CRC, 16-bit, interlaced, over-`MAX_DIM`, truncated
      `IDAT`, decompressed size above the bound, data after `IEND`.
- [x] Integration: building one adopted synthetic source twice gives the same `PixelHash` and one artifact file;
      a revoked source is refused.
- [x] `assemble_release` writes a manifest that parses strictly, refuses each case in scope item 4, never
      overwrites, and the tree contains no file or field naming an active release.
- [x] `verify` passes on a clean synthetic store and reports the specific finding for each planted fault: edited
      PNG pixel, PNG renamed to another hash, deleted artifact record, orphan file in `generated/`, manifest
      pointing at a missing artifact, manifest pointing at a revoked source, stray file in `sources/`.
- [x] `verify` passes on the committed catalog in CI (`test_catalog_integrity.py`).
- [x] `gc` without `--delete` changes nothing; with it, it removes only listed files and never anything under
      `sources/`, `provenance/`, `manifests/`.
- [x] Boundary test: only `store/build` imports `drawing.backend.sandbox`; no other store module imports
      `drawing`.
- [x] (added by asset-planner 2026-10-03) The PNG reader lives in a layer `intake` may import; intake fully validates
      preview structure (not just signature, IHDR and scale), each defect with its own finding code.
- [x] (added by asset-planner 2026-10-03) With Aseprite, `review` renders the staged source into the review area and
      compares pixel hashes with the producer's preview at the same scale; a mismatch is shown prominently in
      `summary.txt` and recorded; without Aseprite it says the preview is producer-supplied and unverified.
- [x] (added by asset-planner 2026-10-03) `adopt` refuses an intake whose store-rendered review is missing or whose
      preview did not match, with its own error code.
- [x] `pytest tests/visual_assets -m "not slow and not extra_slow"` green without Aseprite; integration green
      with it.

## Related Tickets
- TCK-20261002-EPIC-VISUAL-ASSET-FOUNDATION (parent)
- TCK-20261002-VISUAL-ASSETS-STORE-ADOPTION (blocks this)
- TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS

## Related Docs
- docs/plans/visual-asset-foundation/README.md
- docs/architecture/visual_asset_foundation_adr.md (D3, D4, D6)
- docs/assets/store_contract.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (sections 7, 9.3, 12)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- visual_assets/store/build/, visual_assets/store/catalog/release.py, visual_assets/store/verify.py, visual_assets/store/gc.py, visual_assets/catalog/build-config/, tests/visual_assets/

## Assumptions / Open Questions
- D4 confirmed by the user on 2026-10-02: artifact identity is the decoded-pixel hash, not the file bytes.
- D3 (decided): generated PNGs are committed only for adopted assets. `build` reads only adopted sources, so
  this holds by construction; the committed catalog still has no artifact after this ticket.
- `build` has no human gate but writes tracked files derived only from adopted sources. It is CLI-only and never
  on the MCP surface (D5).
- The exact Aseprite export command line must be confirmed against the pinned binary during investigation.
- Whether a registry key may be "optional" in a release is a small contract addition to child 2's
  `VisualKeyDefinition`; if it is needed, add the field with `schema_version` handling and tell the planner.

## Implementation Notes
Staging artifacts: `agent-working/stored_artifacts/TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE/`. Done as asset-planner decided after the re-check:

- **Pure pixels layer** (`store/pixels.py`): bounded stdlib PNG decoder and the `pixels-v1` hash; intake now fully decodes the producer's preview with it (finer finding codes), build uses it for artifact identity.
- **Store's own render** (`rendering.py` with an injected `RenderTool`, `review.py`): `review` records a typed `ReviewRenderCheck` and shows `store_render.png` with a prominent mismatch warning; `adopt` re-renders at adoption time and never
  trusts the stored file (it can be forged by any local process), refuses `preview_mismatch` / `review_render_missing` / `review_render_stale` / `renderer_unavailable`, copies the check into tracked provenance and binds its hash in the `AdoptionRecord`.
- **Build / release / verify / gc**: `store/build/{exportconfig,fingerprint,exporter}.py` (the one store layer importing the shared sandbox), `store/release.py` (ordered `rc-NNNN`, no active pointer), `store/verify.py` (non-blocking findings for
  revoked history), `store/gc.py` (dry run by default); CLI `build`, `release`, `verify`, `gc`; `visual_assets/catalog/build-config/export.toml` committed (rules, not an asset).
- **Contract additions** (additive, schema_version 1): `ArtifactRecord.source_record_hash` (chain anchoring), ordered `ReleaseId`, `VisualKeyDefinition.optional`, `ReviewRenderCheck`, `AdoptionRecord.review_hash`; `visual_key_taken`.

### Where ticket and reality differed (reported to asset-planner, who decided)
1. Ordered release ids, an `optional` marker and the chain-anchoring hash were missing from the contracts; the preview-to-source binding and `visual_key_taken` were added to this ticket by the planner.
2. `release` is `store/release.py` (not `store/catalog/release.py`): it needs records and eligibility. The PNG reader is a new pure layer so intake may import it. `review` is its own layer so intake never imports `drawing`.
3. The PNG is named by pixel hash and each revision has its own record (`<hex>.<revision>.artifact.json`): two revisions that render identically share the PNG, which the ticket's one-record-per-hash naming could not express.
4. Plain export runs no Lua, so the fingerprint's "Lua pin hash" is the pin of the template mounted in the sandbox; the docs say so.
5. A visual key maps to its asset through the adoption record of the asset's latest eligible revision; one key maps to one artifact (stated limit).
6. Two existing tests changed for legitimate reasons: the unknown-layer planted test uses a made-up layer name, and the boundary assertion for `store/build/exporter.py` is restored to the strict `== []` (planner item 7). The committed-catalog test now allows exactly `export.toml` in `build-config/`.

Process notes: while testing, an integration test without the isolating fixture wrote a sprite into the real `~/.cache/rpg-aseprite-mcp`; I removed exactly that directory (`sprites/hero`) and fixed the test. `origin/main` was merged into the branch mid-ticket (agent-working/ path move); the merge commit is `d239424e`.

## Test Summary
Every suite run separately under `systemd-run --user --scope -p MemoryMax=2G` (per the machine's OOM note). `tests/visual_assets`: 971 passed with Aseprite; 771 passed, 200 skipped with the Aseprite binary unavailable (what CI sees: all new unit tests,
the committed-catalog `verify`, and the pure PNG/hash tests run there); store unit + boundary + catalog integrity pass under the system python (707). Static + architecture + docs: 234 passed, 2 skipped, 1 xfailed. Main's path guards: 13 passed.
- `pixels-v1` equals a hand-computed value; 12 encodings of one image hash identically; one pixel, the width, or swapped width/height changes it; the RGB under alpha 0 is ignored; every refusal in the ticket (and APNG, colour-key tRNS, unknown critical chunk) has its own test; a decompression bomb is refused without inflating it.
- Real Aseprite (integration): the store's render equals the drawing tools' preview at scale 1 and 8; a real candidate goes review (MATCH) -> adopt (real re-render) -> build twice (same PixelHash, one artifact file); a revoked source is refused; a producer preview of a different sprite is caught as MISMATCH and adopt refuses.
- Mutation: 32 hand-applied mutants of the new guards plus 22 of the PNG reader; four survived at first (the whole-number-scale check, release's artifact-source-revoked check, and two earlier ones) and each led to a stronger test; all are now caught.

## Files Changed
Added: `visual_assets/store/{pixels,rendering,review,release,verify,gc}.py`, `visual_assets/store/build/{__init__,exportconfig,fingerprint,exporter}.py`, `visual_assets/store/contracts/review.py`, `visual_assets/catalog/build-config/export.toml`,
`visual_assets/catalog/fixtures/contracts/review_render_check.json`, `tests/visual_assets/test_catalog_integrity.py`, `tests/visual_assets/store/unit/test_{pixels,review_render,exportconfig,build,release,verify,gc}.py`,
`tests/visual_assets/store/integration/test_build_real.py`.
Changed: `adoption.py` (render checks, `visual_key_taken`, review copy), `audit.py` (review link), `records.py`, `revoke.py` (single eligibility test), `cli.py`, `identities.py` (`rc-NNNN`), contracts (`artifact`, `definitions`, `adoption`, `intake`, `__init__`), `errors.py`, `config.py`,
`intake/{validator,service,quarantine,__init__}.py` (full PNG validation, `prepare_review`/`export_review`), removed `intake/png.py`, the test support and the boundary test, docs (`store_contract.md`, ADR, plan README, READMEs), tickets 4 and 6.
No `src/`, `frontend/`, requirements or pyproject change.

## Completion Summary
Adopted sources export to PNG artifacts identified by their decoded pixels (`pixels-v1`), release candidates are immutable with ordered ids and no active pointer, `verify` checks the whole store in pure Python and passes on the committed catalog in CI, and `gc` lists before it deletes. The store now renders the source itself so the human's preview is checked against the bytes being adopted, and `adopt` re-does that check instead of trusting a stored file. The committed catalog still holds zero keys, sources, adoptions and artifacts.
