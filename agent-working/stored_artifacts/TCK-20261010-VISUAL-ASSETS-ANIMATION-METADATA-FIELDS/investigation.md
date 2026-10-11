---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation (written at close from the work and the review record)
- `intake/aseprite.read_facts` read only counts. The frame header holds the duration as a WORD at offset 8 (so 0..65535 ms; the design's "over 65535" cannot occur) and the tags chunk (0x2018) holds, per tag, from, to, a direction byte (0..3), a repeat WORD, 10 reserved/colour bytes and a length-prefixed name: 19 bytes minimum per tag. Real Aseprite agrees (a 4-frame sprite with one tag per direction was written and read back through Lua; Lua frame numbers are 1-based, the file's are 0-based).
- All 77 committed `SourceRecord`s are one-frame sources with no tags, so the optional field must be omitted for them (`drop_absent`) to keep every record byte-identical; a test round-trips all of them.
- The test builders wrote only a tag COUNT, so `tags_chunk_of` and per-frame durations were added to them.
- Traps found on the way: the layering test needs the new `animation` store module declared as its own layer; `test_budgets_parity` fails on any `MAX_*` name in code without a budgets row (a later fix of mine added one by accident and had to remove it); `decode_png` keeps its own LRU cache of 4 images.
- Review finding (independent security review, reproduced before fixing): a tag name of unassigned code points is plain-text valid but `repr()` expands each to a 10-character escape, so a quoted finding exceeded the 256-character limit of `IntakeFinding.detail` and `validate` raised. Findings now name a tag by position and `_finding` clamps. Everything else the reviewer tried held: per-read bounds checks (60,000 mutated files), counts, caps, intake-passed-but-adoption-raises (39,041 files), name handling, path traversal in the export.
