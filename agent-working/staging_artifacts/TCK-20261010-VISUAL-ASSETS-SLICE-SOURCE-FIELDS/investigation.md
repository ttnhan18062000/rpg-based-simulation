---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS
artifact_type: investigation
tags: [architecture, testing, security]
---

# Investigation: slice metadata (chunk 0x2022)

## Facts (verified)
- `intake/aseprite.py` skipped chunk 0x2022 (unknown types are skipped by declared size). Tags are the pattern: `_read_tags`, bounds before reads, positions not names in findings.
- Aseprite file spec, slice chunk: DWORD key count, DWORD flags (1 nine-slice, 2 pivot), DWORD reserved, STRING name; per key DWORD frame, LONG x, y, DWORD w, h; nine-slice adds LONG cx, cy, DWORD cw, ch; pivot adds LONG px, py. Centre and pivot are relative to the slice's own corner.
- Real Aseprite (1.3.x on this machine) round-trip: plain, 9-slice and pivot slices written through Lua `spr:newSlice` read back exactly as the parser reports (`test_the_parser_reads_slices_exactly_as_aseprite_reads_them_back`, passed first run). The Lua API only makes frame-0 keys, so multi-key layout is covered by the synthetic builder (same layout, unit tests).
- One slice chunk per slice; flags are per chunk, so "flag/key mismatch" cannot occur in a file. The file-level violations are unknown flag bits and zero keys; the per-key centre/pivot consistency is enforced by the contract (`SourceSlice`).
- Worst-case record: 16 slices x 16 keys with centre and pivot, 32-char names, in a 16-frame record = 30,683 bytes against `MAX_RECORD_BYTES` 131072.
- No committed source has a slice chunk: all 77+ `SourceRecord`s round-trip byte-identical (tested).

## Findings codes
`SLICE_OUT_OF_BOUNDS` (counts), `SLICE_INVALID` (name, duplicates, no keys, flag bits, frame range/order), `SLICE_GEOMETRY_INVALID` (rect/centre/pivot).
