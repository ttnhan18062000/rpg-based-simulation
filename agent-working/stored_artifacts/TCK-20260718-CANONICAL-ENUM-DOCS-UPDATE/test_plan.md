---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE
date: 2026-07-18
tags: [documentation, claude-md]
---

# Test Plan — TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE

## Regression Surface (existing tests that must pass)

- `tests/tools/test_done_checker_static.py`, `test_ticket_field_values.py`,
  `test_layer_registry.py`, `test_validate_frontmatter.py` — unaffected by
  this ticket (documentation-only), must remain green as a regression
  guard.

## New Tests Required (per AC)

None — pure documentation/agent-instruction text changes, no new behavior
to unit-test.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_done_checker_static.py tests/tools/test_ticket_field_values.py tests/tools/test_layer_registry.py tests/tools/test_validate_frontmatter.py -q
node --check .claude/workflows/create-tickets.js
node --check .claude/workflows/simq-audit.js
node --check .claude/workflows/implement-ticket.js
python3 tools/validate_frontmatter.py --content-type doc docs/observability/agent_ops_dashboard_contract.md
python3 tools/validate_frontmatter.py --content-type doc docs/guides/agent_ops_dashboard.md
```

## Anti-Drift Test Guards

A direct grep for `LAYER_VALUES` and non-P3 `P0 | P1 | P2` across
`.claude/` and `docs/` (excluding the correctly-P0-P2-scaled parity-ledger
references) is the actual proof this ticket's completeness AC requires —
not a pytest test, a direct verification pass.
