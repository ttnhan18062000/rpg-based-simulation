---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS
phase: done
date: 2026-10-11
tags: [testing, regression]
---

# Investigation
- Convention: `tests/mutation/baselines/*_vN.json` is one file per version with provenance and a `supersedes` pointer; reused as `rpg_gate_vN.json`.
- No rpg config or stop-line definition exists yet. R1/R2 stop lines are named in the metric-set v1 draft only; the config shape here is a proposal for rpg-planner to confirm.
- Choices: stale_after stored absolutely in the file (so a baseline's staleness does not depend on a config change); before/after computed, not hand-written; unknown harness hash fails closed; first baseline needs no citation.
