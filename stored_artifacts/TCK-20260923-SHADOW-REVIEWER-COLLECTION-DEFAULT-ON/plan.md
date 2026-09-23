---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON
artifact_type: plan
tags: [ai, agent-monitoring, governance]
---

# Plan — TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON

## Approach
New-default gate form: `if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" != "0" ]; then ... ; fi`. An unset
env var reads as empty string in bash `[ ]`, and `"" != "0"` is true, so collection runs by
default. Setting `SHADOW_REVIEWER_LOGGING_ENABLED=0` explicitly is the only way to disable it. This
is the minimal one-character-class change at both call sites (`=` → `!=`, `"1"` → `"0"`) — no
restructuring of the surrounding bash/JS.

## Steps

1. **`implement-ticket.js` call sites** (~1057 architecture, ~1502 security): change
   `= "1"` to `!= "0"` in both `if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" ... ]` strings.
2. **Comments** (~220, ~1049): update "gated behind `SHADOW_REVIEWER_LOGGING_ENABLED`" phrasing that
   currently implies opt-in/off-by-default to state the new on-by-default / `=0` opt-out shape.
3. **Test**: `tests/tools/test_shadow_reviewer_call_site.py` line 230 — change the asserted literal
   string to `if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" != "0" ]`. Add one new test asserting the
   opt-out shape is present in both blocks (`SHADOW_REVIEWER_LOGGING_ENABLED" != "0"` implies the
   `"0"` literal itself is the opt-out value — assert that literal is `"0"`, not `"1"`, at both
   sites, so a future accidental revert back to the old polarity is caught).
4. **`docs/agent-monitoring/schema.md`**: replace "strict `"1"` string equality, off by default"
   with the new default description ("on by default; `SHADOW_REVIEWER_LOGGING_ENABLED=0` opts
   out").
5. **`docs/parity_ledger/infrastructure.yaml`, `INFRA-409`**: load the shard via
   `tools/parity_ledger_writer.py`, edit the `text` field's "off by default" phrase to match, append
   one sentence to `v2_evidence` noting the default-flip ticket and new gate string, call
   `write_entry()` (never a raw string-replace `Edit` on this file — full-file YAML rewrite risk,
   per session memory). Verify with `python3 tools/parity_index.py build` afterward per the module's
   own documented convention for a visible, retro-countable index rebuild.
6. **Epic refresh** (`tickets/todos/TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC.md`): update
   `Related Tickets` path annotations for items 14/15 to `tickets/done/`, and extend the
   `Assumptions` Bucket-B list (items 16, 17) to state plainly: item 16's prerequisite (this
   ticket's part b) has now shipped; item 17 remains genuinely un-gated (no false-positive data
   exists yet). Text-only edit — `## Status: EPIC_SCOPED` and all other sections stay as-is per this
   ticket's own Out of Scope.
7. **Record the known slow-fill limitation** directly in this ticket's own body (Assumptions /
   Open Questions or Implementation Notes) — already drafted in the todos-stub ticket text; carry
   it through unchanged into the final ticket.
8. **Run tests**: `pytest tests/tools/test_shadow_reviewer_call_site.py -v` (scoped, not the full
   suite).

## Risk / Rollback
Single-file code change (2 conditionals + 2 comments), one test file, two docs, one parity-ledger
entry, one epic-text edit — a `git revert` of this ticket's commit fully reverses the default. No
schema change, no new module, no change to `shadow_reviewer_window.py`/`shadow_reviewer_events.py`.

## Test Plan Reference
See `test_plan.md` in this same directory.
