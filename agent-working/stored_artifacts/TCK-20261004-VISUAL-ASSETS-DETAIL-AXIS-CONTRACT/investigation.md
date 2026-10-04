---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT
artifact_type: investigation
tags: [architecture, determinism, mcp]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT

- Re-checked the ticket against the tree: no disagreement except the bounds (see the ticket's Implementation Notes). `ReleaseCandidateManifest` had no sortedness rule before; the new one only constrains new writers (the committed `rc-0001` is sorted).
- Canonical JSON writes `None` as `null`, which would change every committed record and fixture byte for byte; hence omit-when-absent serializers instead of a version bump.
- `verify` cannot require a detail value on an entry for a key that now declares an axis, because a candidate that predates the declaration is legitimate history.
