---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES
phase: done
date: 2026-09-15
tags: [agent-monitoring, reporting, process-improvement]
---

# TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES

## Title
`generate_retro.py` unconditionally overwrites its own report, destroying the hand-written `## Notes` the project's own retro skill instructs a session to add

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found the hard way on 2026-09-15 by `agent-working-implementer` while verifying the
`DUPLICATE-RUN-RECORDS` fix: re-running `python3 tools/agent-monitoring/generate_retro.py --days 14`
to check a corrected figure **rewrote `agent-monitoring/retro/RETRO-LAST14D.md` from scratch**,
deleting every hand-authored section in it. Confirmed with a real `git diff` showing **177 deleted
lines** before it was reverted. The verification had to be completed instead by importing
`_load_runs_and_events()` / `compute_retro_metrics()` / `generate()` directly and calling them
without touching `RETRO_DIR`.

**This is an instruction-level trap, not just an ergonomic wart.** The project's own skill,
`.claude/skills/agent-monitoring-retro/SKILL.md`, explicitly tells a session to:

> Fills in the `## Notes` section of the report with concrete findings and one proposed action per
> issue found, then leaves the report ready to commit.

and

> Commit the filled-in report. Do not discard the notes — they are the institutional memory of
> agent behavior over time.

So the documented workflow is: generate, hand-write analysis into the report, commit it. And the
same tool's next invocation destroys exactly that. A session following both instructions in order
loses its own work — structurally identical to the `append_working_log_row()` +
`record_hand_orchestrated_closure.py` double-write that
`TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` fixed: two correct
instructions that combine into a defect.

The risk is not hypothetical or one-off. `RETRO-LAST14D.md` currently carries a ~200-line deep
review plus an index-defect addendum; the weekly `RETRO-<week>.md` files are the skill's normal
output and are meant to accumulate notes over time. Any regeneration silently discards them, and
because the file is rewritten rather than appended to, nothing warns and nothing fails.

## Scope
- Make regeneration non-destructive with respect to hand-authored content. The mechanism is the
  implementer's choice; the constraint is that content a human or agent wrote must not be silently
  discarded. Reasonable shapes:
  - **Refuse** to overwrite a report that contains content outside the generated sections, unless
    an explicit `--force` is passed.
  - **Preserve** a delimited region (e.g. everything from `## Notes` onward) across regeneration.
  - **Write elsewhere** by default, leaving the existing file untouched.
- Whichever is chosen, a regeneration that *would* discard content must say so rather than doing it
  quietly.
- If the chosen shape changes the documented workflow, update
  `.claude/skills/agent-monitoring-retro/SKILL.md` in the same change so the skill and the tool stop
  disagreeing.

## Out of Scope
- `_update_index`'s zero-reporting defect — that is `TCK-20260915-RETRO-INDEX-REPORTS-ZERO`, a
  separate bug in the same file.
- Restoring any previously-lost notes. The 177-line loss was caught and reverted; whether earlier
  regenerations destroyed notes nobody noticed is unknown and not investigated here.
- Changing the report's generated sections or format.

## Acceptance Criteria
- [x] Running the generator against an existing report containing hand-authored content
      **preserves** that content (splices the existing `## Notes`-onward text onto the freshly
      regenerated report) and prints a status message naming what happened. Silent overwrite is no
      longer possible on the default path.
- [x] `test_main_regenerating_over_hand_authored_report_preserves_notes_end_to_end` plants
      hand-authored content, calls the real `main()`, and asserts on the resulting file's content
      (not a return code) — the exact incident this ticket was filed from, reproduced safely in a
      `tmp_path` fixture.
- [x] `--force` still allows a deliberate full rewrite —
      `test_write_report_preserving_notes_force_discards_existing_notes` proves it discards
      existing notes when passed.
- [x] `.claude/skills/agent-monitoring-retro/SKILL.md` updated to document the preserve-by-default
      behavior and the `--force` escape hatch.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-RETRO-INDEX-REPORTS-ZERO` — sibling defect in the same module
- `TCK-20260915-DUPLICATE-RUN-RECORDS` (done) — the ticket whose verification hit this hazard
- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` (done) — the same
  "two correct instructions combine into a defect" shape

## Related Docs
- `.claude/skills/agent-monitoring-retro/SKILL.md` — the instruction half of the trap
- `agent-monitoring/retro/RETRO-LAST14D.md` — records the hazard in its own correction note
- `docs/guides/agent_monitoring.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-DUPLICATE-RUN-RECORDS/` — where the hazard was hit

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py` — `main()`, `generate()`, and the `RETRO_DIR` write path
- `.claude/skills/agent-monitoring-retro/SKILL.md`
- `Makefile` (`agent-monitoring-retro` target)

## Assumptions / Open Questions
- Whether any past regeneration already destroyed notes is **unknown**. Git history would show it,
  but that search is deliberately out of scope here — flagged in case it is worth its own look.
  Left open, per scope.
- The weekly reports may be more exposed than the period reports, since the skill's documented
  cadence regenerates them routinely. Resolved: the fix applies uniformly to every report type
  (`main()`'s single shared write path), so weekly reports are no longer more exposed than any
  other.

## Implementation Notes
See `staging_artifacts/TCK-20260915-RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES/investigation.md`
for the full root-cause writeup and the real-file validation details.

Chose **preserve** (splice the existing `## Notes`-onward text onto the fresh report) over the
ticket's other two suggested shapes (refuse-unless-force, write-elsewhere) — it matches the
skill's actual documented cadence (routine regeneration, notes accumulate over time) without
forcing every routine call to pass `--force`, and without diverging report content across two file
paths. `_extract_notes_section()` finds the `## Notes` heading (always present in every generated
report, unconditionally) and returns everything from there to EOF; `_write_report_preserving_notes()`
is the single write path `main()` now calls, returning a human-readable status string that always
names what happened (written fresh / preserved N chars / force-discarded), never silent.

Validated against the real at-risk file (backed up first as an extra precaution, though the fix
itself made this unnecessary): `python3 tools/agent-monitoring/generate_retro.py --days 14` against
the real `RETRO-LAST14D.md` — the first time this session ran that exact CLI invocation directly
against that file, since doing so before this fix would have repeated the original 177-line-loss
incident. Printed `preserved 13459 chars of existing ## Notes content`; diff confirmed only
generated-section numbers changed, both hand-authored subsections ("Deep review — 2026-09-15",
"Duplicate run records corrected — 2026-09-15") survived byte-for-byte.

## Test Summary
- `tests/tools/test_generate_retro.py`: 7 new tests — the two pure helper functions
  (`_extract_notes_section`, `_write_report_preserving_notes`) covering preserve/force/no-existing-
  file/no-existing-notes-heading cases, plus an end-to-end `main()` invocation reproducing the
  exact real-world incident in a `tmp_path` fixture.
- Full `tests/tools/test_generate_retro.py` suite: 167 passed.
- Full `tests/tools/` suite: 2684 passed (0 failures) after this ticket's changes.
- Manual: real-file validation against `RETRO-LAST14D.md`, described above.

## Files Changed
- `tools/agent-monitoring/generate_retro.py` — `_extract_notes_section()`,
  `_write_report_preserving_notes()`, a new `--force` flag, `main()`'s write step rewired to the
  new preserving path.
- `.claude/skills/agent-monitoring-retro/SKILL.md` — documents preserve-by-default and `--force`.
- `agent-monitoring/retro/RETRO-LAST14D.md` — regenerated for real (first time all session), safely,
  as part of validating this fix; only generated-section numbers changed.
- `tests/tools/test_generate_retro.py` — 7 new tests.

## Completion Summary
Fixed `generate_retro.py`'s unconditional overwrite (the exact hazard that destroyed 177 lines of
a peer's hand-authored review earlier this session) by making the default write path preserve any
existing report's `## Notes` content across regeneration, splicing it onto the freshly-regenerated
data above it, with `--force` as an explicit, deliberate escape hatch for a full rewrite. Updated
the retro skill to document the new behavior so skill and tool no longer disagree. Validated for
real against the actual file this hazard was discovered on. This closes the 9th and final child
ticket of `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` — a single PR for the whole epic follows
next, per the standing instruction.
