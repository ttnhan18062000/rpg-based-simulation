---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-03
tags: [performance, testing, mcp]
---

# Visual-asset budgets (`U-05`)

Every size, count, dimension and time bound in `visual_assets/`, what it was measured at, and the value this record proposes.
**Status of every row: `APPROVED 2026-10-04`** (the owner approved every proposed value as written, and kept `MAX_SOURCE_BYTES` at 102400 rather than reopening D2, through a blocking question on PR #309). Before that the rows were `PROPOSED`; the planner then
flips each row to `APPROVED <date>`. The code carries exactly the **Proposed** column (`tests/visual_assets/test_budgets_parity.py`
fails otherwise), so a changed number is a change to both.

Measurements come from `tools/visual_assets_measure_budgets.py` (re-runnable, one measurement per process, 2 GB cap), on the
licence holder's machine (Aseprite 1.3.18.6-x64, ADR D10), 2026-10-03. Quoted in
`agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-BUDGETS/investigation.md`. Nothing here is estimated: where no measurement
exists the cell says `NOT MEASURED` and why.

## Rule (applied as written)

- **R1 keep**: the current value is at least 2x the realistic worst case measured, and the cost at the bound stays under 2 s and 256 MiB per operation.
- **R2 raise**: raise to 2x the realistic worst case when the current value is tighter than that.
- **R3 lower**: lower to the largest measured value whose cost stays under 2 s / 256 MiB when the current value costs more.
- **R4**: `MAX_SOURCE_BYTES` is the D2 (no Git LFS) reversal trigger; changing it reopens D2.
- **R0**: no measurement and no data to apply a rule to (structural limit, or no real catalog yet): keep, marked `NOT MEASURED`. A row where the rule gives a silly or conflicting answer is **flagged** (below), not forced.

"Realistic worst case" is the largest thing the project actually produces today: a 128 px sprite, previewed at scale 8 (1024 px, the
only scale `export_handoff` makes), as dense as a random-colour image (the noise case: every pixel a different colour, which is
harsher than pixel art). Cost per operation means one decode, one render, one load.

## Bounds

| Module | Attribute | Current | Measured worst | Proposed | Rule | Flag | Status |
|---|---|---|---|---|---|---|---|
| `visual_assets.store.config` | `MAX_RECORD_BYTES` | 65536 | largest legal record of any type, with 4-byte UTF-8 text everywhere: `IntakeResult` 70540 B (64 findings), `CandidateHandoffPackage` 25534 B, the rest <= 2950 B (`test_record_bounds.py`); with ASCII text 19331 B | `131072` | R2: must cover the largest legal record (the old 65536 refused a legal `IntakeResult`); 131072 is 1.86x of it | F1, F5 (resolved) | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_REGISTRY_BYTES` | 1048576 | a realistic registry (2 axes x 4 values per key) grown to 450530 B (1409 keys) loads in 1.115 s, 26.0 MiB; the maximum legal instance (1024 keys + 1024 aliases) is 387038 B as YAML, 363498 B as compact JSON; an earlier pass: 715226 B loaded in 2.29 s (over 2 s), 1 MiB was not measured and is over the line by the same rate. **Re-measured 2026-10-09** (`TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS`, which added `safety_class` and a structured `fallback` to every key and the loader refuses axes): the realistic maximum a loader accepts (1024 keys + 1024 aliases, no axes, a class and a glyph-and-text fallback on every key, descriptions as before) is 414942 B as YAML (90 % of the bound) and loads in 0.75 s; a registry of 1024 icon keys that also carry labels would be a little larger, so the headroom is about 10 %. **The next growth of the key schema (a new per-key field, or a longer text bound) needs a budget review of `MAX_REGISTRY_BYTES` first, before the field is added** | `458752` | R3: 7 x 64 KiB, the largest rounded value measured under 2 s that still holds the maximum legal instance. Now the registry's own read bound (`size_bound`), not `MAX_RECORD_BYTES` | F1 (resolved) | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_MANIFEST_BYTES` | 393216 | widest legal manifest at 1024 slots (maximum-length ids and detail values, 64 keys x 16 detail values, `test_record_bounds.py`): `ReleaseCandidateManifest` 337137 B, `RuntimeManifest` 451552 B (it adds family, file and sizes per entry and the `details` block of 64 keys x 16 declared values); parse 0.003 s and 0.008 s (before the detail axis: 292081 B and 359764 B; at 1024 slots with a detail value on each, the old bound would have been exceeded by 11604 B before the `details` block, which alone is about 47 KB) | `524288` | new bound for both manifests' read/write size: the widest runtime manifest rounded up to 64 KiB (8 x 64 KiB), 1.16x. History: 327680 for the candidate alone, then 393216 when the runtime manifest was added, now raised for the detail axis (`TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT`); the owner approved the raise on the implementer's measurement, 2026-10-04. It now also bounds the draft preview manifest (`draft export`, a derived manifest-class export, not durable state): the widest at 256 maximum-length entries (64 keys x 4 detail values, 1024 px previews, full `details`) is 154837 B, 30 % of the bound, parse 0.002 s (`test_record_bounds.py`) | F1 (resolved) | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_VISUAL_KEYS` | 4096 | 1024 realistic keys (2 axes x 4 values) + 1024 aliases: 1.044 s, 22.4 MiB; 2048 keys 2.29 s (over); 4096 keys do not fit any byte bound | `1024` | R3: largest measured count under 2 s (there is no real catalog, so a low count costs nothing) | F1 (resolved) | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_DETAIL_KEYS` | new | the widest registry (1024 realistic keys + 1024 aliases) with 64 of its keys declaring a detail axis of 16 maximum-length values: 431326 B of YAML, loads in 1.52 s (R3: under 2 s; still under `MAX_REGISTRY_BYTES` 458752); the runtime manifest repeats each such key's values, 64 keys x 16 values is about 47 KB of the 451552 B widest manifest | `64` | R3, sized with `MAX_DETAIL_VALUES` so that 64 x 16 = `MAX_VISUAL_KEYS` slots: every slot of the widest manifest can carry its own detail value. Real use: one key (`terrain.forest`) with 3 values; owner decision | | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_DRAFT_SET_ENTRIES` | new | the widest legal records at 256 entries with maximum-length ids and detail values (`test_record_bounds.py`): `DraftSet` 116359 B (88.8 % of `MAX_RECORD_BYTES`, parse 0.002 s), `SetAdoptionRecord` 60791 B (with the longest 4-byte text in its free fields, parse 0.002 s); both fit the ordinary record bound (the first measurement, with a `source_hash` per entry, was 138887 B and did not: the field was dropped, its hash stays bound through the intake result) | `256` | R0, an owner decision (blocking question, 2026-10-04: "256 tiles per set"): enough for every Live Map terrain code with detail variants, and the widest set record stays under `MAX_RECORD_BYTES`. There is no limit on the number of sets | | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_DROPPED_DRAFTS` | new | the widest legal `DraftSet` after ADR D22: 256 entries that each declare a revision (`parent_revision`) plus 8 drop records with the longest 4-byte reason (80 characters, `DropReason`): 127211 B, 97.1 % of `MAX_RECORD_BYTES` (`test_record_bounds.py`); the 256-entry set alone was 116359 B before the revision field (123.0 KB with it) | `8` | R3: the largest count that keeps the widest legal set a reader can parse (a writer must never produce a record a reader refuses, F1); a set that needs more drops is rebuilt, not grown. Reason capped at 80 characters for the same reason. Approved with ADR D22 (owner, 2026-10-09, design question 1) | F1 (resolved) | APPROVED 2026-10-09 |
| `visual_assets.store.config` | `MAX_ALIASES` | 1024 | included in the 4096-key load above, not separated | `1024` | R0, NOT MEASURED separately | F1 | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_SOURCE_BYTES` | 102400 | 128 px, 1 frame, noise: 55764 B (1.84x of 102400; flat: 759 B); 16 frames of noise: 889025 B | `102400` | R1 waived: noise is above any realistic case; keeping it avoids reopening D2 (R4). The 16-frame dense case is a known limit: D2's reversal trigger working as designed, to be reopened when real animated art exceeds it. The owner may overrule | F2 (known limit) | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_DIM` | 128 | 128 px is the project maximum (1x, not 2x); 256 px would make a scale-8 preview 2048 px | `128` | R1 conflicts with the 2 s line (F3): kept | F3 | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_PREVIEW_BYTES` | 524288 | 128 px noise preview at scale 8: 83797 B; synthetic 1024 px: 41624 B | `524288` | R1 (2x of 83797 = 167594) | | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_PREVIEW_DIM` | 1024 | decode + pixels-v1 of a 1024 px RGBA PNG, Paeth rows (worst): 1.73 s, 17.0 MiB; 1536 px: 5.06 s; 2048 px: 7.87 s, 68 MiB | `1024` | R2 would give 2048 (7.87 s, over 2 s): kept | F3 | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_DECODED_BYTES` | 25165824 | decoding at the old bound (2508 px square, Paeth): 13.72 s, 102 MiB; at 1024 px (4195328 B decoded): 1.73 s | `4195328` | R3 (1024 * (1024 * 4 + 1)). Now the decoded-size bound only (`pixels.py`); file reads use `MAX_PNG_FILE_BYTES` | F4 (resolved) | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_PNG_FILE_BYTES` | new (the five PNG file reads used `MAX_DECODED_BYTES`) | worst legal store PNG: 1024 px RGBA random noise, written without compression 4195716 B (zlib 0), at zlib 9 4196671 B (noise does not compress); the compressible 2508 px sample was 228094 B and is not the worst case | `4259840` | new bound: the worst legal PNG rounded up to 64 KiB (65 x 64 KiB). Read bound at `verify`, `release`, `exporter`, `adoption`, `intake.service` | F4 (resolved) | APPROVED 2026-10-04 |
| `visual_assets.store.config` | `MAX_UNADOPTED_INTAKE_AGE_DAYS` | new (`gc` kept a PASSED never-adopted intake for ever) | one adopt+build+release adds about 4.4 KB of tracked files; a local intake with its review export about 6 KB (3.3-3.6 KB quarantine, 2.2-2.7 KB review); at the size bounds up to about 2.3 MB per intake (`MAX_SOURCE_BYTES` + two `MAX_PREVIEW_BYTES` renders + records); growth is too small to derive a number | `30` | R0, NOT DERIVED: a judgment, not a measurement. 30 days is long enough to review a candidate over a sprint and short enough that an agent drawing 10 candidates a day leaves at most ~700 MB worst case (~2 MB at real sizes) | | APPROVED 2026-10-04 |
| `visual_assets.store.rendering` | `MAX_RENDER_SCALE` | 16 | Aseprite render of a 128 px noise source: scale 8 0.083 s, scale 16 0.258 s | `16` | R1 (realistic scale is 8) | F6 | APPROVED 2026-10-04 |
| `visual_assets.store.contracts.handoff` | `MAX_LIMITATIONS` | 16 | 16 x 256-char limitations = 7057 B ASCII package; no real producer data | `16` | R0, NOT MEASURED (no real producer yet) | | APPROVED 2026-10-04 |
| `visual_assets.store.contracts.definitions` | `MAX_AXES` | 8 | widest key (8 axes x 64 values) = 7471 B of YAML; no real registry | `8` | R0, NOT MEASURED (no real catalog yet) | | APPROVED 2026-10-04 |
| `visual_assets.store.contracts.definitions` | `MAX_AXIS_VALUES` | 64 | same widest key | `64` | R0, NOT MEASURED (no real catalog yet) | | APPROVED 2026-10-04 |
| `visual_assets.store.contracts.definitions` | `MAX_DETAIL_VALUES` | new (`MAX_AXIS_VALUES` = 64 does not bound the detail axis: 1024 keys x 64 values would be about 2.3 MB in the runtime manifest, 6x the old bound) | 16 maximum-length (32 char) values on each of 64 keys: see `MAX_DETAIL_KEYS` | `16` | R0, a judgment: looks-only variants of a terrain tile are a handful (the pilot plans 3); 16 leaves room and is sized with `MAX_DETAIL_KEYS`; owner decision | | APPROVED 2026-10-04 |
| `visual_assets.store.contracts.intake` | `MAX_FINDINGS` | 64 | 64 x 256-char findings = 19331 B ASCII; the validator has 38 finding codes; no corpus of real rejected packages | `64` | R0, NOT MEASURED (no real rejected corpus) | | APPROVED 2026-10-04 |
| `visual_assets.store.intake.validator` | `UNSUPPORTED_LIMITATIONS` | 5 tokens | not a number: a feature-support list (the format/feature decision) | `unsupported:tilemap, unsupported:indexed_color, unsupported:grayscale, unsupported:linked_cels, unsupported:external_reference` | R0, NOT MEASURED | | APPROVED 2026-10-04 |
| `visual_assets.store.intake.aseprite` | `MAX_PALETTE_ENTRIES` | 65536 | the Aseprite format's own 16-bit ceiling; the walk is bounded by file length | `65536` | R0, structural | | APPROVED 2026-10-04 |
| `visual_assets.store.readmodel` | `DEFAULT_LIMIT` | 50 | read-model page size; no consumer yet | `50` | R0, NOT MEASURED | | APPROVED 2026-10-04 |
| `visual_assets.store.readmodel` | `MAX_LIMIT` | 200 | read-model page size; no consumer yet | `200` | R0, NOT MEASURED | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_DIM` | 128 | same as the store's `MAX_DIM` (kept equal) | `128` | R1 conflicts with the 2 s line (F3): kept | F3 | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_PIXELS_PER_OP` | 4096 | a 4096-pixel op inside a call of 8192: 0.139 s | `4096` | R1 | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_PIXELS_PER_CALL` | 8192 | apply_ops with 8192 noise pixels on a 128 px sprite: 0.139 s | `8192` | R1 | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_OPS` | 256 | apply_ops with 256 rect ops on a 128 px sprite: 0.082 s | `256` | R1 | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_REFS` | 8 | stamp sources per batch; no data | `8` | R0, NOT MEASURED | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_FRAMES` | 16 | 16 frames of noise at 128 px: 889025 B source (over `MAX_SOURCE_BYTES`) | `16` | R0 | F2 | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_PALETTE` | 64 | set_palette entries; no data | `64` | R0, NOT MEASURED | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_REGION` | 32 | no data | `32` | R0, NOT MEASURED | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_SCALE` | 16 | the drawing tools' maximum preview scale: render 0.258 s at 128 px | `16` | R1 | F6 | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_DURATION_MS` | 10000 | frame duration cap; no data | `10000` | R0, NOT MEASURED | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `JOB_TIMEOUT_S` | 30 | slowest measured Aseprite job (a 128 px scale-16 render): 0.258 s; the slowest store operation, adopt of a 128 px noise source, 1.867 s, most of it the Python decode (0.543 s each, about three per adopt) | `30` | R1 (more than 100x the slowest job) | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_REVISIONS` | 9999 | revision-name width (`r0001`..`r9999`); structural | `9999` | R0, structural | | APPROVED 2026-10-04 |
| `visual_assets.drawing.config` | `MAX_FILE_BYTES` | 8388608 | largest measured source: 889025 B | `8388608` | R1 (9x) | | APPROVED 2026-10-04 |

### Unset

None. The retention row, the last one, was approved on 2026-10-04 (`MAX_UNADOPTED_INTAKE_AGE_DAYS` above): `gc` clean-up is age-based on the LOCAL quarantine and review dirs only and never deletes a tracked object or record.

## Measured operation times (128 px noise source, scale 8 preview)

| Operation | 16 px | 128 px |
|---|---|---|
| Aseprite render, scale 8 | 0.034 s | 0.083 s |
| Aseprite render, scale 16 | 0.041 s | 0.258 s |
| `review` (store render + compare) | 0.084 s | 1.293 s |
| `adopt` (re-render + compare + write) | 0.077 s | 1.867 s |
| `build` (export) | 0.044 s | 0.063 s |

`review` and `adopt` at 128 px are dominated by the pure-Python PNG decode of the 1024 px preview, not by Aseprite (render 0.083 s): one
decode + pixels-v1 hash of that real preview took 0.543 s, and `adopt` decodes about three times. The decode, not Aseprite, is what
the dimension bounds protect.

## Rulings and flags

The planner's rulings (2026-10-03) on the first draft of this record, and what changed.

- **F1 + F5: resolved, a defect and wider than the registry.** The invariant is: *every record any writer can produce under the contract bounds is readable by every reader.* Before, `parse_record`, `canonical_json` and every read site used `MAX_RECORD_BYTES` (64 KiB) for all record types, so the registry (about 207 keys), a `ReleaseCandidateManifest` (about 400 entries) and an `IntakeResult` with 4-byte text (68483 B) were legal but unreadable or unwritable. Fix: each record class names its bound (`StoreRecord.size_bound`; `record_bound(cls)` is the one lookup, used by the writer and every reader), the registry uses `MAX_REGISTRY_BYTES`, the manifest uses the new `MAX_MANIFEST_BYTES`, `MAX_RECORD_BYTES` is raised to 131072, and `MAX_VISUAL_KEYS` is lowered to 1024 by R3 (registry load cost). Guard: `tests/visual_assets/store/unit/test_record_bounds.py` builds the maximum legal instance of every record type and reads it back through the real path. Residual, stated plainly: a registry is bounded by bytes first; keys wider than the realistic shape (up to 8 axes x 64 values, 7471 B per key) reach `MAX_REGISTRY_BYTES` before `MAX_VISUAL_KEYS`, which is intended for a hand-edited file.
- **F2: `MAX_SOURCE_BYTES` stays 102400.** R1 waived (see the row). The dense 16-frame case (889025 B) is a known limit.
- **F3: accepted, 128 / 1024 kept.** Finding: **the pure-Python PNG decoder's speed limits the dimension bounds; optimize it before raising them** (2048 px previews decode in 7.87 s). No ticket filed.
- **F4: resolved, the name is split.** `MAX_DECODED_BYTES` is the decoded-size bound in `pixels.py` only; `MAX_PNG_FILE_BYTES` is the file-size bound at the five read sites. A test asserts the worst legal PNG is readable and decodable, and that no other module uses `MAX_DECODED_BYTES`.
- **F5: resolved with F1** (`MAX_RECORD_BYTES` 131072).
- **F6: kept.** The store renders only at a preview's scale, and a preview is bounded by `MAX_PREVIEW_DIM`, so scale 16 of a 128 px sprite is refused upstream, consistently. Scale 16 works only for sprites up to 64 px.
