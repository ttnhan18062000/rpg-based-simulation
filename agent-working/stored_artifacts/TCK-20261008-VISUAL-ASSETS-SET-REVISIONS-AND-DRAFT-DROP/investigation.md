---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP
artifact_type: investigation
date: 2026-10-09
tags: [architecture, testing]
---

# Investigation

- `setadoption.py` always called `adoption.new_source_asset`; `drafts.keep` refused an existing source id; there was no drop.
- Per-slot `adopt --parent` uses `_lineage(source, new=False, parent)`; `check_slot` only excludes the source's own holder, so it never compared the new revision's key and detail with the parent's (the finding).
- `catalogwrite.publish` links files exclusively (`os.link`) and rolls back every earlier file on any failure, so a concurrent adoption between the parent check and the publish collides and nothing stays (tested).
- Widest legal `DraftSet` with `parent_revision` on 256 entries and 8 maximal drops: 127211 B of 131072 (97.1 %).
