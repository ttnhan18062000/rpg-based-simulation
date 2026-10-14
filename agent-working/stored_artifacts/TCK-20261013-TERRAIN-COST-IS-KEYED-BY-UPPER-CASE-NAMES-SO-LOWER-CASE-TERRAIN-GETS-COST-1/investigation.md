---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1
date: 2026-10-14
tags: []
---

# Investigation: TCK-20261013-TERRAIN-COST-IS-KEYED-BY-UPPER-CASE-NAMES-SO-LOWER-CASE-TERRAIN-GETS-COST-1

Compiled content terrain is lower-case, the table was upper-case, so forest, swamp, mountain and road all cost 1.0. The only reader is the readiness pre-check at legality.py:190; movement spends no readiness, so urban_political (plain and road) is unaffected, while frontier_living_world (forest, cave, swamp) changes: pre-check refusals 2913 to 6371 over five seeds. All 24 corpus worlds compile with exact-match ids.
