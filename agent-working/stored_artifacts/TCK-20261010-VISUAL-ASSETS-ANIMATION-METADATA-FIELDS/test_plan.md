---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan (as executed)
- Parser: durations and tags read exactly as written; a one-frame source derives no animation; Aseprite's direction order maps to the contract.
- 11 planted bad cases, each quarantined with its own code (zero duration, tag past the last frame, from after to, tag outside a one-frame source, 17 frames, 17 tags, duplicate, empty, over-long and control-character names, unknown direction) plus a non-UTF-8 name; intake quarantines the candidate.
- Hostile bytes: the tags chunk claimed at every shorter length, declared counts of 17, 1000 and 65535 (each under 0.5 s), a name length running past the chunk, 1500 random mutations plus truncations: findings, never exceptions.
- Contract: 9 planted violations refused. Corpus: every committed SourceRecord byte-identical, every committed source reads with no new finding.
- End to end: a 4-frame fixture adopted, then `export-runtime --animation` equals the values written into the file; with no flag there is no file and the manifest and every PNG are byte-identical.
- Real Aseprite oracle (strict run). Security regression: 4 cases that fail with the fix reverted.
- Regression: the whole `tests/visual_assets` suite after every fix, plus docs, static, architecture and tools lanes.
