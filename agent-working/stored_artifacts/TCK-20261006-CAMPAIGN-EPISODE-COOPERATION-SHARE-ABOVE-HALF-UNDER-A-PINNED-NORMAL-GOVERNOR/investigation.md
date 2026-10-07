---
status: active
layer: testing
authority: P3
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR
artifact_type: investigation
tags: [engine, combat]
---

# Investigation

Share of `cooperation_event` in the event stream, NORMAL pin, 70 ticks, the test's own manifest (the `episode` fixture replicated per seed), two identical runs each, before (`f99cb0c6c`) and after the AGENCY-07 gate:
- seed 42: 797 of 1512 = 0.5271 to 839 of 1691 = 0.4962 (margin 0.0038 under the threshold)
- seed 1337: 635 of 1375 = 0.4618 to 451 of 1266 = 0.3562
- pooled: 1432 of 2887 = 0.4960 to 1290 of 2957 = 0.4363

Cooperation events rose while the total grew faster, so the share fell because entities that no longer retreat on sight engage and pursue (more non-cooperation events), not because cooperation shrank. The earlier doubling of the cooperation count (459 to 926) is not explained by this. The commit range where the share crossed 0.5 was never isolated.
