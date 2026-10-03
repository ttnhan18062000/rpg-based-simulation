---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON
artifact_type: test_plan
tags: [ai, agent-monitoring, governance, testing]
---

# Test Plan — TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON

## Scope
Static source-text tests against `implement-ticket.js` (no JS runner in this repo — same
convention `test_shadow_reviewer_call_site.py` already uses). No behavioral/runtime test needed:
`shadow_reviewer_window.py`/`shadow_reviewer_events.py` are unmodified, so their own existing test
suite (`tests/tools/test_shadow_reviewer_window.py`) is a pure regression check, not new coverage.

## Tests

1. **Updated**: `test_shadow_reviewer_call_site_is_fail_open_and_env_gated` — asserts the new gate
   string `if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" != "0" ]` is present in both the architecture
   and security shadow blocks (replaces the old `= "1"` assertion). Normal flow.
2. **New**: `test_shadow_reviewer_default_on_opt_out_literal_is_zero_not_one` — asserts both blocks'
   gate condition uses the literal `"0"` as the opt-out comparand, not `"1"`, guarding against an
   accidental polarity revert. Regression-prevention.
3. **Unchanged, re-run for regression**: all other tests in `test_shadow_reviewer_call_site.py`
   (fail-open shape, seq disjointness, cost/timing attribution, anti-drift guards) — confirms this
   ticket's diff does not touch the shape those tests cover.
4. **Unchanged, re-run for regression**: `tests/tools/test_shadow_reviewer_window.py` — confirms
   `SHADOW_MAX_SAMPLES`/`SHADOW_SEQ_BASE` and the window-open logic are untouched.

## Commands
```
pytest tests/tools/test_shadow_reviewer_call_site.py tests/tools/test_shadow_reviewer_window.py -v
```
Scoped to the domain under modification, per CLAUDE.md's Testing Rule — not the full suite.

## Out of Scope
- Any live end-to-end run of `implement-ticket.js` itself (no JS test runner exists for
  `.claude/workflows/*.js` in this repo).
- `docs/parity_ledger/infrastructure.yaml`'s own schema validation is exercised by
  `tools/parity_ledger_writer.py::validate_entry()` at write time (raises on violation) — no
  separate test file needed for this ticket's one-entry edit; `tests/tools/test_parity_ledger_writer.py`
  already covers the writer module generically and is unaffected by this ticket's diff.
