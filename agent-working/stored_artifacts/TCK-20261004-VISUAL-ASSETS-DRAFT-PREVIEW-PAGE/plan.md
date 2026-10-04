---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE
artifact_type: plan
tags: [architecture, live-map, testing]
---

# Plan — TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE

1. `DraftPreviewManifest` and `draft export` (verify first, copy previews byte for byte, deterministic, new directory).
2. TS parser mirroring it, adapter to the unchanged loader/resolver, the code-to-key table, a deterministic sample map, the page and folder picker.
3. Fixture generator, tests (hash pin, mutual unparseability, coverage, drawing), isolation, docs, one screenshot.
