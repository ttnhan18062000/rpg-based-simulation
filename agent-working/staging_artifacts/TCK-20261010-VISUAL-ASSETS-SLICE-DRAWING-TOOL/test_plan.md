---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-SLICE-DRAWING-TOOL
artifact_type: test_plan
tags: [architecture, testing, security]
---

# Test plan

Unit (no Aseprite): op validation table (about 45 bad shapes incl. nested extra keys), limit parity, per-batch cap. Real Aseprite: make 9-slice and pivot slices, inspect + parser agree, single key on a multi-frame sprite, replace semantics, limit across batches, outside the canvas refused with no revision, shrink under a slice (same batch and pre-existing) refused atomically, handoff declares/omits the count, full path drawn -> handoff -> intake -> review -> adoption with SourceRecord equal to the request, declared 1 or 3 vs parsed 2 quarantined. Store unit: mismatch both directions, absent accepted, package without the field byte-identical. Mutants: final-canvas check, replace, centre rule, intake count check caught; per-op limit and the Lua pivot edge are equivalent mutants (the final check and the Python pre-check cover them).
