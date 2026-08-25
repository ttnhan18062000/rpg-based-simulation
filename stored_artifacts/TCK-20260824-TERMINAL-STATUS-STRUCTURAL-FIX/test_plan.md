# Test Plan — TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX

## New tests

1. `test_terminal_status_extractor.py::test_call_site_detection_tolerates_unrelated_line_insertion_above`
   — synthetic fixture proving line-insertion tolerance (see plan.md Step 3).

## Modified tests (behavior-preserving, assertion-strengthening)

1. `test_terminal_status_extractor.py::test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count`
   — literal line-number equality replaced with structural invariants (count, ascending, distinct
   call sites; count, distinct, non-None contexts).
2. `test_terminal_status_conformance.py::test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides`
   — same replacement.

## Regression surface (must stay green, unmodified)

- `test_terminal_status_extractor.py::test_terminal_status_extractor_finds_all_14_literal_call_sites`
  — unaffected; doesn't touch `call_sites`/`contexts` shape assertions beyond count/kind.
- `test_terminal_status_extractor.py::test_terminal_status_extractor_finds_verdict_derived_needs_changes_and_blocked`
  — unaffected.
- `test_terminal_status_extractor.py::test_scope_agent_failed_handling_is_an_explicit_documented_decision`
  — unaffected (bypass kind, no `contexts` involvement).
- `test_terminal_status_conformance.py::test_terminal_status_conformance_full_match_both_directions`
  — unaffected (compares `(value, kind)` pairs only, never touches `call_sites`/`contexts`).
- `test_terminal_status_schema.py` (all cases) — unaffected; validates the committed YAML file via
  `terminal_status_loader.py`, a separate data path from the extractor's live Python dicts.

## Commands

```
pytest tests/agent_orchestration_claude_adapter tests/agent_orchestration -m "not slow and not extra_slow" -q
```

## Acceptance-criteria mapping

| AC | Verified by |
|---|---|
| Structural invariants replace literal line-number equality | Modified tests above |
| Distinguishable via stable content marker, not line position | New `contexts` distinctness assertion |
| Tolerant of unrelated line insertions | New synthetic-fixture test |
| No other test hardcodes an implement-ticket.js line number | Investigation's repo-wide grep (documented, not a new gate) |
