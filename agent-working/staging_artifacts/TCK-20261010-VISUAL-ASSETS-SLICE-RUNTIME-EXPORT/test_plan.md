---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan
End to end at x1 (values equal the file's, no flag no file, other outputs byte-identical, twice identical, source without slices omitted); scaling against hand-computed values with a patched scale (x3); unresolvable scale (missing class, wrong factor, width-only and height-only disagreement) refused, no output and no temp dir; CLI flag off by default; empty release. Mutants: scale not applied to rect/centre/pivot, width check, height check, scale-None check, omit-no-slices: all caught.
