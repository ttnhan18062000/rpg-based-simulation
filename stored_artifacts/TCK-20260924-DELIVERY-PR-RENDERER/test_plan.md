---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260924-DELIVERY-PR-RENDERER
date: 2026-09-24
tags: [delivery, ai, documentation]
---

# Test Plan — TCK-20260924-DELIVERY-PR-RENDERER

`tests/tools/test_delivery_pr_render.py`, one test per Acceptance Criterion (AC1–AC10) as listed in
plan.md's Tests section, plus:

## Regression-prone paths
- `test_ticket_found_across_directories` (Assumption 4): a fixture ticket file under a `done/`-like
  subdirectory is still discovered by `find_ticket_file`.
- `test_scope_tie_break_deterministic_and_reported`: two tickets with different layers, equal count
  → tie warning present, scope resolves to the first-discovered ticket's layer.
- `test_why_section_uses_first_paragraph_only`: a multi-paragraph Request Summary fixture renders
  only its first paragraph.
- `test_no_write_side_effect`: `git status --short` unchanged after a `render()` call (mirrors
  `test_delivery_pr_status.py`'s equivalent).

## Full regression check
`pytest tests/tools/ -m "not slow"` after the new test file passes in isolation.

## Recorded in `## Test Summary` once run
Exact command(s) and pass/fail counts.
