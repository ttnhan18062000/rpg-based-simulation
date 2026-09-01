---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT
phase: open
date: 2026-08-31
tags: [bug, schema]
---

# TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT

## Title
Parity ledger `_ID_PATTERN`/schema regex rejects established multi-segment shard IDs (e.g. `WORLD-DEMO-XXX`)

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/parity_ledger_writer.py:48`'s `_ID_PATTERN = re.compile(r"^[A-Z]+-[0-9]{3}$")` (mirrored byte-for-byte in `docs/parity_ledger/schema.json`'s `properties.id.pattern`) requires exactly one hyphen — letters-only prefix, then exactly 3 digits. It structurally rejects any two-hyphen ID. This silently rejects the already-live, already-established `WORLD-DEMO-*`/`WORLD-CULT-*` multi-segment shard-ID convention: `WORLD-DEMO-001` through `WORLD-DEMO-006` in `docs/parity_ledger/world_dynamics.yaml` are all real, existing, valid-in-practice entries that the writer's own `validate_entry()` would reject if run against them today.

Discovered during `TCK-20260831-POPULATION-COHORT-SEEDING` (M2 batch, ticket 9/15) when adding a new `WORLD-DEMO-006` entry — the implementer worked around it by hand-reproducing the writer's validated write path (confirmed by Document-Update to be schema-valid in every other respect) rather than silently renaming the ID to dodge the regex or bypassing validation outright. This is a genuine pre-existing tool gap, not new breakage from that ticket.

**Second, independent blast radius found by Document-Update's follow-up check (not part of the original discovery):** `tools/gate_checks/parity_updater_static.py::next_available_id` mirrors the same `_ID_PATTERN`. Because it walks entries and skips any non-matching id, calling `next_available_id("world_dynamics.yaml")` today silently ignores all 6 `WORLD-DEMO-*` entries and returns `WORLD-102` (next bare `WORLD-NNN`) instead of the correct `WORLD-DEMO-007` — a second tool that would silently propose a colliding/wrong-convention ID for the next entry in this shard.

## Scope
- Extend `tools/parity_ledger_writer.py`'s `_ID_PATTERN` (and the byte-identical `docs/parity_ledger/schema.json` `properties.id.pattern`) to accept multi-segment prefixes, e.g. `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$`.
- Extend `tools/gate_checks/parity_updater_static.py::next_available_id`'s matching logic (or whatever regex/parsing it shares) so it correctly recognizes and increments multi-segment shard IDs like `WORLD-DEMO-*` instead of silently falling back to the bare `WORLD-NNN` sequence.
- Verify `validate_entry()` and `next_available_id()` both pass against the full existing corpus of `WORLD-DEMO-*`/`WORLD-CULT-*` entries after the fix (regression test using real ledger content, not synthetic fixtures).
- Add/extend a test in `tests/tools/test_parity_ledger_writer.py` and/or `test_parity_ledger_schema.py` covering a multi-segment ID round-trip through both `validate_entry()` and `next_available_id()`.

## Out of Scope
- Changing or renaming any existing parity ledger entry IDs.
- Any change to parity ledger *content* (only the ID-pattern validation/generation logic).

## Acceptance Criteria
- [ ] `validate_entry()` accepts `WORLD-DEMO-001` through `WORLD-DEMO-006` (and other existing multi-segment IDs across the ledger, e.g. `WORLD-CULT-001`) without error.
- [ ] `next_available_id("world_dynamics.yaml")` (or the relevant shard) correctly proposes `WORLD-DEMO-007` given the existing `WORLD-DEMO-001..006` entries, not a bare `WORLD-NNN` id.
- [ ] New/extended tests cover both functions against real multi-segment IDs, not just synthetic single-segment ones.
- [ ] No existing single-segment ID (`WORLD-NNN`, `COMB-NNN`, etc.) behavior regresses.

## Related Tickets
- TCK-20260831-POPULATION-COHORT-SEEDING (where this was discovered)

## Related Docs
- docs/parity_ledger/schema.json
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- tools/parity_ledger_writer.py
- tools/gate_checks/parity_updater_static.py
- docs/parity_ledger/schema.json
- tests/tools/test_parity_ledger_writer.py
- tests/tools/test_parity_ledger_schema.py

## Assumptions / Open Questions
- None — the regex gap and its second blast radius (`next_available_id`) were both directly confirmed against live source and the real ledger corpus during `TCK-20260831-POPULATION-COHORT-SEEDING`'s Document-Update phase, not assumed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
