---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION
artifact_type: test_plan
tags: [architecture, testing, live-map]
---

# Test plan — TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION

Seven re-pointed guards plus one new test (`test_the_committed_catalog_holds_exactly_one_set_adoption_and_it_is_the_owners_terrain_v1_decision`: exact adoption id, hash, timestamp, approver, 31 entries each pointing at a committed draft, 34 adoptions by source name). Full: `tests/visual_assets` 1543 passed (2 GB cap); catalog `verify` and `draft verify` clean.
Byte-for-byte: `adoption_files_sha256.txt` lists 156 files; after the commit every committed blob equals its hash.
