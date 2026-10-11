---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS
phase: done
date: 2026-10-11
tags: [testing, regression]
---

# Plan
1. `rpg_gate_baseline.py`: schema, lint, loader, dual reference, staleness, re-baseline, CLI. Pure functions over dicts; no metric id named.
2. Unit tests for each AC2 case.
3. Reference doc and docstring for AC1.
Scope guard: no baseline content, config or stop-line values (rpg's); no known_reds.py change (child 1 is in review).
