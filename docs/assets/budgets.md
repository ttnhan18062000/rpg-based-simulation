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
**Status of every row: `PROPOSED`.** The numbers are not decisions until the owner approves them in PR review; the planner then
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
| `visual_assets.store.config` | `MAX_RECORD_BYTES` | 65536 | largest legal intake_result: 19331 B ASCII, 68483 B with 4-byte UTF-8 text; handoff package 7057 B / 19345 B; fixtures <= 985 B | `65536` | R1 (2x of 19331 = 38662) | F1, F5 | PROPOSED |
| `visual_assets.store.config` | `MAX_REGISTRY_BYTES` | 1048576 | 4096 no-axis keys = 728538 B, loads in 2.62 s; 4096 two-axis keys = 1371610 B (over); only about 207 two-axis keys fit `MAX_RECORD_BYTES` | `1048576` | R0 (R3 would give about 550 KB, unreachable) | F1 | PROPOSED |
| `visual_assets.store.config` | `MAX_VISUAL_KEYS` | 4096 | 4096 keys, 1024 aliases: 2.62 s, 36 MiB peak (over the 2 s line); only about 207 two-axis keys are reachable | `4096` | R0 | F1 | PROPOSED |
| `visual_assets.store.config` | `MAX_ALIASES` | 1024 | included in the 4096-key load above, not separated | `1024` | R0, NOT MEASURED separately | F1 | PROPOSED |
| `visual_assets.store.config` | `MAX_SOURCE_BYTES` | 102400 | 128 px, 1 frame, noise: 55764 B (flat: 759 B); 16 frames of noise: 889025 B | `114688` | R2 + R4 (2x of 55764 = 111528, rounded up to 112 KiB). Reopens D2 | F2 | PROPOSED |
| `visual_assets.store.config` | `MAX_DIM` | 128 | 128 px is the project maximum (1x, not 2x); 256 px would make a scale-8 preview 2048 px | `128` | R1 conflicts with the 2 s line (F3): kept | F3 | PROPOSED |
| `visual_assets.store.config` | `MAX_PREVIEW_BYTES` | 524288 | 128 px noise preview at scale 8: 83797 B; synthetic 1024 px: 41624 B | `524288` | R1 (2x of 83797 = 167594) | | PROPOSED |
| `visual_assets.store.config` | `MAX_PREVIEW_DIM` | 1024 | decode + pixels-v1 of a 1024 px RGBA PNG, Paeth rows (worst): 1.73 s, 17.0 MiB; 1536 px: 5.06 s; 2048 px: 7.87 s, 68 MiB | `1024` | R2 would give 2048 (7.87 s, over 2 s): kept | F3 | PROPOSED |
| `visual_assets.store.config` | `MAX_DECODED_BYTES` | 25165824 | decoding at the bound (2508 px square, Paeth): 13.72 s, 102 MiB; at 1024 px (4195328 B decoded): 1.73 s | `4195328` | R3 (1024 * (1024 * 4 + 1)) | F4 | PROPOSED |
| `visual_assets.store.rendering` | `MAX_RENDER_SCALE` | 16 | Aseprite render of a 128 px noise source: scale 8 0.083 s, scale 16 0.258 s | `16` | R1 (realistic scale is 8) | F6 | PROPOSED |
| `visual_assets.store.contracts.handoff` | `MAX_LIMITATIONS` | 16 | 16 x 256-char limitations = 7057 B ASCII package; no real producer data | `16` | R0, NOT MEASURED (no real producer yet) | | PROPOSED |
| `visual_assets.store.contracts.definitions` | `MAX_AXES` | 8 | widest key (8 axes x 64 values) = 7471 B of YAML; no real registry | `8` | R0, NOT MEASURED (no real catalog yet) | | PROPOSED |
| `visual_assets.store.contracts.definitions` | `MAX_AXIS_VALUES` | 64 | same widest key | `64` | R0, NOT MEASURED (no real catalog yet) | | PROPOSED |
| `visual_assets.store.contracts.intake` | `MAX_FINDINGS` | 64 | 64 x 256-char findings = 19331 B ASCII; the validator has 38 finding codes; no corpus of real rejected packages | `64` | R0, NOT MEASURED (no real rejected corpus) | | PROPOSED |
| `visual_assets.store.intake.validator` | `UNSUPPORTED_LIMITATIONS` | 5 tokens | not a number: a feature-support list (the format/feature decision) | `unsupported:tilemap, unsupported:indexed_color, unsupported:grayscale, unsupported:linked_cels, unsupported:external_reference` | R0, NOT MEASURED | | PROPOSED |
| `visual_assets.store.intake.aseprite` | `MAX_PALETTE_ENTRIES` | 65536 | the Aseprite format's own 16-bit ceiling; the walk is bounded by file length | `65536` | R0, structural | | PROPOSED |
| `visual_assets.store.readmodel` | `DEFAULT_LIMIT` | 50 | read-model page size; no consumer yet | `50` | R0, NOT MEASURED | | PROPOSED |
| `visual_assets.store.readmodel` | `MAX_LIMIT` | 200 | read-model page size; no consumer yet | `200` | R0, NOT MEASURED | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_DIM` | 128 | same as the store's `MAX_DIM` (kept equal) | `128` | R1 conflicts with the 2 s line (F3): kept | F3 | PROPOSED |
| `visual_assets.drawing.config` | `MAX_PIXELS_PER_OP` | 4096 | a 4096-pixel op inside a call of 8192: 0.139 s | `4096` | R1 | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_PIXELS_PER_CALL` | 8192 | apply_ops with 8192 noise pixels on a 128 px sprite: 0.139 s | `8192` | R1 | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_OPS` | 256 | apply_ops with 256 rect ops on a 128 px sprite: 0.082 s | `256` | R1 | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_REFS` | 8 | stamp sources per batch; no data | `8` | R0, NOT MEASURED | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_FRAMES` | 16 | 16 frames of noise at 128 px: 889025 B source (over `MAX_SOURCE_BYTES`) | `16` | R0 | F2 | PROPOSED |
| `visual_assets.drawing.config` | `MAX_PALETTE` | 64 | set_palette entries; no data | `64` | R0, NOT MEASURED | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_REGION` | 32 | no data | `32` | R0, NOT MEASURED | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_SCALE` | 16 | the drawing tools' maximum preview scale: render 0.258 s at 128 px | `16` | R1 | F6 | PROPOSED |
| `visual_assets.drawing.config` | `MAX_DURATION_MS` | 10000 | frame duration cap; no data | `10000` | R0, NOT MEASURED | | PROPOSED |
| `visual_assets.drawing.config` | `JOB_TIMEOUT_S` | 30 | slowest measured Aseprite job (a 128 px scale-16 render): 0.258 s; the slowest store operation, adopt of a 128 px noise source, 1.867 s, most of it the Python decode (0.543 s each, about three per adopt) | `30` | R1 (more than 100x the slowest job) | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_REVISIONS` | 9999 | revision-name width (`r0001`..`r9999`); structural | `9999` | R0, structural | | PROPOSED |
| `visual_assets.drawing.config` | `MAX_FILE_BYTES` | 8388608 | largest measured source: 889025 B | `8388608` | R1 (9x) | | PROPOSED |

### Unset

| Bound | Value | Reason | Status |
|---|---|---|---|
| Retention: age-based quarantine or review clean-up | UNSET | no real catalog yet; `gc` is reachability-only | UNSET |

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

## Flags: rows where the rule gives a silly or conflicting answer

The proposed value for each flagged row is the current value. These need a ruling from the planner or owner.

- **F1: the registry's real capacity is set by `MAX_RECORD_BYTES`, not by the registry bounds.** `load_registry` reads the file (up to `MAX_REGISTRY_BYTES`, 1 MiB) and then parses it with `parse_record`, which refuses input over `MAX_RECORD_BYTES` (64 KiB). Measured with the real configuration: about 207 two-axis keys (373 with no axes) are accepted, so `MAX_VISUAL_KEYS` (4096) and `MAX_REGISTRY_BYTES` (1 MiB) can never be reached, and the 2.62 s load at 4096 keys cannot happen. Applying R3 to the unreachable bounds would be meaningless. The decision: give the registry its own parse bound (a code change), or accept 64 KiB (about 200 keys) as the real limit and lower the other two to match. Not decided here.
- **F2: a full 16-frame animation does not fit `MAX_SOURCE_BYTES`.** Noise at 128 px is 889025 B for 16 frames; the proposed 114688 B holds a dense 128 px sprite with one frame and about 2 frames of noise. Flat sprites are small (2769 B for 16 frames). Real animated art lies between the two and there is no real art to measure. Raising this reopens D2 (no Git LFS).
- **F3: R1/R2 conflict with the 2 s line for dimensions.** The realistic worst case is exactly the current bound (128 px; 1024 px preview), so R2 says "raise to 2x", but a 2048 px preview decodes in 7.87 s, over the 2 s line. Kept. The decoder is the limit (a pure-Python per-byte loop); optimizing it is out of scope and is a finding for the planner.
- **F4: `MAX_DECODED_BYTES` has two jobs.** `pixels.decode_png` uses it as a bound on decoded size; five other call sites (`verify`, `release`, `exporter`, `adoption`, `intake.service`) use it as a bound on the PNG file's own size when reading it. The proposed 4195328 is right for the first and very large for the second (the largest measured PNG file is 228094 B at 2508 px). One name with two meanings is easy to misread; splitting it would be a code change.
- **F5: a legal intake result can exceed `MAX_RECORD_BYTES`.** 64 findings of 256 four-byte characters serialize to 68483 B, so the store could write a record it then refuses to read. Only reachable with adversarial text; the realistic worst case (ASCII) is 19331 B. Left as is.
- **F6: scale 16 of a 128 px sprite cannot pass `MAX_PREVIEW_DIM`.** `MAX_RENDER_SCALE` and the drawing `MAX_SCALE` allow scale 16, but the store refuses a 2048 px render. Scale 16 works only for sprites up to 64 px. Kept; stated here so nobody expects 128 px at scale 16.
