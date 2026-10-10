---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS
phase: implement
date: 2026-10-10
tags: [architecture, testing, security]
---

# TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS

## Title
Slice metadata (name, per-frame rect, 9-slice centre, pivot) read from each source and stored per source revision

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`. Owner, 2026-10-10 (blocking questions, after PR #487 merged): next asset batch = slices, 9-slice centres and pivots, covering the store AND the agents' drawing tool; bounds approved: at most 16 named slices per source and at most 16 per-frame keys per slice; slice names follow the animation tag rule (1..32 chars, `BoundedText`).

## Scope
- **Parser** (`intake/aseprite.py`): read the slice chunk 0x2022 instead of skipping it. Layout per the Aseprite file spec (verify against real Aseprite, below): DWORD key count, DWORD flags (1 = 9-slice, 2 = pivot), DWORD reserved, STRING name; per key: DWORD frame, LONG x, LONG y, DWORD w, DWORD h; if 9-slice: LONG cx, LONG cy, DWORD cw, DWORD ch; if pivot: LONG px, LONG py. The slice user-data chunk (0x2020 right after) stays skipped.
- **Hostile input, as for tags:** check the slice count against `MAX_SOURCE_SLICES` and each key count against `MAX_SLICE_KEYS` BEFORE reading entries; check byte lengths before each read; validate names with the record's own name type; findings name a slice by position, never its text; detail clamped to 256 chars.
- **Bounds** in `visual_assets/store/config.py`: `MAX_SOURCE_SLICES = 16`, `MAX_SLICE_KEYS = 16` (owner-approved 2026-10-10); rows in `budgets.md`.
- **Contract** (new `contracts/slices.py` or alongside animation, implementer's choice): `SliceName` (same rule as `TagName`), `SliceRect(x, y, w, h)`, `SlicePivot(x, y)`, `SliceKey(frame, bounds, center?, pivot?)`, `SourceSlice(name, keys)`. Rules: names unique per source; slices sorted by name; keys sorted by frame, unique, `frame < frame_count`; `w, h >= 1`; bounds inside the canvas; centre (relative to the slice origin) inside the slice bounds with `w, h >= 1`; pivot (relative to the slice origin) with `0 <= px <= w` and `0 <= py <= h`; the 9-slice and pivot flags hold for every key of a slice.
- **Storage:** optional `SourceRecord.slices`, dropped when absent (`drop_absent`) so every existing record stays byte-identical; derived at adoption like `SourceRecord.animation` (`store/animation.py:25-37`, `adoption.py:224-242`); a bad one is refused (new quarantine codes, e.g. `SLICE_OUT_OF_BOUNDS`, `SLICE_INVALID`, `SLICE_GEOMETRY_INVALID`).
- **Real-Aseprite parity test** (`needs_aseprite`, `tests/visual_assets/store/integration/test_real_aseprite.py`, like `test_the_parser_reads_animation_metadata_exactly_as_aseprite_reads_it_back` at :210): Lua `spr:newSlice`, `.center`, `.pivot`; reload; compare to `read_facts`. Test builders gain a slice chunk builder.
- **ADR D25** (draft text; **the owner approves it before this child's commit is approved**): slices per source revision, the bounds, the geometry rules, coordinates in source pixels.

## Out of Scope
- No `src/`, no app wiring (activation parked until the RPG core lands, PR #450), no gate result moved, no new art, no `.github/` change, no other `frontend/` file.
- No registry (`catalog/registry`), `ArtifactRecord` or runtime-manifest field: slices live per source revision, so the registry budget (90% used, budgets.md standing rule) is not touched.
- Git LFS, raising any existing bound, client use of atlases/animation/slices, a self-hosted runner.
- Slice user data (colour, text, properties). Per-frame keys made by the drawing tool (child 3 makes single-key slices).

## Acceptance Criteria
- [ ] Owner approved D25 text (asked by the implementer as a blocking question; planner reviews the draft first).
- [ ] Every existing source record and rc-0008 rebuild byte-identical (no slices in today's sources).
- [ ] Each planted bad case refused with its code (counts over bound, truncated chunk, duplicate name, key frame out of range, rect outside canvas, centre outside rect, pivot outside rect, flag/key mismatch, bad name).
- [ ] Real-Aseprite parity test passes locally; security review clean or findings fixed.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-SLICES`
- Pattern: `TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/research_asset_pipeline.md` (section 8, practice row 12, recommendation 5: pivot and 9-slice fields before UI-panel or animated assets)
- `agent-working/stored_artifacts/TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS/` (the pattern this batch copies)

## Related Code Areas
- `visual_assets/store/intake/aseprite.py` (:81-111 tags, :245 skip, :272-285 checks), `visual_assets/store/contracts/{animation,source,intake,base}.py`, `visual_assets/store/{animation,adoption,config}.py`, `tests/visual_assets/store/builders.py`

## Assumptions / Open Questions
- Store edits make `docs/assets/aseprite_local_proof.json` stale: do NOT re-run it here; child 4 re-runs it once after the last store edit.

## Implementation Notes
Parser `_read_slice`/`_slice_problems` (bounds before reads, findings by chunk position), `contracts/slices.py`, `store/slices.py`, `SourceRecord.slices` (empty tuple refused), adoption derives and refuses a bad one, three `SLICE_*` codes, bounds 16/16 with budgets rows (worst case 30,683 B), ADR D25 accepted by the owner 2026-10-10. Security review: clean (80k fuzz cases, only `SliceError`); its note on finding positions after a rejected slice was fixed. Handoff slice-count check is part of child 3.

## Test Summary
41 new unit tests, 9 parser mutants all caught, real-Aseprite parity test passes locally; `tests/visual_assets` + docs + static green except the proof-record staleness test (expected; child 4 re-runs the record).

## Files Changed
`visual_assets/store/{config,adoption,slices}.py`, `contracts/{slices,source,intake}.py`, `intake/aseprite.py`, builders, unit + integration tests, `test_boundaries.py`, `budgets.md`, ADR D25, staging artifacts.

## Completion Summary

