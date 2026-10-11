---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS
phase: done
date: 2026-10-11
tags: [testing, regression]
---

# Test plan

## Proof Plan
- level: unit
- proof kind: behaviour tests of pure functions plus CLI exit codes
- oracle source: the epic's rules (dual reference, staleness by date / harness hash / config, refused re-baselines, immutability)
- expected effect: every AC2 case passes; a stale baseline is never reported current; no existing file is modified
- selected commands: `pytest tests/unit/tools/test_rpg_gate_baseline.py`
