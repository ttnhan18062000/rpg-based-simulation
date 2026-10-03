---
ticket: TCK-20260627-P3A-DEFERRED-EPICS
phase: Test
date: 2026-06-28
---

# Test Plan — TCK-20260627-P3A-DEFERRED-EPICS

## Regression Surface

This is a documentation + ticket-creation ticket. No production code is changed.
The only test surface is `tests/docs/` (doc-existence and structure tests).

Run:
```
pytest tests/docs/ -x -q
```

## New Tests Required

None. No behavior changes; no new production code.

## Scoped Pytest Command

```bash
pytest tests/docs/ -x -q
```

Rationale: doc tests verify that registered docs exist, have valid frontmatter, and
conform to schema. Any new ticket files created under `tickets/todos/` are not doc-tested
(they are not in `docs/REGISTRY.yaml`), so no new tests are needed.

## Anti-Drift Test Guards

- If new epic tickets are added to `docs/REGISTRY.yaml`, run `make knowledge-index-update`
  to keep the search index current.
- Verify `tickets/working_log.csv` is appended (not inserted) at the bottom.
- Verify `tickets/todos/` does not contain a stale copy of this ticket after finalize.
