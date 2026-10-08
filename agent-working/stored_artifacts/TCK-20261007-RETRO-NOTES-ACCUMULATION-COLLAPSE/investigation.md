---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE
artifact_type: investigation
tags: [agent-monitoring, retro]
---

# Investigation

- `_write_report_preserving_notes(report, out_path, force)` keeps everything from the first `## Notes` to end of file verbatim (`_extract_notes_section`); `--force` discards it. Nothing structures the Notes, so every regeneration's addendum accumulates.
- W40 (`RETRO-2026-W40.md`, 614 lines): Notes from line 449, a first note ("written 2026-09-29") plus addenda written at 18 runs (9/29), 38 runs (9/30), 61 runs (10/01) and a "Final close-out addendum" at **251 runs / 1570 events** (10/07), which itself says the earlier ones were written at 18, 38 and 61 runs. No machine-readable stamp exists; the headings differ in wording.
- W41 (`RETRO-2026-W41.md`, 466 lines): Notes from line 449 with three dated addenda: 2026-10-06, 2026-10-07 (8 DONE runs since last retro) and 2026-10-08 (125 W41 runs, 122 DONE). **Would the new convention collapse it cleanly? Yes, once the three addenda carry the new markers** (the 10/08 one is the natural Final entry, the others have dates and the run counts can be read from their text or entered by the author). Without markers nothing collapses: everything is preserved verbatim, so adopting the convention for W41 is a deliberate follow-up edit, not an accident. W41 is left untouched here (out of scope).
- Run count source for staleness: the report's own deduped run count (`deduped_run_count` in `main()`); `RETRO-ALL`/`LAST*` outputs share the writer and pass their own count.
- Recoverability of collapsed text: the retro files are committed, but a note written and collapsed before its first commit would be lost, and git archaeology is a poor reading path. So the plan archives the full text of every collapsed entry in an append-only sidecar before collapsing.
