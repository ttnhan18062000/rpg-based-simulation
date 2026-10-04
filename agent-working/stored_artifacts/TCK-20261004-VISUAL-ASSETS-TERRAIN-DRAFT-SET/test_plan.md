---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET
artifact_type: test_plan
tags: [architecture, live-map, testing]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET

- [x] `draft verify` clean; every key except forest has a draft; verified in a test on the committed set.
- [x] The page shows the whole set with no missing rows; screenshot stored.
- [x] Catalog `verify` clean; rc-0003 entries equal rc-0002's; guards re-pointed.
- [x] References never reach the DraftSet, `draft verify` or `adopt-set`.

## Proof Plan
- level: contract and catalog integrity (pure Python and vitest), one local browser capture
- proof kind: exact set contents, entry equality between rc-0002 and rc-0003, reference-entry isolation, a colour-vision pair report
- oracle source: the ticket, planner decisions A and B, the page's explicit code-to-key table
- expected effect: a full terrain draft set is reviewable as a whole; nothing is adopted or released
- selected commands: `pytest tests/visual_assets`, `python -m visual_assets.store verify`, `python -m visual_assets.store draft verify`, `npx vitest run src/visualAssets`
