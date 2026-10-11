---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation
All 70 committed artifact PNGs carry only IHDR, sRGB, IDAT, IEND (no tIME or text), so the allowlist (plus PLTE, tRNS, gAMA) fits real data. `export_runtime` copies the stored PNG bytes, so export-twice identity follows; the rebuild test is what proves the stored bytes themselves are reproducible. A rebuilt file is named by its pixel hash, so existence of the file means the pixels match; bytes are then compared. Aseprite 1.3.18.6 rebuilt all 70 byte-identically.
