---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP
artifact_type: test_plan
phase: investigate
date: 2026-08-08
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP

## No code change — no new tests

Real, evidenced conclusion: no scorer bug found. Docs-only deliverable, no new `src/` behavior to
test.

## Regression guard

`pytest tests/simulation_quality/test_faction_scorer.py -q` is unrelated; the relevant existing
suite for `CombatScorer` itself (if any exists under `tests/simulation_quality/`) is unaffected
since no code changed — confirmed via `git diff --stat` showing only doc changes for this ticket.
