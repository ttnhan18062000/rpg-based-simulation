---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1
artifact_type: plan
phase: done
date: 2026-10-24
tags: [testing, regression, simulation-quality]
---

# Plan

1. Run every anchored key twice, isolated, `--audit-mode`, `--workers 1`, with `tools/test_architecture/simq_audit_rows.py`, from a detached worktree pinned at 341f700d0 (baseline v1; src identical to e8df8b96d).
2. `simq_reanchor` builds the moved-rows table; rpg-planner rules row by row (2026-10-24).
3. Commit the re-anchored fixture from a main-based branch: `simq_reanchor --exclude` keeps the 36 held rows at their committed anchors; `SCORE_TOLERANCE_OVERRIDES` stays empty.
4. `slow_known_reds.yaml`: retire the 11 family entries and the corpus catch-all; add 12 entries for the held keys under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE.
5. Update the two tests that pinned the old fixture and registry; close the four family tickets with pointers.
