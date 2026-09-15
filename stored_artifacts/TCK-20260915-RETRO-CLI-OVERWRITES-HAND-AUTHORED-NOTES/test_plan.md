# Test Plan — TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES

- `tests/tools/test_generate_retro.py` (7 new tests):
  - `_extract_notes_section`: returns notes-onward text; returns `None` when no heading exists.
  - `_write_report_preserving_notes`: writes cleanly when no existing file; preserves existing
    hand-authored Notes by default (asserting both that fresh data appears above Notes AND that
    the exact hand-authored text survives, not the fresh placeholder); `--force` discards existing
    Notes; an existing file with no `## Notes` heading at all overwrites cleanly (nothing to
    preserve, must not raise).
  - `test_main_regenerating_over_hand_authored_report_preserves_notes_end_to_end`: a real `main()`
    call (not just the pure helper functions) against a report with planted hand-authored content,
    asserting the content survives — mirrors the exact real-world incident this ticket was filed
    from.
- Full `tests/tools/test_generate_retro.py` suite (167 tests) re-run clean.
- Manual, against the real at-risk file: `python3 tools/agent-monitoring/generate_retro.py --days
  14` against the real `RETRO-LAST14D.md` (backed up first) — confirmed via the printed status
  message and a diff against the backup that only generated-section numbers changed and both
  hand-authored subsections survived byte-for-byte.
- Full `tests/tools/` suite re-run for final regression confirmation.
