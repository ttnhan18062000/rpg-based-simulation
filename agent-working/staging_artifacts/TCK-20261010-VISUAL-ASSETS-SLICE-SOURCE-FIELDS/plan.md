---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS
artifact_type: plan
tags: [architecture, testing, security]
---

# Plan: slice source fields

1. Bounds `MAX_SOURCE_SLICES`, `MAX_SLICE_KEYS` = 16 in `config.py`; two rows in `budgets.md` (owner-approved 2026-10-10).
2. `contracts/slices.py`: `SliceName`, `SliceRect`, `SlicePivot`, `SliceKey`, `SourceSlice`, `check_slices` (needs canvas and frame count, so `SourceRecord` calls it).
3. `SourceRecord.slices` optional, `drop_absent`; an empty tuple is refused so one absent shape exists.
4. Parser `_read_slice` / `_slice_problems`; `RawSlice`, `RawSliceKey` on `AsepriteFacts`.
5. `store/slices.py` derives the records (sorted by name); `adoption.build_entry_records` calls it (refuses if invalid).
6. Codes in `contracts/intake.py`. Layer `slices` in `test_boundaries.py`.
7. ADR D25 draft (owner approves the text first). Not here: runtime export, drawing tool, docs sweep, proof-record re-run (children 2-4).
