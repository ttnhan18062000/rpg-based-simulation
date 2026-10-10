---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT
artifact_type: plan
tags: [architecture, testing]
---

# Plan
1. `contracts/slices.py`: RuntimeSliceKey (flat), RuntimeSlice, RuntimeSliceEntry, RuntimeSlices (MAX_MANIFEST_BYTES).
2. `store/slices.py`: `runtime_slices_bytes(entries, scales=)`, `SliceScaleError`.
3. `runtime_export.export_runtime(slices=)`, CLI `--slices`, BuildError `slices_scale_unresolved`.
4. `store_contract.md` section; boundaries entries; tests.
