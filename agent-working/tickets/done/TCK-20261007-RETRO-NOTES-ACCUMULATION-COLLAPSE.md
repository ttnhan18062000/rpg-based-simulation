---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE
phase: done
date: 2026-10-07
tags: [agent-monitoring]
---

# TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE

## Title
Retro Notes: stamp addenda with run count, mark Final, collapse older per-regen addenda

## Status
DONE

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
- [x] Regenerating a retro whose Notes contain a Final-marked block plus earlier stamped per-regen addenda collapses each earlier addendum to a one-line history entry and keeps the Final block byte-for-byte
- [x] Unmarked hand-written text in Notes survives regeneration byte-for-byte (test)
- [x] A note stamped with run count N is flagged stale when current data has more than N runs (e.g. stamped at 18 vs 251 now)
- [x] Regenerating twice on the same input yields identical output (idempotent)
- [x] --force still discards Notes explicitly
- [x] Existing test_extract_notes_section and test_write_report_preserving_notes tests still pass
- [x] SKILL.md documents the stamp/Final marker convention

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
New `tools/agent-monitoring/retro_notes.py` and `_write_report_preserving_notes(report, out_path, force, run_count=None)` in `generate_retro.py` (`main()` passes the deduped run count). Convention: `<!-- retro-note runs=N [final] -->` starts an entry; stamped non-final entries followed by a later `final` entry collapse to one `<!-- retro-note-collapsed runs=N --> - headline (full text: archive/...)` line; their full text is first appended to `retro/archive/RETRO-<label>-notes-history.md` and read back (a failing archive write collapses nothing and warns); the `final` block, unmarked text and malformed markers are preserved verbatim; a generated status line under `## Notes` flags a final (or newest stamped) note written at fewer runs than the report covers; regeneration is idempotent; `--force` still discards Notes. `SKILL.md` documents the markers and that a session adding an addendum must stamp it in the same edit. `RETRO-2026-W40.md` was migrated once (markers at 10/18/38/61 runs and the 251-run close-out as `final`; its Notes went from 614 to 511 lines, everything above `## Notes` byte-identical, the full text of the four collapsed entries in `retro/archive/RETRO-2026-W40-notes-history.md`).

**W41 question (planner):** `RETRO-2026-W41.md` has the same accumulation (addenda 2026-10-06, 10-07, 10-08). The new convention would collapse it cleanly once those three addenda carry markers (the 10-08 one as `final`, run counts from their text); until then nothing collapses and everything is preserved. W41 is left untouched, as instructed.

## Test Summary
`pytest tests/tools/test_retro_notes.py test_generate_retro.py`: 201 passed (13 new in test_retro_notes.py; the existing `test_extract_notes_section*` and `test_write_report_preserving_notes*` tests pass unchanged).

## Files Changed
tools/agent-monitoring/retro_notes.py, tools/agent-monitoring/generate_retro.py, tests/tools/test_retro_notes.py, .claude/skills/agent-monitoring-retro/SKILL.md, agent-working/agent-monitoring/retro/RETRO-2026-W40.md, agent-working/agent-monitoring/retro/archive/RETRO-2026-W40-notes-history.md

## Completion Summary
Convention, collapse, archive, stale flag, SKILL.md and the W40 migration are in. Collapsing is lossy in the readable file by design; the archive is the recovery path. W41 and the other weeks are not migrated.
