---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation: slices in the runtime export

- The only scale class is x1 (`exportconfig` refuses others), but the contract is scale-generic. Scale is taken from the export config by the artifact id's scale class and CROSS-CHECKED against the artifact record's width and height (= source size x scale); either disagreeing refuses (`slices_scale_unresolved`).
- Mirrors `store/animation.py`: newest source revision found from the artifact file names; entries without slices omitted; manifest untouched.
- Layering: `slices` now reads `records`; `runtime_export` may import `slices` and `build` (export config only).
