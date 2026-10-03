---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST
phase: open
date: 2026-10-03
tags: [architecture, rendering, determinism, testing]
---

# TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST

## Title
Minimal runtime manifest (proposal 9.3) exported from one release candidate, and a synthetic fixture export the frontend rehearsal consumes

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Under Profile A (ADR `D8`) the frontend build consumes the assets of one release candidate. The store's
`ReleaseCandidateManifest` is an internal record (artifact ids, registry hash); the client needs the smaller shipped contract of
proposal 9.3: exact release identity, artifact hashes, publisher-generated file names, decoded bounds and the fallback-contract
version, and **nothing** from the protected provenance (no approver, no source path, no licence record, no review note). This
ticket adds that contract and its export, plus a committed synthetic export for ticket 4 to build against.

## Scope
1. **Contract** `visual_assets/store/contracts/runtime.py`: `RuntimeManifest` (`record_type: "runtime_manifest"`, `schema_version: 1`,
   `extra="forbid"`, frozen, strict, like every other record) with `catalog_id`, `release_id`, `candidate_manifest_hash`
   (`FileHash` of the exact candidate manifest bytes it was exported from), `registry_hash`, `fallback_contract_version: Literal[1]`,
   and `entries`: `visual_key`, `family` (from the registry), `pixel_hash`, `file` (exactly `<64 hex>.png`, derived from the pixel
   hash, never a path), `width`, `height` (decoded, bounded by `config.MAX_DIM`). Unique keys, at most `MAX_VISUAL_KEYS`, sorted by
   key. Add a contract fixture in `catalog/fixtures/contracts/` and its round-trip test like the other records.
2. **Export** `visual_assets/store/runtime_export.py`: `export_runtime(catalog_id, release_id, out_dir, ...)`:
   - runs `verify` first and refuses on any blocking finding (`verify_failed`);
   - reads the candidate manifest strictly; refuses an unknown release (`unknown_release`);
   - for each entry: opens the artifact PNG under `generated/`, re-decodes it with `store/pixels.py`, checks the pixel hash
     (`artifact_mismatch`), takes width and height from the decode;
   - writes `runtime_manifest.json` (`canonical_json`) and the PNGs as `<hex>.png` into `out_dir`, staged in a `.tmp-*` sibling and
     renamed, so the result is all-or-nothing; refuses an existing `out_dir` (`out_exists`) and any `out_dir` inside the catalog root
     (`out_inside_catalog`), and never follows a symlink;
   - is deterministic: the same release gives byte-identical output.
   Add the layer's `STORE_ALLOWED` row in `tests/visual_assets/test_boundaries.py`; the drawing server may **not** import it (no
   MCP tool for export).
3. **CLI** `python -m visual_assets.store export-runtime --catalog C --release rc-NNNN --out DIR`: no human gate (it reads committed
   candidates and writes outside the catalog), exits non-zero with the code on refusal.
4. **Synthetic fixture export.** A generator in the tests tree (for example `tests/visual_assets/store/runtime_fixture.py`) builds a
   synthetic catalog with the existing support code (`tests/visual_assets/store/adoption_support.py`, fake renderer, no Aseprite),
   with three `fixture.rehearsal.*` keys whose 16 x 16 images are clearly different shapes (not only different hues: ticket 4 checks
   that), assembles one release candidate, and exports it. Its committed output lives at
   `frontend/src/visualAssets/__fixtures__/rehearsal/` (manifest + PNGs). A test regenerates it into `tmp_path` and asserts it is
   byte-identical to the committed copy; the generator has a `--write` mode to refresh it. This is the only `visual_assets` -> `frontend/`
   link and it is a test-time, file-level one: no import either way.
5. **Docs**: `docs/assets/store_contract.md` gains the runtime manifest (fields, what it excludes and why, the export command and its
   refusal codes); the command table and the "Not built" list are updated.

## Out of Scope
- Writing into any real frontend build path from the CLI, wiring the export into `npm run build`, or exporting a real catalog
  (there is none). Wiring the real build is part of `AM-M6`, dormant.
- Animation, frames, pivots, atlases, more than scale class `x1`, accessibility variants (proposal 9.2 descriptor axes): the
  manifest carries `fallback_contract_version` so a later version can add them.
- A fallback-safety class in the registry: the rehearsal's fallbacks are defined on the frontend side by family (ticket 4). If
  you find that a registry field is needed, stop and tell the planner.

## Acceptance Criteria
- [ ] `RuntimeManifest` rejects unknown fields, a non-derived `file`, duplicate keys, oversize dimensions, and an unsupported version (each tested).
- [ ] The exported manifest contains no field from the provenance records (test lists the allowed field names exactly).
- [ ] `export_runtime` refuses `verify_failed`, `unknown_release`, `artifact_mismatch`, `out_exists`, `out_inside_catalog`, each leaving no output and no change to the catalog (snapshot test, like `test_release.py`).
- [ ] Two exports of the same release are byte-identical.
- [ ] The committed frontend fixture equals a fresh regeneration (test), and its three images differ in shape, not only colour (test compares alpha masks).
- [ ] Boundary test green with the new row; the drawing server cannot import `runtime_export`.
- [ ] `tests/visual_assets` passes without Aseprite.

## Related Tickets
- TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL (parent)
- TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE (release candidates, `pixels-v1`, `verify`)
- TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL (consumes the fixture)

## Related Docs
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (9.1-9.4)
- docs/assets/store_contract.md, docs/architecture/visual_asset_foundation_adr.md (D3, D4, D8, D9)

## Related Stored Artifacts
- None yet; staging artifacts go to `agent-working/staging_artifacts/TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST/`.

## Related Code Areas
- visual_assets/store/contracts/, visual_assets/store/release.py, verify.py, pixels.py, cli.py; tests/visual_assets/store/; tests/visual_assets/test_boundaries.py; frontend/src/visualAssets/__fixtures__/ (new)

## Assumptions / Open Questions
- The candidate manifest bytes are hashed as stored (they are written with `canonical_json` and never rewritten).
- The frontend fixture PNGs are tiny (16 x 16); committing them is consistent with D3 because they are synthetic fixtures, not adopted assets, and live in a `__fixtures__` directory that cannot be mistaken for production.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
