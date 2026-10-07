---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE
phase: open
date: 2026-10-07
tags: [agent-monitoring]
---

# TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE

## Title
Retro Notes: stamp addenda with run count, mark Final, collapse older per-regen addenda

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The retro's Notes section keeps every regeneration's addendum, so RETRO-2026-W40 grew to 558 lines and older addenda (written at 18, 38, 61 runs) conflict with the final tables. Either mark a Final block and collapse earlier per-regen addenda to a one-line history, or stamp notes with the run count they were written at and flag notes older than the data. Hand-written notes must never be dropped silently.

## Scope
- Introduce an explicit, parsable note convention in generate_retro.py (run-count stamp and Final marker) instead of inferring from free-form prose
- Extend _write_report_preserving_notes to collapse earlier stamped per-regen addenda to one-line history entries while keeping the Final block verbatim
- Flag a note stamped with run count N as stale when current data has more than N runs
- Preserve any addendum without a recognizable stamp or Final marker verbatim
- Keep --force discarding Notes explicitly; keep output above ## Notes unchanged and regeneration idempotent
- Update the agent-monitoring-retro SKILL.md so authors use the new marker
- Decide and record where full collapsed addendum text stays recoverable (git history or archived block)
- One-off migration of RETRO-2026-W40.md to the new convention

## Out of Scope
- Changing any retro content above the ## Notes heading
- Adding a Failures section (separate ticket)
- Rewriting other weeks' retros beyond W40
- Dropping or auto-editing hand-authored notes that carry no marker

## Acceptance Criteria
- [ ] Regenerating a retro whose Notes contain a Final-marked block plus earlier stamped per-regen addenda collapses each earlier addendum to a one-line history entry and keeps the Final block byte-for-byte
- [ ] Unmarked hand-written text in Notes survives regeneration byte-for-byte (test)
- [ ] A note stamped with run count N is flagged stale when current data has more than N runs (e.g. stamped at 18 vs 251 now)
- [ ] Regenerating twice on the same input yields identical output (idempotent)
- [ ] --force still discards Notes explicitly
- [ ] Existing test_extract_notes_section and test_write_report_preserving_notes tests still pass
- [ ] SKILL.md documents the stamp/Final marker convention

## Related Tickets
- TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES
- TCK-20260704-RETRO-LOOP-ENFORCEMENT
- TCK-20260607-MON-RETRO

## Related Docs
- docs/guidelines/design_patterns.md
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tests/tools/test_generate_retro.py
- agent-working/agent-monitoring/retro/RETRO-2026-W40.md
- .claude/skills/agent-monitoring-retro/SKILL.md

## Assumptions / Open Questions
- Collapsing is lossy, so full addendum text must remain recoverable (git history or archived block)
- Existing addenda have inconsistent headings, so a new stamp convention is required rather than parsing prose
- RETRO-ALL/LAST* outputs share the writer and must not regress

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
