# Plan — TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES

1. Add `_extract_notes_section()` and `_write_report_preserving_notes()` to `generate_retro.py`;
   add a `--force` argparse flag.
2. Replace `main()`'s unconditional `out_path.write_text(report)` with a call to
   `_write_report_preserving_notes(report, out_path, args.force)`, printing its returned status
   (never silent).
3. Update `.claude/skills/agent-monitoring-retro/SKILL.md` to document the new preserve-by-default
   behavior and the `--force` escape hatch, so the skill and the tool agree.
4. Add tests: the two pure helper functions directly (preserve, no-existing-notes, no-existing-file
   cases), an end-to-end `main()` invocation proving a real regeneration preserves hand-authored
   content, and confirm `--force` still allows a full discard.
5. Validate against the real at-risk file (`RETRO-LAST14D.md`, backed up first) — the first safe
   real regeneration of that file all session.
6. Run full affected regression scope.
