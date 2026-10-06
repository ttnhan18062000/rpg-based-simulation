---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN
artifact_type: test_plan
tags: [mcp, live-map, testing]
---

# Test plan — TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN

Python: `test_terrainset_fixture.py` (fresh export equals committed, exactly the 34 slots and declared axes, rc-0005 = rc-0004 + 31 on the same registry, forest bytes equal the pilot's); re-pointed by equality: adopted_facts GENERATED/RELEASE_CANDIDATES, store tools stdio (34 artifacts, 5 releases).
Frontend: `mapScene.test.ts` (layout: 23 codes, 3x3 patch each, forest plain/bush/tree; markers; each of the 22 keys missing -> its fill; forest variant fallbacks; borders off/on; missing and corrupt masks; marker order; flat control), `terrainsetDrill.test.ts` (rollback pairs, recall, no mixed snapshot), isolation count 13 -> 47 on purpose.
Browser: `map.capture.ts` x 4 clients = 16 passed. All on commit 2c793286f: pytest 1548, vitest 230, tsc/eslint clean, AM5-S PASS, verify store ok / drafts ok.
