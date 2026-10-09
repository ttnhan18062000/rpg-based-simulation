---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION
artifact_type: test_plan
tags: [architecture, testing, hud]
---

# Test plan — TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION

- `test_icon_set_adoption.py`: the v2 draft set hashes to what the adoption recorded and every entry is adopted with its own source; the set-adoption record's facts (approver, time, hash, 22 entries); the 36 icon sources equal the key set plus v2 sources; no artifact and no candidate covers an icon slot.
- `test_icon_v2_keys.py`: each v2 key adopted exactly once, no artifact, no candidate slot. `test_detail_axis.py`, `test_catalog_integrity.py`, `test_adoption.py`, `test_registry.py` and the stdio store test: counts and sets by equality (70 sources, three set adoptions, 140 intake files).
- Fixture `--check` for both icon fixtures (identical). Whole scoped suites listed in the ticket.
