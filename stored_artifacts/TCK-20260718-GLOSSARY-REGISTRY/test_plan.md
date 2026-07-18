---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-REGISTRY
artifact_type: test_plan
tags: [dashboard, observability, reporting]
---

# Test Plan — TCK-20260718-GLOSSARY-REGISTRY

## Regression Surface
None — new module, no existing consumers yet (this ticket only builds the registry; the API
endpoint that will consume it is a separate, later ticket).

## New Tests Required
- I/O: missing-file returns empty, reads entries, skips blank lines, raises on duplicate term key.
- `add_term`: appends and returns entry; rejects invalid category; rejects blank/whitespace-only
  description; rejects duplicate term (append-only); existing entries unchanged after further
  adds; mixed-case and underscore terms accepted (no canonical-form rejection).
- `GLOSSARY_CATEGORIES` is exactly the documented fixed 7-value set.
- Real-registry tests (no `root` override): every `ticket_field_values.py` canonical value
  (`TIER_VALUES | PRIORITY_VALUES | WORKFLOW_STATUS_VALUES`) has a glossary entry; every real
  entry has a non-blank description and a valid category.

## Scoped Pytest Commands
```
python3 -m pytest tests/tools/test_glossary_registry.py -q
```

## Anti-Drift Test Guards
`test_add_term_no_canonical_form_check_mixed_case_and_underscores_allowed` — guards against a
future edit accidentally importing/reapplying `tag_registry.py`'s canonical-form rule onto this
module, which would break real terms like `DONE`/`P0`/`dod_condition_failed`.
