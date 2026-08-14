---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-REGISTRY
phase: done
date: 2026-07-18
tags: [dashboard, observability, reporting]
---

# TCK-20260718-GLOSSARY-REGISTRY

## Title
New append-only glossary registry for dashboard enum-label descriptions

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child of `TCK-20260718-GLOSSARY-TOOLTIPS-EPIC`. Build the backend-owned data source the epic's
tooltips will read from — a registry of one-sentence descriptions per enum-like label this
dashboard renders (ticket status/tier/priority/type, run/gate status, reason codes, event
status), mirroring the `tag_registry.py`/`layer_registry.py` pattern established earlier today.

## Scope
- `tools/glossary_registry.py`: append-only JSONL registry module, `category`-field shape (7
  fixed categories), `add`/`list` CLI, `load_registry()` read function — mirrors `tag_registry.py`.
- `docs/guidelines/glossary_registry.jsonl`: seeded with 35 real terms via the real `add_term()`
  API, covering `tools/ticket_field_values.py`'s canonical Tier/Priority/ticket-Status values,
  `## Type` values, the live corpus's run/gate `final_status` values, and
  `docs/agent-monitoring/schema.md`'s documented `reason_code`/event-`status` values.
- `tests/tools/test_glossary_registry.py`: 18 tests mirroring `test_layer_registry.py`'s
  structure.

## Out of Scope
- Wiring this registry into any API endpoint — `TCK-20260718-GLOSSARY-API`'s scope.
- Frontend tooltip rendering — `TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`'s scope.
- A canonical-form enforcement rule — deliberately absent (see module docstring): these are
  existing fixed strings this repo's code already emits, not freely-chosen labels.

## Acceptance Criteria
- [x] `tools/glossary_registry.py` mirrors `tag_registry.py`'s append-only/`add`/`list` shape.
- [x] `docs/guidelines/glossary_registry.jsonl` seeded with 35 terms, each with a real,
      non-placeholder description.
- [x] Every `TIER_VALUES`/`PRIORITY_VALUES`/`WORKFLOW_STATUS_VALUES` canonical value has a
      glossary entry (verified by a real-registry test, not a fixture).
- [x] 18/18 new tests passing.

## Related Tickets
- TCK-20260718-GLOSSARY-TOOLTIPS-EPIC (parent epic)
- TCK-20260718-GLOSSARY-API (depends on this ticket)

## Related Docs
- docs/plans/agent_ops_dashboard/proposal_glossary_tooltips.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260718-GLOSSARY-REGISTRY/

## Related Code Areas
- tools/glossary_registry.py
- docs/guidelines/glossary_registry.jsonl
- tests/tools/test_glossary_registry.py
- tools/tag_registry.py (reference template)
- tools/layer_registry.py (reference template)

## Assumptions / Open Questions
None.

## Implementation Notes
Executed directly (Read/Edit/Bash/Write) — no Agent-tool subagent access in this execution
context. Registry seeded via the real `add_term()` API in a throwaway Python invocation (never
hand-written JSON lines), matching `TCK-20260718-LAYER-REGISTRY-CONVERSION`'s stated precedent for
this exact concern — verified afterward by reloading the file and confirming 35 entries with no
duplicate-key exception.

Case-sensitivity was checked explicitly: no collision exists between uppercase ticket/run-status
terms and the lowercase `event-status` terms (`ok`/`failed`/`blocked`/`skipped`) or lowercase
`reason-code` terms — confirmed via a dedicated test
(`test_is_term_registered_case_sensitive`) and by successfully loading all 35 seeded entries with
zero duplicate-key errors.

## Test Summary
`python3 -m pytest tests/tools/test_glossary_registry.py -q` — 18/18 passing, re-run and confirmed
clean.

## Files Changed
- tools/glossary_registry.py (new)
- docs/guidelines/glossary_registry.jsonl (new, 35 entries)
- tests/tools/test_glossary_registry.py (new)

## Completion Summary
Built the glossary registry mechanism and seeded it with 35 real, accurate term descriptions
spanning every enum-like label domain the dashboard renders. 18/18 tests passing. Unblocks
`TCK-20260718-GLOSSARY-API`.
