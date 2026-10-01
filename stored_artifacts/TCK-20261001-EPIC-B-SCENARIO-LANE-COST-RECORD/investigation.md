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
| #271 `a9646c9de` | none | none | none |
| #271 `e75ff2e77` | none | none | none |
| #271 `248372a26` | 36815393173 | success, 34 s | skipped |
| #275 `e147d7514` | 36837239759 | success, 48 s | skipped |

The reviewer's three figures matched. Routing: #271 final head 0 matched / 3 unknown / 16 irrelevant; #275 0 matched / 6 unknown / 17 irrelevant. Both are tests-only fail-open cases.
