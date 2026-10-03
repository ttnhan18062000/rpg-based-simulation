---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261001-EPIC-B-SCENARIO-LANE-COST-RECORD
artifact_type: investigation
tags: [testing]
---

# Investigation

Verified through the GitHub Actions API on 2026-10-01 (not taken from the reviewer's figures):

| Head SHA | Run | Scenario lane | Perf / cert / arena |
|---|---|---|---|
| #271 `369acbac3` | 36810173881 | success, 51 s | skipped |
| #271 `a9646c9de` | 36812211906 | success, 50 s | skipped |
| #271 `e75ff2e77` | 36813602119 (workflow failure in `API / tools / logging`) | success, 50 s | skipped |
| #271 `248372a26` | 36815393173 | success, 34 s | skipped |
| #275 `e147d7514` | 36837239759 | success, 48 s | skipped |
| #275 `d15ff2163` | 36840523273 | success, 47 s | skipped |

Correction note: a first version of this table showed the two #271 rows above as "none". The reviewer found runs for both and they were re-queried by full SHA; the cause of the original empty result is not established. An empty runs query is not evidence of no run.

The reviewer's three figures matched. Routing: #271 final head 0 matched / 3 unknown / 16 irrelevant; #275 0 matched / 6 unknown / 17 irrelevant. Both are tests-only fail-open cases.
