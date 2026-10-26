---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1
artifact_type: investigation
phase: done
date: 2026-10-24
tags: [testing, regression, simulation-quality]
---

# Moved rows on baseline v1 (measured, not yet ruled)

Measured sha 341f700d0 (src identical to e8df8b96d), 81 keys x2 isolated audit_mode runs, `--workers 1`, 162 runs 0 failed, every pair identical (simq_reanchor accepted all 81). Committed anchors = main at c6ff5149f (the #531 values, plus the 27 held rows at their old values).
Files: `reanchor_table.tsv` (all 810 rows, tool output), `ruling_table.tsv` (the 536 moved rows; columns kind and held_in_531 added).
Moved = not in band before under audit_mode: 536 of 810 rows, all 81 keys; 274 rows unmoved. All 27 rows held in #531 moved (held_in_531 = held).
Kinds: to-no-data = ok anchor, now no-data (status change, rpg fix (b) min-event rule); grade-up/down = grade changed; score-only = same grade, score outside tolerance.

| pillar | to-no-data | grade-up | grade-down | score-only | total |
|---|---|---|---|---|---|
| AGENCY | 49 | 2 | 0 | 1 | 52 |
| COGNITION | 60 | 5 | 2 | 3 | 70 |
| COMBAT | 41 | 1 | 0 | 22 | 64 |
| ECONOMY | 16 | 3 | 1 | 16 | 36 |
| FACTION | 69 | 1 | 0 | 2 | 72 |
| INFORMATION | 36 | 18 | 5 | 19 | 78 |
| NARRATIVE | 16 | 3 | 3 | 13 | 35 |
| PROGRESSION | 31 | 7 | 4 | 12 | 54 |
| SOCIAL | 11 | 10 | 1 | 32 | 54 |
| WORLD | 9 | 1 | 0 | 11 | 21 |
| all | 338 | 51 | 16 | 131 | 536 |

No determinism findings (no non-identical pair). SCORE_TOLERANCE_OVERRIDES untouched. Causes are not attributed here: that is the ruling.

to-no-data rows (338): 338 have event_count < min_events with reason below_min_events, identical on both reps (columns event_count, min_events, reason come from each run's quality_report.json pillar); exceptions: 0

NARRATIVE (ruled by rpg-planner via testing-planner, 2026-10-24): the 35 moved NARRATIVE rows are marked kind=narrative-retired, re-anchored to the v1 values with the note "retired under D77, removed by TCK-20261014-SIMQ-PILLARS-COMPUTED-FROM-TYPED-RECORDS-WITH-SEED-SPREAD-D77", and are not ruled as behaviour. Kind counts now: {'grade-down': 13, 'narrative-retired': 35, 'grade-up': 48, 'score-only': 118, 'to-no-data': 322}. The 16 NARRATIVE to-no-data rows keep their event_count/min_events/reason columns; they are counted under narrative-retired, not to-no-data (322 to-no-data left).

FINAL (owner confirmed 2026-10-26, issue #715 comment 6400785924): 500 re-anchored (322 fix (b), 35 NARRATIVE D77, 36 INFORMATION, 107 per-row cited) and 36 held under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE (`exclude.tsv`). The counts above this line are the 2026-10-24 first cut (505 / 31).
