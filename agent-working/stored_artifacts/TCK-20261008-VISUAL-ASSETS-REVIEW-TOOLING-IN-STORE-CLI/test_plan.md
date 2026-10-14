---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI
artifact_type: test_plan
date: 2026-10-09
tags: [architecture, testing]
---

# Test plan

- Commit 1: byte-for-byte proof (evaluator JSON x3, review folders x3, fixture `--check` x3) before/after the move; boundary rows with planted violations (review importing a gate layer or build, drawing other than technique, store/drawing importing review); scoped suites; vitest.
- Commit 2: `test_review_cli.py` (generic evaluation equals the committed rule_result.json byte for byte for the three sets; flag behaviour; unknown set; review-sheets output); `test_review_sheets.py` (+4: one adopt-set for a revising set with NEW/REVISION and drop commands, per-slot for older sets, partial adoption fallback, mode decision); `test_pilot_colour_vision.py` (+2: slot by key and detail, refusal). Mutants A-I.
- Also run `tests/unit/tools` and `tests/tools` (planner's request; they found two child 2 misses).
