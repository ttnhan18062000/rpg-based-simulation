---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE
phase: open
date: 2026-10-02
tags: [architecture, testing, documentation]
---

# TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE

## Title
Sandboxed build, canonical pixel hash, release-candidate manifest, `verify` and `gc`

## Status
OPEN

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

## Out of Scope
- Activation, runtime manifest locators, client compatibility ranges, signing (`AM-M5`-`M7`, `AM1-W08`).
- Atlases, sheets, animation export; more than one scale class.
- CI with Aseprite (`U-14`); the exporter is exercised locally only.
- MCP store tools (child 6).

## Acceptance Criteria
- [ ] Two PNG fixtures with identical pixels but different encodings (different filter choice, compression
      level, colour type RGBA vs indexed, an extra ancillary text chunk, different RGB under alpha 0) have the
      same `pixel_hash`; changing one visible pixel, the width, or swapping width and height changes it.
- [ ] `pixel_hash` of one fixture equals a value computed by hand in the test from the documented definition
      (not by calling the same function twice).
- [ ] The PNG reader rejects each of: bad signature, bad CRC, 16-bit, interlaced, over-`MAX_DIM`, truncated
      `IDAT`, decompressed size above the bound, data after `IEND`.
- [ ] Integration: building one adopted synthetic source twice gives the same `PixelHash` and one artifact file;
      a revoked source is refused.
- [ ] `assemble_release` writes a manifest that parses strictly, refuses each case in scope item 4, never
      overwrites, and the tree contains no file or field naming an active release.
- [ ] `verify` passes on a clean synthetic store and reports the specific finding for each planted fault: edited
      PNG pixel, PNG renamed to another hash, deleted artifact record, orphan file in `generated/`, manifest
      pointing at a missing artifact, manifest pointing at a revoked source, stray file in `sources/`.
- [ ] `verify` passes on the committed catalog in CI (`test_catalog_integrity.py`).
- [ ] `gc` without `--delete` changes nothing; with it, it removes only listed files and never anything under
      `sources/`, `provenance/`, `manifests/`.
- [ ] Boundary test: only `store/build` imports `drawing.backend.sandbox`; no other store module imports
      `drawing`.
- [ ] `pytest tests/visual_assets -m "not slow and not extra_slow"` green without Aseprite; integration green
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
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(open)
