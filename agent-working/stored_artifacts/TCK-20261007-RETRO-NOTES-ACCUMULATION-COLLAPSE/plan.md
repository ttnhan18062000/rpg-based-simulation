---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261007-RETRO-NOTES-ACCUMULATION-COLLAPSE
artifact_type: plan
tags: [agent-monitoring, retro]
---

# Plan

## Convention (explicit and parsable, not inferred from prose)
A note entry starts with a marker line `<!-- retro-note runs=N [final] -->` (N = the retro's deduped run count when the entry was written; `final` marks the current statement). The entry runs to the next marker or to end of file. Text before the first marker is **unmarked** and always preserved verbatim. A marker with a missing or non-integer `runs` is not a marker (text stays where it is, verbatim).

## Behaviour of `_write_report_preserving_notes(report, out_path, force, run_count=None)`
1. Parse the existing Notes into unmarked prefix + entries.
2. Entries that are stamped, not `final`, and followed by a later `final` entry are **collapsed**: replaced by one line `<!-- retro-note-collapsed runs=N --> - <first line of the entry, cut at 120 chars> (full text: <archive path>)`. The Final entry and every unmarked or malformed text are written back byte-for-byte. Collapsed lines are never collapsed again.
3. **Archive first**: the full text of each entry about to be collapsed is appended to `agent-working/agent-monitoring/retro/archive/RETRO-<label>-notes-history.md` (append-only, read back and compared) before the report is rewritten. If that write fails, nothing is collapsed and a warning is printed.
4. **Staleness flag**: a generated line right under the `## Notes` heading, `<!-- retro-notes-status -->_Final note written at N runs; this report covers M runs: refresh it._` shown when `run_count` is given and exceeds the Final entry's N (or the newest stamp when no entry is final). The line is regenerated (the old one is stripped) so it never accumulates; it is outside every entry, so the Final block stays byte-identical.
5. `--force` still replaces Notes wholesale (no collapse, no archive). Everything above `## Notes` is untouched. Idempotent: a second regeneration finds only collapsed lines, a Final entry and the status line.
6. `main()` passes the report's `deduped_run_count` as `run_count`.

## Other changes
- `.claude/skills/agent-monitoring-retro/SKILL.md`: document the marker, the `final` flag, and "when you add a new addendum, mark it `runs=N`; mark the newest one `final` and remove `final` from the previous one".
- One-off migration of `RETRO-2026-W40.md`: insert markers (first note and the 18/38/61-run addenda `runs=10/18/38/61`, the 251-run close-out `runs=251 final`), run the regeneration once, commit the collapsed file and its archive. Only W40 is rewritten.
- The ticket records the W41 answer (see investigation): collapses cleanly once its three addenda are marked; left as is.

## Scope guards
No change above `## Notes`; no deleting of unmarked hand-written text; no change to `--force` semantics.

## Questions for the planner
1. Archive in `retro/archive/RETRO-<label>-notes-history.md` (my recommendation: recoverable without git archaeology) or git history only?
2. Marker syntax as above (HTML comment, invisible in rendered Markdown) acceptable?
