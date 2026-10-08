---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE
artifact_type: test_plan
tags: [agent-monitoring, retro]
---

# Test plan

Extend `tests/tools/test_generate_retro.py` (existing `test_extract_notes_section*` and `test_write_report_preserving_notes*` stay green unchanged).
1. Final + earlier stamped entries: each earlier entry collapses to exactly one history line; the Final entry is byte-for-byte unchanged.
2. Unmarked hand-written text (before any marker, or between none) survives byte-for-byte.
3. Staleness: an entry stamped `runs=18` with current run count 251 -> the status line says so; equal or lower current count -> no stale flag.
4. Idempotent: regenerate twice on the same input -> identical file; the second run also writes nothing new to the archive.
5. Archive: the collapsed entry's full text is in the archive file (read back equal) BEFORE the report is rewritten; if the archive write fails, the report is not collapsed and a warning is printed (nothing lost).
6. `--force` still replaces the Notes (and does not collapse or archive).
7. A malformed marker (no `runs=`, non-integer) is treated as unmarked: preserved verbatim, never collapsed.
8. W40 migration: after adding markers to the real file, a dry regeneration collapses the 18/38/61-run addenda and keeps the 251-run Final entry.
9. Output above `## Notes` unchanged vs. the pre-change generator (golden comparison on a fixture).
