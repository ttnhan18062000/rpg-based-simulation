---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN
phase: done
date: 2026-10-11
tags: [testing, regression, simulation-quality]
---

# Test plan

## Proof Plan
- level: unit from fixture documents, plus a CLI test
- proof kind: one test per state and per rule, including both boundary cases of the k*SE AND floor rule
- oracle source: the ticket's acceptance criteria and the metric contract
- expected effect: each fixture lands in exactly the expected state; the verdict is red only for an unowned or expired fail or an unstable metric
- selected commands: `pytest tests/unit/tools/test_rpg_gate_report.py tests/unit/tools/test_rpg_gate_baseline.py tests/unit/tools/test_known_reds.py`
