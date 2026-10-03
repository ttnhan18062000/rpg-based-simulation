---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-BUDGETS
artifact_type: test_plan
tags: [performance, testing, mcp]
---

# Test Plan — TCK-20261003-VISUAL-ASSETS-BUDGETS

- Parity test passes on the real tree (every row equals the code; every code bound has a row; no provisional comment).
- Mutants, each must fail naming the row: a changed value (`MAX_PREVIEW_DIM`), a new bound with no row, a deleted row, a row naming a missing attribute, a restored "provisional (U-05)" comment.
- `tests/visual_assets` without Aseprite stays green after `MAX_SOURCE_BYTES` and `MAX_DECODED_BYTES` change.
- `make visual-assets-aseprite-local`: 0 skipped (lowered decoded bound must not break a real render).
- `tests/static`, `tests/architecture`, `tests/docs`.

## Proof Plan

- Level: unit (pure-function checkers over the doc and the module attributes) plus the strict real-Aseprite run.
- Proof kind: executable test plus recorded mutants.
- Oracle source: `docs/assets/budgets.md` (the Proposed column) against the module attributes.
- Expected effect: the parity test passes on the tree and fails naming the row on each of the five mutants.
- Selected commands: `pytest tests/visual_assets/test_budgets_parity.py`; `make visual-assets-aseprite-local`; `pytest tests/static tests/architecture tests/docs`.
