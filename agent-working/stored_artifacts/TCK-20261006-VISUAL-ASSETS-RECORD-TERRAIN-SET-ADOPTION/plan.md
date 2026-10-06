---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION
artifact_type: plan
tags: [architecture, testing, live-map]
---

# Plan — TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION

1. Hash the 156 untracked files `adopt-set` wrote (adoption_files_sha256.txt) and commit them unchanged; compare the committed blobs to the hashes afterwards.
2. `tests/visual_assets/adopted_facts.py`: one module of exact facts (set adoption id, draft set hash, timestamp, 34 sources by name, counts); re-point the seven guards to it with equality only.
3. Docs: store_contract, fallback_safety, pilot_terrain_key say what is adopted and that no release candidate covers the 31 slots. 4. Full suite, `verify`, `draft verify`.
