---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT
artifact_type: investigation
tags: [architecture, determinism, mcp]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT

- Ticket 1 keyed `snapshot.entries` by `slotKey`, so the plain key does not resolve for a key with an axis; the detail branch is chosen by `snapshot.details.has(key)`.
- A declared value with no art has no entry; mapping that to `unknown_key` would be wrong (the key is known), so it is `missing_image`, and the family is taken from any of the key's slots.
- `Math.imul(h ^ byte, prime) >>> 0` gives exact 32-bit FNV-1a; the published vectors confirm it.
