---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS
artifact_type: test_plan
tags: [architecture, testing, security]
---

# Test plan

- Unit (`store/unit/test_slice_metadata.py`): reads plain/9-slice/pivot exactly; 20 planted bad cases each with its code; signed values; non-UTF-8 name; contract rules (mixed centre/pivot, canvas, frames, order, duplicates); intake quarantine; hostile name never in a finding; chunk cut at every length; lying key count (bound+1, 2, 0xFFFFFFFF); name length past chunk; 2000 slice chunks stop at the bound, fast; worst-case record size; every committed record byte-identical and derives no slices; adoption stores slices and leaves a plain source unchanged, `verify` clean.
- Mutants (parser lines removed one at a time): each bound/geometry check, the key-length check, centre origin; one survived (negative centre origin) and got a test.
- Real Aseprite: `test_real_aseprite.py` slice parity (local only).
- Whole `tests/visual_assets` + docs + static run after the change (proof-record staleness test is expected red until child 4 re-runs it).

- Multi-key layout is covered by the synthetic builder only (the Aseprite Lua API makes frame-0 keys); the builder shares the file layout with the parser and the single-key real-file test proves that layout.
