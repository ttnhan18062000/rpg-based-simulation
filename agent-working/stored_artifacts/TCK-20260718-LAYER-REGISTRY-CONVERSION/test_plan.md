---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260718-LAYER-REGISTRY-CONVERSION
date: 2026-07-18
tags: [frontmatter, tagging]
---

# Test Plan — TCK-20260718-LAYER-REGISTRY-CONVERSION

## Regression Surface (existing tests that must pass)

- `tests/tools/test_validate_frontmatter.py::TestEnumAntiDrift::test_enum_values_layer`
  — must still pass unchanged (same 19-value equality assertion).
- `tests/tools/test_ticket_field_values.py::test_layer_values_is_imported_not_duplicated`
  — must still pass unchanged (identity check).
- `tests/tools/test_add_frontmatter_tickets.py` — layer-inference tests
  must still pass (inferred layers must remain valid `LAYER_VALUES`
  members).
- `tests/tools/test_status_drift_check.py`, `tests/tools/test_done_checker_static.py`
  — unaffected, must remain green (transitively import `validate_frontmatter`).
- `tests/tools/test_agent_ops_dashboard_ingest.py`,
  `tests/tools/test_agent_ops_dashboard_api.py` — unaffected, confirm the
  dashboard backend still imports and runs cleanly.

## New Tests Required (per AC)

`tests/tools/test_layer_registry.py`, mirroring
`tests/tools/test_tag_registry.py`'s structure: `canonical_form_violation`,
`is_layer_registered`, `load_registry` (missing file, reads entries, skips
blanks, raises on duplicate), `add_layer` (appends correctly, rejects
non-canonical, rejects duplicate, append-only), `check_layers_registered`,
and `layer_values()` — both against a fixture and against the real,
live-seeded repo registry (the latter proves the actual seed data landed
correctly, not just that the mechanism works in isolation).

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_layer_registry.py tests/tools/test_validate_frontmatter.py tests/tools/test_ticket_field_values.py tests/tools/test_add_frontmatter_tickets.py tests/tools/test_status_drift_check.py tests/tools/test_done_checker_static.py tests/tools/test_tag_registry.py -q
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py -q
```

## Anti-Drift Test Guards

- `test_layer_values_matches_real_seeded_registry` — asserts against the
  real repo registry (no `root` override), so a future accidental edit to
  the seeded JSONL that drops or corrupts an entry is caught immediately.
- Genuine before/after full-corpus scan (not a pytest test — a direct
  script run via `git stash`) is the actual proof of zero regressions this
  ticket's highest-risk AC requires.
