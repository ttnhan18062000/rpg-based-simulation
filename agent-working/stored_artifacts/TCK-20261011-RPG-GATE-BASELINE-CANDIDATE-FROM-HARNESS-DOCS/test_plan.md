---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS
phase: done
date: 2026-10-11
tags: [testing, regression, simulation-quality]
---

# TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS: test_plan

tests/unit/tools/test_rpg_gate_candidate.py (17): round trip to an all-pass report; statistics and thresholds on rows; byte-identical output; refusals (no-data, matrix mismatch, sha/hash/ticks, seeds, thresholds, missing k/floor, absent row); owned fail omitted and recorded; unowned, expired and wrong-state owners refuse; lint rejects a listed row still in metrics; evidence-only refused; CLI writes or refuses without writing. tests/static/test_ci_rpg_gate_workflow_shape.py: the candidate step is best-effort, labelled, inside report/.
