---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-RELEASE-BYTE-REPRODUCIBILITY
artifact_type: plan
tags: [architecture, testing]
---

# Plan
One test module, `tests/visual_assets/test_release_byte_reproducibility.py`, no product code. Local: rebuild rc-0008 in a temp copy of the store (sources, provenance, definitions, build-config, STORE_FORMAT) with the real renderer, compare PNG bytes with the committed ones, verdict per entry. CI: export-runtime twice, tree hash equal; chunk allowlist over exports and committed PNGs; planted tIME/tEXt/iTXt/zTXt fail.

## Proof Plan
- Rebuild of rc-0008: 70 of 70 IDENTICAL (Aseprite 1.3.18.6, 2026-10-10, strict mode `VISUAL_ASSETS_REQUIRE_ASEPRITE=1`, 10 passed).
- The check can fail: a copy of the stored artifacts with one PNG re-encoded (extra tEXt, same pixels) gives BYTES_DIFFER_PIXELS_MATCH and a deleted one STORED_MISSING; planted chunks fail the allowlist; a one-byte-different export changes the tree hash.
- Verdict design for byte drift (planner to confirm): pass with a warning that names entries and the Aseprite version.
