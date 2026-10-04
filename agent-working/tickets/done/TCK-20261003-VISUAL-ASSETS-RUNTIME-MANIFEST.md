---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST
phase: done
date: 2026-10-03
tags: [architecture, rendering, determinism, testing]
---

# TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST

## Title
Minimal runtime manifest (proposal 9.3) exported from one release candidate, and a synthetic fixture export the frontend rehearsal consumes

## Status
DONE

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
- [x] `RuntimeManifest` rejects unknown fields, a non-derived `file`, duplicate keys, oversize dimensions, and an unsupported version (each tested).
- [x] The exported manifest contains no field from the provenance records (test lists the allowed field names exactly).
- [x] `export_runtime` refuses `verify_failed`, `unknown_release`, `artifact_mismatch`, `out_exists`, `out_inside_catalog`, each leaving no output and no change to the catalog (snapshot test, like `test_release.py`).
- [x] Two exports of the same release are byte-identical.
- [x] The committed frontend fixture equals a fresh regeneration (test), and its three images differ in shape, not only colour (test compares alpha masks).
- [x] Boundary test green with the new row; the drawing server cannot import `runtime_export`.
- [x] `tests/visual_assets` passes without Aseprite.

## Related Tickets
- TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL (parent)
- TCK-20261002-VISUAL-ASSETS-STORE-BUILD-RELEASE (release candidates, `pixels-v1`, `verify`)
- TCK-20261003-VISUAL-ASSETS-SURFACE-REHEARSAL (consumes the fixture)

## Related Docs
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md (9.1-9.4)
- docs/assets/store_contract.md, docs/architecture/visual_asset_foundation_adr.md (D3, D4, D8, D9)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST/` (plan, investigation, test_plan)

## Related Code Areas
- visual_assets/store/contracts/, visual_assets/store/release.py, verify.py, pixels.py, cli.py; tests/visual_assets/store/; tests/visual_assets/test_boundaries.py; frontend/src/visualAssets/__fixtures__/ (new)

## Assumptions / Open Questions
- The candidate manifest bytes are hashed as stored (they are written with `canonical_json` and never rewritten).
- The frontend fixture PNGs are tiny (16 x 16); committing them is consistent with D3 because they are synthetic fixtures, not adopted assets, and live in a `__fixtures__` directory that cannot be mistaken for production.

## Implementation Notes
- **Re-check against what landed:** the CLI spelling follows `release` (`--catalog-id`, `--release-id`, plus `--out`), not the ticket's `--catalog`/`--release`; no registry field was needed.
- `MAX_MANIFEST_BYTES` raised 327680 -> 393216: the guard test (maximum legal instance of every record type, ticket 2) caught that the runtime manifest at 1024 entries is 359764 B (family, file, width, height per entry) against the candidate manifest's 292081 B. `docs/assets/budgets.md` row updated; still `PROPOSED`.
- `RuntimeManifest` has `size_bound = "MAX_MANIFEST_BYTES"`, joins `RECORD_TYPES` (so the generic strictness tests run on it) and has a contract fixture.
- Extra refusal `registry_mismatch` (the candidate's registry hash no longer matches the registry); also `out_parent_missing`.
- The output is checked before `verify` runs (tests prove the order); the export stages in a `.tmp-*` sibling and renames, so a failure or a racing creator of the output leaves nothing and replaces nothing.
- Fixture PNGs are encoded with zlib level 0 so the committed bytes do not depend on the zlib build; the three shapes (diamond, disc, hollow frame) differ in alpha mask by well over 20 pixels pairwise.
- No MCP exposure: `runtime_export` is not in `SERVER_STORE_ALLOWED`; the planted-server-import test now lists it.
- `test_docs_commands.py`: the command-name regex accepted only `[a-z_]`, so `export-runtime` was undocumented to it; it now accepts a hyphen. `test_record_bounds.py`: `runtime_export.py` is a new PNG read site and is in the expected set.

## Test Summary
- `tests/visual_assets` without Aseprite: 979 passed, 202 skipped. `make visual-assets-aseprite-local`: 202 passed, 0 skipped. `tests/static tests/architecture tests/docs`: 240 passed.
- New: `test_runtime_contract.py` (14), `test_runtime_export.py` (17), `test_runtime_fixture.py` (3); the maximal runtime manifest in `test_record_bounds.py`.
- Mutants, each killed by its named test: verify not run (`test_a_store_that_fails_verify_is_refused`); inside-catalog check removed (two tests); symlink-blind `exists()` (survived at first, because `rename` onto a symlink also refuses; the tests now assert the output is refused before `verify` runs, and it dies); pixel hash unchecked; no cleanup on failure (two tests); file derivation unchecked; registry hash unchecked; generator changed without refreshing the fixture (byte-identical test); two identical shapes (alpha-mask test).

## Files Changed
- New: `visual_assets/store/contracts/runtime.py`, `visual_assets/store/runtime_export.py`, `visual_assets/catalog/fixtures/contracts/runtime_manifest.json`, `tests/visual_assets/store/runtime_fixture.py`, `tests/visual_assets/store/unit/test_runtime_{contract,export,fixture}.py`, `frontend/src/visualAssets/__fixtures__/rehearsal/` (manifest + 3 PNGs)
- Changed: `visual_assets/store/{cli,config}.py`, `store/contracts/__init__.py`, `tests/visual_assets/test_boundaries.py`, `tests/visual_assets/store/unit/{conftest,test_record_bounds,test_docs_commands}.py`, `docs/assets/{store_contract,budgets}.md`

## Completion Summary
`export-runtime` writes the client's small runtime manifest and PNGs for one release candidate into a new directory, deterministically and all-or-nothing, with no MCP exposure; a committed synthetic export of three differently shaped images is ready for the surface rehearsal.
