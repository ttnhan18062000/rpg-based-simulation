---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION
artifact_type: investigation
tags: [architecture, mcp, testing]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION

- `catalogwrite.publish` refuses paths outside the catalog, so drafts need their own writer.
- Every reader parses `provenance/adoptions/*.json` as `AdoptionRecord`; a set record needs its own folder.
- `adopt` needs `package.json` (width/height) and all three staged hashes, so entries keep them.
- DraftSet at 256 maximum-length entries with a `source_hash` is 138887 B; dropping it (bound through the intake result) gives 116359 B.
