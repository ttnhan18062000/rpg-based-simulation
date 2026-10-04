---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET
artifact_type: investigation
tags: [architecture, live-map, testing]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET

- A registry edit changes `registry_hash`, which invalidates export of earlier candidates by design (`registry_mismatch`).
- A draft entry needs a PASSED intake and `adopt-set` refuses already-held slots, so adopted art can only be shown by reference.
- `apply_ops` limits a stamp batch to 8 distinct sources; the contact sheets are built in batches.

## Style note
One palette family derived from each terrain's Live Map fill (ramp d2 < d1 < base < l1 < l2), light from the top-left, all textures periodic mod 16 so tiles repeat seamlessly, a few named accents (berries, embers, moss, reeds, glow), 4 to 7 colours per tile. See the ticket's Implementation Notes and `tile_generator.py`.
