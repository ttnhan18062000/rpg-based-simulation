---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP
date: 2026-07-18
tags: [data-quality]
---

# Test Plan — TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP

## Regression Surface (existing tests that must pass)

- `tests/tools/test_ticket_field_values.py` — unaffected by this ticket
  (no code change), must remain green.
- `tests/tools/test_validate_frontmatter.py` — both touched ticket files
  must still pass frontmatter validation after the body-text edit.

## New Tests Required (per AC)

None — this ticket makes no code change, only ticket-body data
corrections. Verification is direct: re-run the real check function against
the full corpus (not a new unit test, since there is no new behavior to
unit-test).

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_ticket_field_values.py -q
python3 tools/validate_frontmatter.py --content-type ticket tickets/done/TCK-20260326-HYSTERESIS.md
python3 tools/validate_frontmatter.py --content-type ticket tickets/done/TCK-20260326-NARRATIVE.md
```

## Anti-Drift Test Guards

Live corpus re-scan (not a pytest test, a direct script run) is the actual
proof this ticket's AC requires: 0 `FAIL` findings from
`check_ticket_field_values` across `tickets/{done,inprogress,todos}/`
after the fix.
