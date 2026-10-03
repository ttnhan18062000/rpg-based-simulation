---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION
artifact_type: test_plan
tags: [agent-monitoring, workflows, process-improvement]
---

# Test Plan — TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION

## Regression Surface

All unit-level (this repo has no combat-arena or integration suite touching
`tools/agent-monitoring/` or `registries/`; everything below is `tests/tools/` unit-style).

- `tests/tools/test_validate_agent_monitoring.py` — full file. Specifically
  `test_canonical_vocabulary_single_sourced` (object-identity guard on
  `WORKFLOW_PHASES`/`infer_workflow`) must keep passing unmodified. Also exercises
  `compute_drift_report`, which reads `WORKFLOW_PHASES`/`is_known_agent` — must not start flagging
  the two new literals as drift once real events use them.
- `tests/tools/test_record_events.py` — full file. Covers `warn_vocabulary_drift`'s use of
  `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` at write time (warn-only, never raises/exits — confirmed by
  `test_vocabulary_warning_never_raises_or_exits`).
- `tests/tools/test_glossary_registry.py` — full file (18+ tests). Specifically:
  - `test_real_seeded_registry_covers_every_workflow_phase` (lines 197-217) — **this is the test
    that will hard-fail** if `vocabulary.py`'s `WORKFLOW_PHASES` edit lands without a matching
    `glossary_registry.jsonl` entry for `"Document-Update"`. This is the primary regression gate
    for this ticket's step-1/step-2 coupling.
  - `test_real_seeded_registry_every_entry_has_non_blank_description`,
    `test_real_seeded_registry_every_entry_has_valid_category` — must still pass against the new
    line.
  - `test_add_term_rejects_duplicate_term`, `test_load_registry_raises_on_duplicate_term` — confirm
    the append-only guard the new line must respect (added exactly once, never re-added).
- `tests/tools/test_doc_updater_agent_file.py`,
  `tests/tools/test_document_update_phase_wiring.py`,
  `tests/tools/test_workflow_meta_conformance.py` — CORE-WIRING's own regression surface for the
  phase's existence in `implement-ticket.js`. Not directly touched by this ticket, but should stay
  green since this ticket makes those real phase/agent literals recognized rather than flagged.
  Included for completeness, not required to re-run exhaustively, but worth a spot-check since
  `test_workflow_meta_conformance.py` parses the same `.js` file this ticket's vocabulary must stay
  consistent with.

## New Tests Required

No new test *files* are required — this ticket only needs to prove the two dict edits stick and
the existing structural guards (identity check, coverage check, duplicate-rejection) still hold.
Per the ticket's own Scope, no new test-writing task is listed; the acceptance criteria are
satisfied entirely by existing tests re-passing against the edited data. If Plan/Implement judges
a direct, explicit regression test is warranted (belt-and-suspenders beyond the existing coverage
test), the one candidate is:

- **Test name**: `test_document_update_phase_and_agent_registered_in_vocabulary`
- **Category**: unit
- **What it verifies**: `"Document-Update" in WORKFLOW_PHASES["implement-ticket"]` and
  `"doc-updater" in WORKFLOW_AGENTS["implement-ticket"]` — a direct, structural (membership-based,
  not count-based) assertion that this ticket's specific literals landed, independent of the
  broader coverage test in `test_glossary_registry.py`. Optional: this duplicates what
  `test_real_seeded_registry_covers_every_workflow_phase` already indirectly proves for the phase
  side, so only worth adding if Plan wants an explicit, ticket-scoped assertion rather than relying
  on the pre-existing coverage test.
- **Where it should live**: `tests/tools/test_validate_agent_monitoring.py` (co-located with
  `test_canonical_vocabulary_single_sourced`, same file, same object-identity/membership style —
  not a new file).

Anti-drift constraint on any such addition: assert **membership**
(`"Document-Update" in WORKFLOW_PHASES["implement-ticket"]`), never
`len(WORKFLOW_PHASES["implement-ticket"]) == 12` — a count assertion would need editing again on
the next vocabulary addition to this workflow, defeating the point of a regression guard.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_glossary_registry.py -v
```

Optional wider spot-check (sibling's own regression surface, to confirm no cross-ticket
interaction):

```
python3 -m pytest tests/tools/test_doc_updater_agent_file.py tests/tools/test_document_update_phase_wiring.py tests/tools/test_workflow_meta_conformance.py -v
```

Never `pytest tests/` — scoped to `tests/tools/` (agent-monitoring/glossary-registry domain) per
project testing rule.

## Anti-Drift Test Guards

- `test_canonical_vocabulary_single_sourced` itself is the guard against this ticket accidentally
  duplicating `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` into a second definition instead of editing the
  single source in `vocabulary.py` — re-running it unmodified after the edit is both an acceptance
  criterion and an anti-drift check in one.
- `test_real_seeded_registry_covers_every_workflow_phase` is the guard against landing the
  `vocabulary.py` edit without the matching `glossary_registry.jsonl` entry (or vice versa) — it
  fails loudly on any registration-count mismatch between the two files, catching exactly the
  "sibling landed, vocab didn't" / "vocab landed, glossary didn't" partial-state scenarios the
  ticket's own Request Summary describes as safe-but-inert intermediate states. (Those intermediate
  states are safe only when *this ticket itself* hasn't landed yet — mid-ticket, both edits must
  land together or this test fails.)
- `test_add_term_rejects_duplicate_term` / `test_load_registry_raises_on_duplicate_term` guard
  against a second, accidental `"Document-Update"` registration (e.g. re-running the CLI add
  command twice) — confirms the append-only law holds.
- `test_vocabulary_warning_never_raises_or_exits` (in `test_record_events.py`) guards that even if
  something is missed, the drift check stays warn-only and never blocks a run — confirms this
  ticket's change cannot introduce a new hard-failure mode in the write path.
- No test in this ticket's regression surface should start asserting a fixed count
  (`len(WORKFLOW_PHASES[...]) == 12`, `len(WORKFLOW_AGENTS[...]) == 12`, or a fixed total line
  count for `glossary_registry.jsonl`) — confirmed none currently do; any new test added here must
  preserve that property (see New Tests Required's anti-drift constraint) so the next vocabulary
  addition (e.g. the dashboard-palette sibling, or any future phase) doesn't require editing this
  ticket's tests again.
