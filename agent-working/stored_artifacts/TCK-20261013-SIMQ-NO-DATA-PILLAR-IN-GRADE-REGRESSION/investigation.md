---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION
phase: done
date: 2026-10-14
tags: [testing, regression, simulation-quality]
---

# Investigation

Pillar-default reads found in the SimQ tests (grade "C" and score 0.0 defaults, and no-default reads that a null grade or score would break):
- `test_grade_regression.py`: L250 `actual_scores.get(pillar, 0.0)`; L332, L379, L432, L435, L473, L476 `actual_grades.get(pillar, "C")`; `_extract_pillar_grades/_scores` (`data["grade"]`, `data["normalized_score"]`); `pillars["COGNITION"]["grade"] == "S"`; the schema guard.
- `test_corpus_diversity.py`: `_anchor()` reads and the 14 guards comparing `snap.grade` / `result["grade"]`.
- `simq_reanchor.py` L112-124.
- `tools/evaluate_simq.py` `_extract_pillar_grades`, `anchor_grades`.

The overall is not anchored in the fixture (810 = 81 x 10 pillar rows). Reports today have no `status` field (AC6). The #531 stored rows give an end-to-end regression oracle for the re-anchor tool.
