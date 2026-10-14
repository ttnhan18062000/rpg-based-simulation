---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-RECORD-ICON-OWNER-FIXES-ADOPTION
artifact_type: investigation
tags: [architecture, testing, documentation]
---

# Investigation

- Adoptions of revisions add adoptions and intakes but no source asset: 70 sources, 77 adoptions, 77 revisions (`store list --kind source` counts revisions).
- Six tests failed before the guard edits, all counts: test_store_tools_stdio, test_adoption, test_registry, test_catalog_integrity, test_terrain_draft_set, plus the README test (the generator now correctly says ALREADY ADOPTED).
- Fixtures `icondraft_fixes`, `icondraft_v2` and `icondraft` stay identical (`--check`).
